import os
import json
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
import sys
import time
import threading
from queue import Queue

# Add the parent directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_summarizer import process_video as process_video_core
from llm_handler import MultiLLMHandler

def home(request):
    """Home page view"""
    return render(request, 'summarizer/home.html')

@csrf_exempt
@require_http_methods(["POST"])
def process_video(request):
    """Process YouTube video and return results"""
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
        
        # Process the video
        result = process_video_core(video_url)
        
        if result['success']:
            # Store result in session
            request.session['last_result'] = result
            
            return JsonResponse({
                'success': True,
                'data': {
                    'title': result['title'],
                    'channel': result['channel'],
                    'duration': result['duration'],
                    'executive_summary': result['executive_summary'],
                    'timestamps': result['timestamps'],
                    'full_summary': result['full_summary'],
                    'processing_time': result['processing_time']
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error_message', 'Failed to process video'),
                'suggestions': result.get('suggestions', [])
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })



def demo_video(request):
    """Demo video processing"""
    demo_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual demo video
    
    try:
        result = process_video_core(demo_url)
        
        if result['success']:
            request.session['last_result'] = result
            return render(request, 'summarizer/result_simple.html', {
                'video_title': result['title'],
                'channel': result['channel'],
                'duration': result['duration'],
                'executive_summary': result['executive_summary'],
                'timestamps': result['timestamps'],
                'full_summary': result['full_summary'],
                'processing_time': result['processing_time'],
                'is_demo': True
            })
        else:
            messages.error(request, result.get('error_message', 'Demo failed'))
            return redirect('summarizer:home')
            
    except Exception as e:
        messages.error(request, f'Demo error: {str(e)}')
        return redirect('summarizer:home')

def is_valid_youtube_url(url):
    """Validate YouTube URL format"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+'
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False

def get_llm_status(request):
    """Get LLM provider status"""
    try:
        handler = MultiLLMHandler()
        status = handler.get_status()
        return JsonResponse(status)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }) 
    
def result(request):
    # Get the last result from session
    result = request.session.get('last_result')
    if not result:
        return redirect('summarizer:home')
    return render(request, 'summarizer/result_simple.html', result)