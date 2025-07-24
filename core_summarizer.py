import os
import time
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import TextFormatter
import requests
from urllib.parse import urlparse, parse_qs
import logging
from llm_handler import MultiLLMHandler
from django.shortcuts import render, redirect


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Simple text processing functions to replace NLTK
def simple_sentence_tokenize(text):
    """Simple sentence tokenization without NLTK"""
    # Split on common sentence endings
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def simple_word_tokenize(text):
    """Simple word tokenization without NLTK"""
    # Split on whitespace and punctuation
    words = re.findall(r'\b\w+\b', text.lower())
    return words

def get_stop_words():
    """Get common English stop words"""
    return {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 
        'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with',
        'i', 'you', 'your', 'we', 'they', 'them', 'this', 'these', 'those', 'but', 'or',
        'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
    }

@dataclass
class Timestamp:
    time: str
    title: str
    section_id: int
    start_index: int
    end_index: int

@dataclass
class VideoInfo:
    video_id: str
    title: str
    duration: str
    channel: str
    upload_date: str

class YouTubeSummarizer:
    def __init__(self):
        self.llm_handler = MultiLLMHandler()
        self.text_formatter = TextFormatter()
        self.stop_words = get_stop_words()
        
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        # Handle different YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid YouTube URL format")

    def check_video_accessibility(self, url: str) -> Dict:
        """Check if video is accessible before processing"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text.lower()
            
            # Check for common restriction patterns
            if "video is restricted" in content:
                return {
                    'accessible': False,
                    'error_type': 'restricted',
                    'error_message': 'Video is restricted by network/administrator policies'
                }
            elif "video unavailable" in content:
                return {
                    'accessible': False,
                    'error_type': 'unavailable',
                    'error_message': 'Video is unavailable or has been removed'
                }
            elif "private video" in content:
                return {
                    'accessible': False,
                    'error_type': 'private',
                    'error_message': 'Video is private'
                }
            elif "age-restricted" in content:
                return {
                    'accessible': False,
                    'error_type': 'age_restricted',
                    'error_message': 'Video is age-restricted'
                }
            else:
                return {
                    'accessible': True,
                    'error_type': None,
                    'error_message': None
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'accessible': False,
                'error_type': 'network_error',
                'error_message': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'accessible': False,
                'error_type': 'unknown_error',
                'error_message': f'Unknown error: {str(e)}'
            }

    def get_video_metadata(self, video_id: str, transcript_data: List[Dict] = None) -> VideoInfo:
        """Get video metadata using available information"""
        try:
            # Calculate duration from transcript data if available
            duration_str = "Unknown"
            if transcript_data:
                try:
                    # Handle both dict and object formats
                    max_time = 0
                    for entry in transcript_data:
                        if isinstance(entry, dict):
                            max_time = max(max_time, entry['start'] + entry['duration'])
                        else:
                            max_time = max(max_time, entry.start + entry.duration)
                    duration_str = f"{int(max_time // 60)}:{int(max_time % 60):02d}"
                except Exception as e:
                    logger.warning(f"Could not calculate duration: {e}")
                    duration_str = "Unknown"
            
            # Try to get additional metadata from YouTube
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                response = requests.get(url, timeout=10)
                content = response.text
                
                # Extract title from page
                title_match = re.search(r'"title":"([^"]*)"', content)
                title = title_match.group(1) if title_match else "Unknown Title"
                
                # Extract channel from page
                channel_match = re.search(r'"author":"([^"]*)"', content)
                channel = channel_match.group(1) if channel_match else "Unknown Channel"
                
                # Clean up extracted data
                title = title.encode().decode('unicode_escape')
                channel = channel.encode().decode('unicode_escape')
                
            except Exception as e:
                logger.warning(f"Could not extract metadata from page: {e}")
                title = "Unknown Title"
                channel = "Unknown Channel"
            
            return VideoInfo(
                video_id=video_id,
                title=title,
                duration=duration_str,
                channel=channel,
                upload_date="Unknown Date"
            )
            
        except Exception as e:
            logger.warning(f"Could not get full metadata: {e}")
            return VideoInfo(
                video_id=video_id,
                title="Unknown Title",
                duration="Unknown",
                channel="Unknown Channel",
                upload_date="Unknown Date"
            )


    def extract_subtitles(self, video_url: str) -> Dict:
        """Extract subtitles using youtube-transcript-api with proper error handling"""
        logger.info("Extracting subtitles...")
        start_time = time.time()

        try:
            # Check video accessibility first
            accessibility = self.check_video_accessibility(video_url)
            if not accessibility['accessible']:
                logger.error(f"Video accessibility error: {accessibility['error_message']}")
                return {
                    'success': False,
                    'error_code': accessibility['error_type'].upper(),
                    'error_message': accessibility['error_message'],
                    'suggestions': self._get_error_suggestions(accessibility['error_type'])
                }

            # Extract video ID
            video_id = self.extract_video_id(video_url)

            # Get transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_transcript(['en-US', 'en-GB'])
                except NoTranscriptFound:
                    available_transcripts = list(transcript_list)
                    if not available_transcripts:
                        raise NoTranscriptFound("No transcripts available")
                    transcript = available_transcripts[0]

            # Fetch transcript data
            transcript_data = transcript.fetch()

            # Get video metadata
            video_info = self.get_video_metadata(video_id, transcript_data)

            # Format transcript
            formatted_transcript = self.text_formatter.format_transcript(transcript_data)

            # Convert to list format for processing
            structured_transcript = []
            for entry in transcript_data:
                # Handle both dict and object formats
                if isinstance(entry, dict):
                    structured_transcript.append({
                        'text': entry['text'],
                        'start': entry['start'],
                        'duration': entry['duration']
                    })
                else:
                    # Handle object format
                    structured_transcript.append({
                        'text': entry.text,
                        'start': entry.start,
                        'duration': entry.duration
                    })

            processing_time = time.time() - start_time
            logger.info(f"Subtitles extracted in {processing_time:.2f}s")

            return {
                'success': True,
                'video_info': video_info,
                'transcript_data': transcript_data,
                'transcript_text': formatted_transcript,
                'transcript_list': structured_transcript,
                'processing_time': processing_time
            }

        except TranscriptsDisabled:
            logger.error("Transcripts are disabled for this video.")
            return {
                'success': False,
                'error_code': 'TRANSCRIPTS_DISABLED',
                'error_message': 'This video has transcripts disabled',
                'suggestions': ['Try finding similar content with enabled subtitles']
            }
        except NoTranscriptFound:
            logger.error("No transcripts found for this video.")
            return {
                'success': False,
                'error_code': 'NO_TRANSCRIPTS',
                'error_message': 'No English transcripts found for this video',
                'suggestions': ['Try videos with English subtitles']
            }
        except VideoUnavailable:
            logger.error("Video is unavailable or restricted.")
            return {
                'success': False,
                'error_code': 'VIDEO_UNAVAILABLE',
                'error_message': 'Video is unavailable or restricted',
                'suggestions': ['Check if video is public and accessible']
            }
        except ValueError as e:
            logger.error(f"Invalid URL: {e}")
            return {
                'success': False,
                'error_code': 'INVALID_URL',
                'error_message': str(e),
                'suggestions': ['Check the YouTube URL format']
            }
        except Exception as e:
            import traceback
            logger.error(f"Exception during subtitle extraction: {repr(e)}")
            logger.error(traceback.format_exc())
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HTTP response content: {e.response.content}")
            if "restricted" in error_msg.lower():
                return {
                    'success': False,
                    'error_code': 'RESTRICTED_VIDEO',
                    'error_message': f'Failed to extract subtitles: {error_msg}',
                    'suggestions': [
                        'Try accessing from a different network',
                        'Use a VPN if geographically restricted',
                        'Check with your IT administrator about restrictions',
                        'Try a different video'
                    ]
                }
            else:
                return {
                    'success': False,
                    'error_code': 'EXTRACTION_ERROR',
                    'error_message': f'Failed to extract subtitles: {error_msg}',
                    'suggestions': ['Check if the video is available and public']
                }



    def _get_error_suggestions(self, error_type: str) -> List[str]:
        """Get error-specific suggestions"""
        suggestions = {
            'restricted': [
                "Try accessing from a different network (mobile data, home WiFi)",
                "Use a VPN to bypass geographic restrictions",
                "Check with your IT administrator about network restrictions",
                "Try a different Google account or incognito mode"
            ],
            'unavailable': [
                "Check if the video URL is correct",
                "The video might have been removed or made private",
                "Try searching for the video again on YouTube"
            ],
            'private': [
                "Contact the video owner for access",
                "Check if you have the correct sharing link",
                "The video might have been made private recently"
            ],
            'age_restricted': [
                "Sign in to YouTube with an adult account",
                "The video requires age verification"
            ],
            'network_error': [
                "Check your internet connection",
                "Try again in a few minutes",
                "Use a different DNS server"
            ]
        }
        return suggestions.get(error_type, ["Try a different video URL"])

    def analyze_content_structure(self, transcript_list: List[Dict]) -> List[Dict]:
        """Analyze transcript to identify topic boundaries and key concepts"""
        logger.info("🧠 Analyzing content structure...")
        
        # Extract text and timing information
        sentences = []
        
        for entry in transcript_list:
            text = entry['text']
            start_time = entry['start']
            duration = entry['duration']
            
            # Split into sentences
            for sentence in simple_sentence_tokenize(text):
                sentences.append({
                    'text': sentence,
                    'start_time': start_time,
                    'end_time': start_time + duration,
                    'word_count': len(simple_word_tokenize(sentence))
                })
        
        # Calculate topic boundaries using content analysis
        topic_boundaries = self._detect_topic_boundaries(sentences)
        
        return topic_boundaries

    def _detect_topic_boundaries(self, sentences: List[Dict]) -> List[Dict]:
        """Detect topic boundaries using NLP techniques"""
        boundaries = []
        
        # Simple approach: look for significant content shifts
        for i in range(1, len(sentences)):
            prev_sentence = sentences[i-1]
            curr_sentence = sentences[i]
            
            # Calculate similarity/difference metrics
            prev_words = set(simple_word_tokenize(prev_sentence['text'].lower()))
            curr_words = set(simple_word_tokenize(curr_sentence['text'].lower()))
            
            # Remove stop words
            prev_words = prev_words - self.stop_words
            curr_words = curr_words - self.stop_words
            
            # Calculate Jaccard similarity
            intersection = len(prev_words & curr_words)
            union = len(prev_words | curr_words)
            similarity = intersection / union if union > 0 else 0
            
            # Detect boundary if similarity is low and time gap is significant
            time_gap = curr_sentence['start_time'] - prev_sentence['end_time']
            
            if similarity < 0.3 and time_gap > 2.0:  # Low similarity and >2s gap
                boundaries.append({
                    'index': i,
                    'start_time': curr_sentence['start_time'],
                    'confidence': 1 - similarity
                })
        
        # Ensure we have reasonable number of boundaries (8-12)
        if len(boundaries) < 8:
            # Add more boundaries based on time intervals
            total_duration = sentences[-1]['end_time'] if sentences else 0
            target_sections = 10
            interval = total_duration / target_sections
            
            for i in range(1, target_sections):
                target_time = i * interval
                # Find closest sentence to this time
                closest_idx = min(range(len(sentences)), 
                                key=lambda x: abs(sentences[x]['start_time'] - target_time))
                boundaries.append({
                    'index': closest_idx,
                    'start_time': sentences[closest_idx]['start_time'],
                    'confidence': 0.5
                })
        
        # Sort and deduplicate
        boundaries = sorted(boundaries, key=lambda x: x['start_time'])
        unique_boundaries = []
        for boundary in boundaries:
            if not unique_boundaries or boundary['start_time'] - unique_boundaries[-1]['start_time'] > 30:
                unique_boundaries.append(boundary)
        
        return unique_boundaries[:12]  # Limit to 12 sections

    def generate_timestamps(self, transcript_list: List[Dict]) -> List[Timestamp]:
        """Generate intelligent timestamps with descriptive titles"""
        logger.info("⏰ Generating intelligent timestamps...")
        start_time = time.time()
        
        # Analyze content structure
        boundaries = self.analyze_content_structure(transcript_list)
        
        timestamps = []
        for i, boundary in enumerate(boundaries):
            # Get text around this boundary for title generation
            start_idx = max(0, boundary['index'] - 2)
            end_idx = min(len(transcript_list), boundary['index'] + 3)
            
            context_text = " ".join([entry['text'] for entry in transcript_list[start_idx:end_idx]])
            
            # Generate title using AI
            title = self._generate_section_title(context_text, i + 1)
            
            # Convert time to MM:SS format
            time_str = self._seconds_to_timestamp(boundary['start_time'])
            
            timestamp = Timestamp(
                time=time_str,
                title=title,
                section_id=i + 1,
                start_index=boundary['index'],
                end_index=boundaries[i + 1]['index'] if i + 1 < len(boundaries) else len(transcript_list)
            )
            timestamps.append(timestamp)
        
        processing_time = time.time() - start_time
        logger.info(f"Timestamps generated in {processing_time:.2f}s")
        
        return timestamps
    def _generate_section_title(self, context_text: str, section_num: int) -> str:
        """Generate a concise and descriptive title for a section using the LLM"""
        try:
            trimmed_text = context_text.strip()[:500].replace('\n', ' ')
            
            prompt = f"""You are an educational content assistant.

