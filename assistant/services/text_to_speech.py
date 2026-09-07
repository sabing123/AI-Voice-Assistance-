import os
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def synthesize(self, text: str, output_path: str) -> str:
        """
        Synthesize text to speech audio and save to output_path.
        """
        raise NotImplementedError("Subclasses must implement synthesize")


class gTTSService(TextToSpeechService):
    def __init__(self):
        self.lang = os.getenv('TTS_LANG', 'en')

    def synthesize(self, text: str, output_path: str) -> str:
        if not text:
            return None

        try:
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(output_path)
            if os.path.exists(output_path):
                return output_path
            return None
        except Exception as e:
            logger.exception("gTTS synthesis failed")
            return None


def get_text_to_speech_service() -> TextToSpeechService:
    return gTTSService()
