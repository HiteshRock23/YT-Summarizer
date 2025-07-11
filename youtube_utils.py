from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs


def get_video_id(youtube_url):
    """Extract the video ID from a YouTube URL."""
    query = urlparse(youtube_url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None


def get_transcript(youtube_url):
    """Fetch transcript for a YouTube video. Returns transcript as a string or raises an Exception."""
    video_id = get_video_id(youtube_url)
    if not video_id:
        raise ValueError('Invalid YouTube URL')
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript])
    except (TranscriptsDisabled, NoTranscriptFound):
        raise Exception('Transcript not available for this video.')
    except VideoUnavailable:
        raise Exception('Video unavailable.')
    except Exception as e:
        raise Exception(f'Error fetching transcript: {str(e)}') 