Based on the following video section content, generate a clear, concise, and academic section title in **less than 8 words**.

Content:
\"\"\"{trimmed_text}\"\"\"

Rules:
- Be specific to the topic
- Avoid generic words like 'Section' or 'Part'
- No quotes or punctuation at the end

Only respond with the section title."""

            title = self.llm_handler.generate_content(prompt)

            if title:
                # Clean and sanitize
                title = title.strip().strip('"\'')
                title = title.split('\n')[0]
                title = re.sub(r'[^\w\s\-]', '', title)  # Remove special characters
                return title if title else f"Section {section_num}"
            else:
                return f"Section {section_num}"

        except Exception as e:
            logger.warning(f"Failed to generate title for section {section_num}: {e}")
            return f"Section {section_num}"

    # def _generate_section_title(self, context_text: str, section_num: int) -> str:
    #     """Generate descriptive title for a section using AI"""
    #     try:
    #         prompt = f"""
    #         Generate a concise, descriptive title (max 8 words) for this video section based on the content:
            
    #         Content: {context_text[:500]}...
            
    #         Requirements:
    #         - Be specific and educational
    #         - Use clear, academic language
    #         - Focus on the main topic or concept
    #         - Keep it under 8 words
            
    #         Title:"""
            
    #         title = self.llm_handler.generate_content(prompt, task_type="title")
            
    #         if title:
    #             # Clean up the title
    #             title = re.sub(r'^["\']|["\']$', '', title)  # Remove quotes
    #             title = title.split('\n')[0]  # Take first line only
    #             return title if title else f"Section {section_num}"
    #         else:
    #             return f"Section {section_num}"
            
    #     except Exception as e:
    #         logger.warning(f"Failed to generate title for section {section_num}: {e}")
    #         return f"Section {section_num}"

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def summarize_section(self, transcript_list: List[Dict], section_id: int, timestamps: List[Timestamp]) -> str:
        """Summarize a specific timestamp section"""
        logger.info(f"📝 Summarizing section {section_id}...")
        
        # Find the timestamp
        timestamp = next((ts for ts in timestamps if ts.section_id == section_id), None)
        if not timestamp:
            return "Section not found"
        
        # Extract section text
        section_text = " ".join([
            entry['text'] for entry in transcript_list[timestamp.start_index:timestamp.end_index]
        ])
        
        # Generate summary
        prompt = f"""
        Create a detailed, educational summary of this video section titled "{timestamp.title}":
        
        {section_text}
        
        Requirements:
        - Maintain academic tone
        - Include key concepts and definitions
        - Preserve technical terminology
        - Focus on educational value
        - Structure with bullet points for clarity
        
        Summary:"""
        
        try:
            summary = self.llm_handler.generate_content(prompt, task_type="summary")
            return summary if summary else f"Summary failed for section {section_id}"
        except Exception as e:
            logger.error(f"Failed to summarize section {section_id}: {e}")
            return f"Summary failed for section {section_id}"

    def summarize_full_video(self, transcript_text: str, timestamps: List[Timestamp], video_info: VideoInfo) -> str:
        """Generate comprehensive full video summary"""
        logger.info("🎯 Generating full video summary...")
        start_time = time.time()
        
        # Create structured summary using timestamps
        timestamp_summaries = []
        for timestamp in timestamps:
            timestamp_summaries.append(f"## {timestamp.time} - {timestamp.title}")
        
        prompt = f"""
        Create a comprehensive summary of this educational video: "{video_info.title}"
        
        Video Information:
        - Channel: {video_info.channel}
        - Duration: {video_info.duration}
        
        Main Sections:
        {chr(10).join(timestamp_summaries)}
        
        Full Transcript:
        {transcript_text[:8000]}...
        
        Requirements:
        1. Create an executive summary (2-3 sentences) of the entire video
        2. Structure the summary using the provided timestamps as section headers
        3. Include key concepts, important facts, and main takeaways
        4. Maintain logical flow between sections
        5. Use academic tone suitable for students
        6. Preserve technical terminology and definitions
        7. Focus on educational value and learning outcomes
        
        Format the response with:
        - Executive Summary at the top
        - Detailed sections following the timestamp structure
        - Key takeaways at the end
        """
        
        try:
            summary = self.llm_handler.generate_content(prompt, task_type="summary")
            
            if summary:
                processing_time = time.time() - start_time
                logger.info(f"Full summary generated in {processing_time:.2f}s")
                return summary
            else:
                return "Summary generation failed: All LLM providers unavailable"
                
        except Exception as e:
            logger.error(f"Failed to generate full summary: {e}")
            return f"Summary generation failed: {str(e)}"

    def process_video(self, video_url: str) -> Dict:
        """Main processing pipeline for video summarization"""
        logger.info("Starting video processing pipeline...")
        total_start_time = time.time()
        
        try:
            # Step 1: Extract subtitles
            subtitle_result = self.extract_subtitles(video_url)
            if not subtitle_result['success']:
                return subtitle_result
            
            video_info = subtitle_result['video_info']
            transcript_list = subtitle_result['transcript_list']
            transcript_text = subtitle_result['transcript_text']
            
            # Step 2: Generate timestamps
            timestamps = self.generate_timestamps(transcript_list)
            
            # Step 3: Generate full summary
            full_summary = self.summarize_full_video(transcript_text, timestamps, video_info)
            
            # Step 4: Create executive summary
            executive_summary = self._extract_executive_summary(full_summary)
            
            # Step 5: Prepare response
            total_time = time.time() - total_start_time
            
            response = {
                'success': True,
                'video_id': video_info.video_id,
                'title': video_info.title,
                'duration': video_info.duration,
                'channel': video_info.channel,
                'upload_date': video_info.upload_date,
                'timestamps': [
                    {
                        'time': ts.time,
                        'title': ts.title,
                        'section_id': ts.section_id,
                        'start_index': ts.start_index,
                        'end_index': ts.end_index
                    } for ts in timestamps
                ],
                'executive_summary': executive_summary,
                'full_summary': full_summary,
                'processing_time': total_time,
                'subtitle_extraction_time': subtitle_result['processing_time']
            }
            
            logger.info(f"Video processing completed in {total_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                'success': False,
                'error_code': 'PROCESSING_ERROR',
                'error_message': f'Video processing failed: {str(e)}',
                'suggestions': ['Check video URL and try again']
            }

    def _extract_executive_summary(self, full_summary: str) -> str:
        """Extract executive summary from full summary"""
        lines = full_summary.split('\n')
        executive_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('#'):
                executive_lines.append(line.strip())
                if len(executive_lines) >= 3:  # Take first 3 sentences
                    break
        
        return ' '.join(executive_lines) if executive_lines else "Summary not available"

