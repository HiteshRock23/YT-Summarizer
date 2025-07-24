from django.urls import path
from . import views
from . import streaming_views

app_name = 'summarizer'

urlpatterns = [
    path('', views.home, name='home'),
    path('process/', views.process_video, name='process_video'),
    path('demo/', views.demo_video, name='demo_video'),
    path('result/', views.result, name='result'),
    # Interactive streaming endpoints
    path('interactive/', streaming_views.interactive_view, name='interactive'),
    path('process-interactive/', streaming_views.process_video_interactive, name='process_video_interactive'),
    path('stream-summary/', streaming_views.stream_summary, name='stream_summary'),
]