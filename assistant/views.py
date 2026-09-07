import os
import uuid
from django.conf import settings
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ChatInputSerializer
from .services.ai import get_ai_service
from .services.speech_to_text import get_speech_to_text_service
from .services.text_to_speech import get_text_to_speech_service

class IndexView(TemplateView):
    template_name = 'assistant/index.html'


class ConversationListCreateAPIView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            conversations = Conversation.objects.filter(user=request.user)
        else:
            conversations = Conversation.objects.none()
        serializer = ConversationSerializer(conversations, many=True)
        return Response({
            "success": True,
            "conversations": serializer.data
        })

    def post(self, request):
        title = request.data.get('title', 'New Conversation')
        user = request.user if request.user.is_authenticated else None
        conversation = Conversation.objects.create(title=title, user=user)
        serializer = ConversationSerializer(conversation)
        return Response({
            "success": True,
            "conversation": serializer.data
        }, status=status.HTTP_201_CREATED)


class ConversationDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({
                "success": False,
                "error": "Conversation not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if conversation.user and conversation.user != request.user:
            return Response({
                "success": False,
                "error": "Unauthorized access to conversation."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationSerializer(conversation)
        return Response({
            "success": True,
            "conversation": serializer.data
        })

    def delete(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({
                "success": False,
                "error": "Conversation not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if conversation.user and conversation.user != request.user:
            return Response({
                "success": False,
                "error": "Unauthorized access to conversation."
            }, status=status.HTTP_403_FORBIDDEN)

        conversation.delete()
        return Response({
            "success": True,
            "message": "Conversation deleted successfully."
        })

    def patch(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({
                "success": False,
                "error": "Conversation not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if conversation.user and conversation.user != request.user:
            return Response({
                "success": False,
                "error": "Unauthorized access to conversation."
            }, status=status.HTTP_403_FORBIDDEN)

        new_title = request.data.get('title')
        if not new_title:
            return Response({
                "success": False,
                "error": "Title is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        conversation.title = new_title[:100]
        conversation.save()
        serializer = ConversationSerializer(conversation)
        return Response({
            "success": True,
            "conversation": serializer.data
        })


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        user_message_text = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id)
                if conversation.user and conversation.user != request.user:
                    return Response({
                        "success": False,
                        "error": "Unauthorized access to conversation."
                    }, status=status.HTTP_403_FORBIDDEN)
            except Conversation.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "Conversation not found."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            title_text = user_message_text[:30] + ('...' if len(user_message_text) > 30 else '')
            user = request.user if request.user.is_authenticated else None
            conversation = Conversation.objects.create(title=title_text, user=user)

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message_text
        )

        ai_service = get_ai_service()
        recent_messages = conversation.messages.order_by('-created_at')[1:11]
        context = [{"role": msg.role, "content": msg.content} for msg in reversed(recent_messages)]

        try:
            assistant_response_text = ai_service.generate_response(user_message_text, context=context)
        except Exception:
            return Response({
                "success": False,
                "error": "Failed to generate AI response. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        assistant_msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_response_text
        )
        conversation.save()

        audio_url = None
        try:
            tts_service = get_text_to_speech_service()
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            audio_filename = f"tts_{uuid.uuid4()}.mp3"
            audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_filename)
            synthesized_path = tts_service.synthesize(assistant_response_text, audio_filepath)
            if synthesized_path and os.path.exists(synthesized_path):
                audio_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{audio_filename}")
        except Exception:
            pass

        return Response({
            "success": True,
            "conversation_id": conversation.id,
            "response": assistant_response_text,
            "audio_url": audio_url,
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "created_at": assistant_msg.created_at
            }
        }, status=status.HTTP_200_OK)


class VoiceAPIView(APIView):
    def post(self, request):
        if 'audio' not in request.FILES:
            return Response({
                "success": False,
                "error": "No audio file provided."
            }, status=status.HTTP_400_BAD_REQUEST)

        audio_file = request.FILES['audio']
        conversation_id = request.data.get('conversation_id')

        if audio_file.size > 10 * 1024 * 1024:
            return Response({
                "success": False,
                "error": "Audio file is too large (max 10MB)."
            }, status=status.HTTP_400_BAD_REQUEST)

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        ext = os.path.splitext(audio_file.name)[1] or '.webm'
        temp_filename = f"upload_{uuid.uuid4()}{ext}"
        temp_filepath = os.path.join(settings.MEDIA_ROOT, temp_filename)

        try:
            with open(temp_filepath, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            stt_service = get_speech_to_text_service()
            user_message_text = stt_service.transcribe(temp_filepath)

            if not user_message_text:
                return Response({
                    "success": False,
                    "error": "Could not transcribe audio."
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({
                "success": False,
                "error": "Speech-to-text processing failed."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    pass

        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id)
                if conversation.user and conversation.user != request.user:
                    return Response({
                        "success": False,
                        "error": "Unauthorized access to conversation."
                    }, status=status.HTTP_403_FORBIDDEN)
            except Conversation.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "Conversation not found."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            title_text = user_message_text[:30] + ('...' if len(user_message_text) > 30 else '')
            user = request.user if request.user.is_authenticated else None
            conversation = Conversation.objects.create(title=title_text, user=user)

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message_text
        )

        ai_service = get_ai_service()
        recent_messages = conversation.messages.order_by('-created_at')[1:11]
        context = [{"role": msg.role, "content": msg.content} for msg in reversed(recent_messages)]

        try:
            assistant_response_text = ai_service.generate_response(user_message_text, context=context)
        except Exception:
            return Response({
                "success": False,
                "error": "Failed to generate AI response."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        assistant_msg = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_response_text
        )
        conversation.save()

        audio_url = None
        try:
            tts_service = get_text_to_speech_service()
            tts_filename = f"tts_{uuid.uuid4()}.mp3"
            tts_filepath = os.path.join(settings.MEDIA_ROOT, tts_filename)
            synthesized_path = tts_service.synthesize(assistant_response_text, tts_filepath)
            if synthesized_path and os.path.exists(synthesized_path):
                audio_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{tts_filename}")
        except Exception:
            pass

        return Response({
            "success": True,
            "conversation_id": conversation.id,
            "transcription": user_message_text,
            "response": assistant_response_text,
            "audio_url": audio_url,
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "created_at": assistant_msg.created_at
            }
        }, status=status.HTTP_200_OK)


class TranscribeAPIView(APIView):
    def post(self, request):
        if 'audio' not in request.FILES:
            return Response({
                "success": False,
                "error": "No audio file provided."
            }, status=status.HTTP_400_BAD_REQUEST)

        audio_file = request.FILES['audio']

        if audio_file.size > 10 * 1024 * 1024:
            return Response({
                "success": False,
                "error": "Audio file is too large (max 10MB)."
            }, status=status.HTTP_400_BAD_REQUEST)

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        ext = os.path.splitext(audio_file.name)[1] or '.webm'
        temp_filename = f"transcribe_{uuid.uuid4()}{ext}"
        temp_filepath = os.path.join(settings.MEDIA_ROOT, temp_filename)

        try:
            with open(temp_filepath, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            stt_service = get_speech_to_text_service()
            transcription_text = stt_service.transcribe(temp_filepath)

            if not transcription_text:
                return Response({
                    "success": False,
                    "error": "Could not transcribe audio."
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "success": True,
                "transcription": transcription_text
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "success": False,
                "error": "Speech-to-text processing failed."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    pass