# Convenience functions for external use
def extract_subtitles(video_url: str) -> Dict:
    """Extract subtitles from YouTube video"""
    summarizer = YouTubeSummarizer()
    return summarizer.extract_subtitles(video_url)

def generate_timestamps(transcript: List[Dict]) -> List[Dict]:
    """Generate intelligent timestamps from transcript"""
    summarizer = YouTubeSummarizer()
    timestamps = summarizer.generate_timestamps(transcript)
    return [
        {
            'time': ts.time,
            'title': ts.title,
            'section_id': ts.section_id,
            'start_index': ts.start_index,
            'end_index': ts.end_index
        } for ts in timestamps
    ]

def summarize_section(transcript: List[Dict], section_id: int, timestamps: List[Dict]) -> str:
    """Summarize a specific section"""
    summarizer = YouTubeSummarizer()
    timestamp_objects = [
        Timestamp(
            time=ts['time'],
            title=ts['title'],
            section_id=ts['section_id'],
            start_index=ts['start_index'],
            end_index=ts['end_index']
        ) for ts in timestamps
    ]
    return summarizer.summarize_section(transcript, section_id, timestamp_objects)

def summarize_full_video(transcript: str, timestamps: List[Dict], video_info: Dict) -> str:
    """Generate full video summary"""
    summarizer = YouTubeSummarizer()
    video_info_obj = VideoInfo(
        video_id=video_info.get('video_id', ''),
        title=video_info.get('title', ''),
        duration=video_info.get('duration', ''),
        channel=video_info.get('channel', ''),
        upload_date=video_info.get('upload_date', '')
    )
    timestamp_objects = [
        Timestamp(
            time=ts['time'],
            title=ts['title'],
            section_id=ts['section_id'],
            start_index=ts['start_index'],
            end_index=ts['end_index']
        ) for ts in timestamps
    ]
    return summarizer.summarize_full_video(transcript, timestamp_objects, video_info_obj)

