"""
Media service for handling voice messages, images, and file processing.
"""

import logging
import io
from typing import Optional, Tuple
import httpx

from telegram import File

logger = logging.getLogger(__name__)


class MediaService:
    """Handles media file downloads and processing."""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient()
    
    async def download_file(self, file: File) -> bytes:
        """Download a file from Telegram."""
        try:
            file_bytes = await file.download_as_bytearray()
            return bytes(file_bytes)
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def download_voice_message(self, file: File) -> bytes:
        """Download and return voice message bytes."""
        return await self.download_file(file)
    
    async def download_image(self, file: File) -> bytes:
        """Download and return image bytes."""
        return await self.download_file(file)
    
    async def convert_ogg_to_wav(self, ogg_data: bytes) -> bytes:
        """Convert OGG audio to WAV format."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_ogg(io.BytesIO(ogg_data))
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            return wav_buffer.getvalue()
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return ogg_data
    
    async def resize_image(
        self,
        image_data: bytes,
        max_size: Tuple[int, int] = (1024, 1024)
    ) -> bytes:
        """Resize image if it exceeds max dimensions."""
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Image resize error: {e}")
            return image_data
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

