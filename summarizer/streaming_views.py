import os
import json
import re
import time
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import sys

# Add the parent directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def is_valid_youtube_url(url):
    """Validate YouTube URL format"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False

def interactive_view(request):
    """Serve the interactive streaming template"""
    return render(request, 'summarizer/interactive_result.html')

@csrf_exempt
@require_http_methods(["POST"])
def process_video_interactive(request):
    """Interactive video processing - returns timestamps first, then streams summary"""
    try:
        data = json.loads(request.body)
        video_url = data.get('video_url', '').strip()
        
        if not video_url:
            return JsonResponse({
                'success': False,
                'error': 'Please provide a YouTube URL'
            })
        
        # Validate YouTube URL
        if not is_valid_youtube_url(video_url):
            return JsonResponse({
                'success': False,
                'error': 'Please provide a valid YouTube URL'
            })
        
        # Import here to avoid circular imports
        from core_summarizer import YouTubeSummarizer
        
        summarizer = YouTubeSummarizer()
        
        # Step 1: Extract subtitles and generate timestamps quickly
        subtitle_result = summarizer.extract_subtitles(video_url)
        if not subtitle_result['success']:
            return JsonResponse({
                'success': False,
                'error': subtitle_result['error']
            })
        
        # Generate timestamps immediately
        timestamps = summarizer.generate_timestamps(
            subtitle_result['transcript'], 
            subtitle_result['video_info']
        )
        
        # Return timestamps immediately (partial response)
        partial_result = {
            'success': True,
            'status': 'partial',
            'stage': 'timestamps_ready',
            'timestamps': timestamps,
            'video_info': subtitle_result['video_info'],
            'processing_time': subtitle_result['processing_time']
        }
        
        # Store partial result and video data for streaming
        request.session['current_processing'] = {
            'transcript': subtitle_result['transcript'],
            'timestamps': timestamps,
            'video_info': subtitle_result['video_info']
        }
        
        return JsonResponse(partial_result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def stream_summary(request):
    """Stream the full summary with typewriter effect"""
    try:
        # Get processing data from session
        processing_data = request.session.get('current_processing')
        if not processing_data:
            return JsonResponse({
                'success': False,
                'error': 'No processing data found. Please start video processing first.'
            })
        
        def generate_summary_stream():
            """Generator function for streaming summary"""
            try:
                from core_summarizer import YouTubeSummarizer
                
                summarizer = YouTubeSummarizer()
                
                # Generate full summary
                full_summary = summarizer.summarize_full_video(
                    processing_data['transcript'],
                    processing_data['timestamps'],
                    processing_data['video_info']
                )
                
                if not full_summary:
                    yield f"data: {{\"error\": \"Failed to generate summary\"}}\n\n"
                    return
                
                # Split summary into sentences for streaming
                sentences = re.split(r'(?<=[.!?])\s+', full_summary)
                
                # Stream each sentence with a small delay
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        chunk_data = {
                            'type': 'sentence',
                            'content': sentence.strip() + ' ',
                            'index': i,
                            'total': len(sentences),
                            'complete': False
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        time.sleep(0.1)  # Small delay for typewriter effect
                
                # Send completion signal
                completion_data = {
                    'type': 'complete',
                    'content': '',
                    'complete': True,
                    'full_summary': full_summary
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
                # Store complete result in session
                complete_result = {
                    'success': True,
                    'timestamps': processing_data['timestamps'],
                    'full_summary': full_summary,
                    'video_info': processing_data['video_info']
                }
                request.session['last_result'] = complete_result
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'content': f'Summary generation failed: {str(e)}',
                    'complete': True
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        response = StreamingHttpResponse(
            generate_summary_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Streaming failed: {str(e)}'
        })