def process_video(video_url: str) -> Dict:
    """Main function to process video and return complete summary"""
    summarizer = YouTubeSummarizer()
    return summarizer.process_video(video_url)


if __name__ == "__main__":
    # Test the system
    test_url = input("Enter YouTube URL: ")
    result = process_video(test_url)
    
    if result['success']:
        print(f"\n✅ Success! Processing time: {result['processing_time']:.2f}s")
        print(f"📺 Video: {result['title']}")
        print(f"⏰ Duration: {result['duration']}")
        print(f"📝 Executive Summary: {result['executive_summary']}")
        print(f"🔢 Timestamps: {len(result['timestamps'])} sections")
    else:
        print(f"❌ Error: {result['error_message']}")
        if 'suggestions' in result:
            print("\n💡 Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")



# import os
# import time
# import textwrap
# from dotenv import load_dotenv
# from youtube_transcript_api import YouTubeTranscriptApi
# import google.generativeai as genai
# import subprocess

# # ✅ Load API Key
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=GOOGLE_API_KEY)
# gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# # ✅ Get Transcript and Cache
# def get_transcript(video_id, cache_dir="transcripts"):
#     os.makedirs(cache_dir, exist_ok=True)
#     file_path = os.path.join(cache_dir, f"{video_id}.txt")

