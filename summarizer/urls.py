from django.urls import path
from . import views

app_name = 'summarizer'

urlpatterns = [
    path('', views.home, name='home'),
    path('process/', views.process_video, name='process_video'),
    path('download/<str:filename>/', views.download_pdf, name='download_pdf'),
    path('demo/', views.demo_video, name='demo_video'),
] 