import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AIService:
    def generate_response(self, message: str, context: list = None) -> str:
        """
        Generate a response given a user message and optional context.
        """
        raise NotImplementedError("Subclasses must implement generate_response")


class GeminiAIService(AIService):
    def __init__(self):
        self.api_key = os.getenv('AI_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.configured_model = os.getenv('AI_MODEL', 'gemini-3.6-flash')

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to configure Gemini API: {e}")

    def _get_working_model(self):
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name.replace('models/', '')
                    available_models.append(model_name)

            if available_models:
                if self.configured_model in available_models:
                    return self.configured_model
                return available_models[0]
        except Exception as e:
            logger.warning(f"Could not list Gemini models dynamically: {e}")

        return self.configured_model

    def generate_response(self, message: str, context: list = None) -> str:
        if not self.api_key:
            logger.warning("AI_API_KEY / GEMINI_API_KEY not configured. Using fallback AI response.")
            return f"Hello! I received your message: \"{message}\". (Gemini AI running in fallback mode because API key is not set)."

        model_name = self._get_working_model()
        models_to_try = [
            model_name,
            self.configured_model,
            'gemini-3.6-flash',
            'gemini-3.5-flash-lite',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro'
        ]
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = None
        for m_name in models_to_try:
            try:
                model = genai.GenerativeModel(m_name)

                history = []
                if context:
                    for msg in context:
                        role = "user" if msg['role'] == 'user' else "model"
                        history.append({"role": role, "parts": [msg['content']]})

                chat = model.start_chat(history=history)
                response = chat.send_message(message)
                return response.text.strip()
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini model '{m_name}' failed: {e}")
                continue

        logger.exception(f"All Gemini models failed. Last error: {last_error}")
        return f"Hello! I received your message: \"{message}\". (Gemini API Error: {last_error})"


def get_ai_service() -> AIService:
    return GeminiAIService()
