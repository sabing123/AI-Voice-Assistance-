from django.urls import path
from .views import (
    IndexView, ChatAPIView, VoiceAPIView, TranscribeAPIView,
    ConversationListCreateAPIView, ConversationDetailAPIView
)

app_name = 'assistant'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('api/chat/', ChatAPIView.as_view(), name='chat_api'),
    path('api/voice/', VoiceAPIView.as_view(), name='voice_api'),
    path('api/transcribe/', TranscribeAPIView.as_view(), name='transcribe_api'),
    path('api/conversations/', ConversationListCreateAPIView.as_view(), name='conversation_list_create'),
    path('api/conversations/<int:pk>/', ConversationDetailAPIView.as_view(), name='conversation_detail'),
]