#     if os.path.exists(file_path):
#         with open(file_path, "r", encoding="utf-8") as f:
#             return f.read()

#     transcript = YouTubeTranscriptApi.get_transcript(video_id)
#     text = " ".join([segment["text"] for segment in transcript])

#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(text)

#     return text

# # ✅ Gemini Summarizer
# def summarize_with_gemini(transcript):
#     print("🔷 Trying Gemini 1.5 Flash...")
#     prompt = f"""
# You are a helpful assistant that summarizes long educational transcripts for students.

# Summarize the following transcript clearly, using:
# - Bullet points
# - Headings for topics
# - Simple and student-friendly language

# Transcript:
# {transcript[:25000]}
# """
#     try:
#         response = gemini_model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         print("❌ Gemini failed:", e)
#         return None

# # ✅ Mistral 7B via Ollama
# def summarize_with_mistral(transcript):
#     print("🔸 Falling back to Mistral 7B (Ollama)...")
#     mistral_prompt = f"""
# You are an assistant that summarizes transcripts for students. Make the summary clear and concise with bullet points.

# Transcript:
# {transcript[:4000]}
# """

#     result = subprocess.run(
#         ["ollama", "run", "mistral"],
#         input=mistral_prompt,
#         text=True,
#         capture_output=True
#     )
#     return result.stdout.strip() if result.returncode == 0 else "⚠️ Mistral summarization failed."

# # ✅ Main Controller
# def summarize_video(video_id):
#     transcript = get_transcript(video_id)
#     summary = summarize_with_gemini(transcript)
#     if summary:
#         print("✅ Gemini summary completed.")
#         return summary
#     else:
#         summary = summarize_with_mistral(transcript)
#         print("✅ Mistral fallback completed.")
#         return summary

# # ✅ Run
# if __name__ == "__main__":
#     video_id = "tRZGeaHPoaw"  # Change this to any YouTube video ID
#     final_summary = summarize_video(video_id)

#     print("\n📄 FINAL SUMMARY:\n")
#     print(textwrap.fill(final_summary, width=100))
