from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from .models import Conversation, Message

class AssistantModelTests(TestCase):
    def test_conversation_creation(self):
        conv = Conversation.objects.create(title="Test Chat")
        self.assertEqual(str(conv), f"Test Chat ({conv.id})")
        self.assertEqual(conv.title, "Test Chat")

    def test_message_creation(self):
        conv = Conversation.objects.create(title="Test Chat")
        msg = Message.objects.create(conversation=conv, role='user', content='Hello AI')
        self.assertEqual(str(msg), "[user] Hello AI")
        self.assertEqual(msg.conversation, conv)


class AssistantAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

    def test_chat_api_new_conversation(self):
        url = reverse('assistant:chat_api')
        data = {"message": "Hello from test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('conversation_id', response.data)
        self.assertIn('response', response.data)

        # Verify messages stored in DB
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2) # User message + Assistant response

    def test_chat_api_existing_conversation(self):
        conv = Conversation.objects.create(title="Existing Chat", user=self.user)
        url = reverse('assistant:chat_api')
        data = {"message": "Follow up message", "conversation_id": conv.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['conversation_id'], conv.id)
        self.assertEqual(conv.messages.count(), 2)

    def test_chat_api_empty_message(self):
        url = reverse('assistant:chat_api')
        data = {"message": ""}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_conversation_list_api(self):
        Conversation.objects.create(title="Chat 1", user=self.user)
        Conversation.objects.create(title="Chat 2", user=self.user)
        url = reverse('assistant:conversation_list_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['conversations']), 2)

    def test_voice_api_no_audio(self):
        url = reverse('assistant:voice_api')
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_voice_api_with_audio(self):
        url = reverse('assistant:voice_api')
        audio_file = SimpleUploadedFile("test_audio.webm", b"dummy audio content", content_type="audio/webm")
        response = self.client.post(url, {"audio": audio_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('transcription', response.data)
        self.assertIn('response', response.data)
