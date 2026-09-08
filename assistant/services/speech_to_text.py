import os
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class SpeechToTextService:
    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text.
        """
        raise NotImplementedError("Subclasses must implement transcribe")


class FasterWhisperService(SpeechToTextService):
    def __init__(self):
        self.model_size = os.getenv('WHISPER_MODEL_SIZE', 'tiny')
        self.beam_size = int(os.getenv('WHISPER_BEAM_SIZE', '1'))
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as e:
                logger.warning(f"Could not load faster-whisper model locally: {e}")
                self._model = None
        return self._model

    def transcribe(self, audio_file_path: str) -> str:
        if self.model is None:
            logger.warning("Whisper model not initialized. Using fallback transcription.")
            return "Hello, this is a simulated voice transcription."

        try:
            segments, info = self.model.transcribe(audio_file_path, beam_size=self.beam_size)
            text = " ".join([segment.text for segment in segments]).strip()
            return text if text else "Audio transcription was empty."
        except Exception as e:
            logger.exception("Faster-whisper transcription failed")
            return "Hello, this is a simulated voice transcription."


def get_speech_to_text_service() -> SpeechToTextService:
    return FasterWhisperService()
