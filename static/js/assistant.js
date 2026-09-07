document.addEventListener('alpine:init', () => {
    Alpine.data('voiceAssistant', () => ({
        messages: [
            { role: 'assistant', content: 'Hello! I am your AI Voice Assistant. You can type or speak to me.', audioUrl: null }
        ],
        conversations: [],
        inputMessage: '',
        conversationId: null,
        isLoading: false,
        isRecording: false,
        errorMessage: '',
        theme: localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'),
        globalSoundEnabled: false,
        mediaRecorder: null,
        audioChunks: [],
        currentPlayingAudio: null,

        async initApp() {
            document.documentElement.setAttribute('data-theme', this.theme);
            await this.fetchConversations();
        },

        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', this.theme);
            document.documentElement.setAttribute('data-theme', this.theme);
        },

        async fetchConversations() {
            try {
                const response = await fetch('/api/conversations/');
                const data = await response.json();
                if (data.success) {
                    this.conversations = data.conversations;
                }
            } catch (err) {
                console.error('Failed to fetch conversations:', err);
            }
        },

        async loadConversation(id) {
            try {
                const response = await fetch(`/api/conversations/${id}/`);
                const data = await response.json();
                if (data.success) {
                    this.conversationId = data.conversation.id;
                    this.messages = data.conversation.messages.map(m => ({
                        role: m.role,
                        content: m.content,
                        audioUrl: null
                    }));
                    this.scrollToBottom();
                } else {
                    this.errorMessage = data.error || 'Failed to load conversation.';
                }
            } catch (err) {
                console.error('Failed to load conversation:', err);
                this.errorMessage = 'Network error while loading conversation.';
            }
        },

        startNewChat() {
            this.conversationId = null;
            this.messages = [
                { role: 'assistant', content: 'Hello! I am your AI Voice Assistant. You can type or speak to me.', audioUrl: null }
            ];
            this.inputMessage = '';
            this.errorMessage = '';
        },

        toggleGlobalSound() {
            this.globalSoundEnabled = !this.globalSoundEnabled;
            if (!this.globalSoundEnabled) {
                this.stopAllAudio();
            }
        },

        stopAllAudio() {
            if (this.currentPlayingAudio) {
                this.currentPlayingAudio.pause();
                this.currentPlayingAudio.currentTime = 0;
                this.currentPlayingAudio = null;
            }
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
        },

        async sendMessage() {
            const text = this.inputMessage.trim();
            if (!text || this.isLoading) return;

            this.errorMessage = '';
            this.messages.push({ role: 'user', content: text, audioUrl: null });
            this.inputMessage = '';
            this.isLoading = true;

            try {
                const response = await fetch('/api/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({
                        message: text,
                        conversation_id: this.conversationId
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.conversationId = data.conversation_id;
                    this.messages.push({ role: 'assistant', content: data.response, audioUrl: data.audio_url });
                    if (data.audio_url && this.globalSoundEnabled) {
                        this.playAudio(data.audio_url);
                    }
                    await this.fetchConversations();
                } else {
                    this.errorMessage = data.error || 'Failed to get a response from the server.';
                }
            } catch (err) {
                console.error('Chat error:', err);
                this.errorMessage = 'Network error occurred. Please try again.';
            } finally {
                this.isLoading = false;
                this.scrollToBottom();
            }
        },

        async toggleRecording() {
            if (this.isRecording) {
                this.stopRecording();
            } else {
                await this.startRecording();
            }
        },

        async startRecording() {
            this.errorMessage = '';
            this.audioChunks = [];

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.errorMessage = 'Audio recording is not supported by your browser.';
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(stream);

                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.audioChunks.push(event.data);
                    }
                };

                this.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                    stream.getTracks().forEach(track => track.stop());
                    await this.uploadAudio(audioBlob);
                };

                this.mediaRecorder.start();
                this.isRecording = true;
            } catch (err) {
                console.error('Microphone error:', err);
                this.errorMessage = 'Microphone permission denied or device unavailable.';
                this.isRecording = false;
            }
        },

        stopRecording() {
            if (this.mediaRecorder && this.isRecording) {
                this.mediaRecorder.stop();
                this.isRecording = false;
            }
        },

        async uploadAudio(audioBlob) {
            this.isLoading = true;
            this.errorMessage = '';
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice_input.webm');
            if (this.conversationId) {
                formData.append('conversation_id', this.conversationId);
            }

            try {
                const response = await fetch('/api/voice/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    this.conversationId = data.conversation_id;
                    this.messages.push({ role: 'user', content: data.transcription, audioUrl: null });
                    this.messages.push({ role: 'assistant', content: data.response, audioUrl: data.audio_url });
                    if (data.audio_url && this.globalSoundEnabled) {
                        this.playAudio(data.audio_url);
                    }
                    await this.fetchConversations();
                } else {
                    this.errorMessage = data.error || 'Failed to process voice input.';
                }
            } catch (err) {
                console.error('Voice upload error:', err);
                this.errorMessage = 'Network error occurred during voice upload.';
            } finally {
                this.isLoading = false;
                this.scrollToBottom();
            }
        },

        playAudio(url) {
            if (!this.globalSoundEnabled) return;

            this.stopAllAudio();

            const audio = new Audio(url);
            this.currentPlayingAudio = audio;
            audio.play().catch(err => {
                console.warn('Audio autoplay prevented or failed:', err);
            });

            audio.onended = () => {
                if (this.currentPlayingAudio === audio) {
                    this.currentPlayingAudio = null;
                }
            };
        },

        playMessageAudio(msg) {
            if (!this.globalSoundEnabled) return;

            if (this.currentPlayingAudio || ('speechSynthesis' in window && window.speechSynthesis.speaking)) {
                this.stopAllAudio();
                return;
            }

            if (msg.audioUrl) {
                this.playAudio(msg.audioUrl);
            } else if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(msg.content);
                window.speechSynthesis.speak(utterance);
            }
        },

        scrollToBottom() {
            this.$nextTick(() => {
                const chatContainer = document.getElementById('chat-container');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            });
        },

        async deleteConversation(id) {
            if (!confirm('Are you sure you want to delete this conversation?')) return;
            try {
                const response = await fetch(`/api/conversations/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });
                const data = await response.json();
                if (data.success) {
                    this.conversations = this.conversations.filter(c => c.id !== id);
                    if (this.conversationId === id) {
                        this.startNewChat();
                    }
                } else {
                    this.errorMessage = data.error || 'Failed to delete conversation.';
                }
            } catch (err) {
                console.error('Delete conversation error:', err);
                this.errorMessage = 'Network error while deleting conversation.';
            }
        },

        showRenameModal: false,
        renamingId: null,
        newChatTitle: '',

        openRenameModal(id, currentTitle) {
            this.renamingId = id;
            this.newChatTitle = currentTitle;
            this.showRenameModal = true;
            this.$nextTick(() => {
                const input = document.getElementById('rename-input-field');
                if (input) input.focus();
            });
        },

        closeRenameModal() {
            this.showRenameModal = false;
            this.renamingId = null;
            this.newChatTitle = '';
        },

        async submitRename() {
            const id = this.renamingId;
            const title = this.newChatTitle.trim();
            if (!id || !title) return;

            try {
                const response = await fetch(`/api/conversations/${id}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({ title: title })
                });
                const data = await response.json();
                if (data.success) {
                    const conv = this.conversations.find(c => c.id === id);
                    if (conv) {
                        conv.title = data.conversation.title;
                    }
                    this.closeRenameModal();
                } else {
                    this.errorMessage = data.error || 'Failed to rename conversation.';
                }
            } catch (err) {
                console.error('Rename conversation error:', err);
                this.errorMessage = 'Network error while renaming conversation.';
            }
        },

        renameConversation(id, currentTitle) {
            this.openRenameModal(id, currentTitle);
        },

        getCsrfToken() {
            let cookieValue = null;
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring('csrftoken='.length));
                    break;
                }
            }
            return cookieValue;
        }
    }));
});
