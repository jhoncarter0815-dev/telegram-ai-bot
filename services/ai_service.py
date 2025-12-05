"""
AI Service module for Google Gemini integration.
Provides unified interface for AI interactions including:
- Text generation (chat)
- Image analysis
- Audio transcription
"""

import logging
from typing import List, Dict, Tuple, Optional
from enum import Enum
import asyncio
import time

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)


class AIModel(Enum):
    """Available AI models."""
    GEMINI_20_FLASH = "gemini-2.0-flash"
    GEMINI_25_FLASH = "gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"


class AIService:
    """AI service for text generation using Google Gemini."""

    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.gemini_models = {
            "gemini-2.0-flash": genai.GenerativeModel("models/gemini-2.0-flash"),
            "gemini-2.5-flash": genai.GenerativeModel("models/gemini-2.5-flash"),
            "gemini-2.5-pro": genai.GenerativeModel("models/gemini-2.5-pro"),
        }

        # System prompts
        self.system_prompt = """You are a helpful, friendly, and knowledgeable AI assistant.
You provide accurate, helpful responses while being conversational and engaging.
You can help with a wide range of tasks including answering questions, creative writing,
coding help, analysis, and general conversation. Be concise but thorough."""

    def is_gemini_model(self, model: str) -> bool:
        """Check if model is a Gemini model."""
        return model.startswith("gemini-")

    async def _call_gemini(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.0-flash"
    ) -> Tuple[str, int]:
        """Call Gemini API."""
        try:
            gemini_model = self.gemini_models.get(model, self.gemini_models["gemini-2.0-flash"])
            
            # Convert messages to Gemini format
            history = []
            for msg in messages[:-1]:  # All except last
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
            chat = gemini_model.start_chat(history=history)
            
            # Send the last message
            last_message = messages[-1]["content"] if messages else ""
            response = await asyncio.to_thread(chat.send_message, last_message)
            
            # Estimate tokens (Gemini doesn't always provide exact count)
            tokens = len(last_message.split()) + len(response.text.split())
            return response.text, tokens * 2  # Rough estimation
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        model: str = None,
        use_fallback: bool = True
    ) -> Tuple[str, str, int]:
        """
        Generate AI response with optional fallback.

        Returns: (response_text, model_used, tokens_used)
        """
        model = model or settings.default_ai_model

        # Ensure we use a valid Gemini model
        if not self.is_gemini_model(model):
            model = settings.default_ai_model

        conversation_history = conversation_history or []

        # Build messages list
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        try:
            response, tokens = await self._call_gemini(messages, model)
            return response, model, tokens
        except Exception as e:
            logger.warning(f"Model {model} failed: {e}")
            if use_fallback:
                return await self._fallback_generate(messages, model)
            raise

        return "I'm sorry, I couldn't process your request.", model, 0

    async def _fallback_generate(
        self,
        messages: List[Dict[str, str]],
        failed_model: str
    ) -> Tuple[str, str, int]:
        """Try alternate Gemini model if primary fails."""
        fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"]

        for fallback_model in fallback_models:
            if fallback_model != failed_model:
                try:
                    logger.info(f"Trying fallback model: {fallback_model}")
                    response, tokens = await self._call_gemini(messages, fallback_model)
                    return response, fallback_model, tokens
                except Exception as e:
                    logger.warning(f"Fallback {fallback_model} failed: {e}")
                    continue

        logger.error("All models failed")
        return "I'm experiencing technical difficulties. Please try again later.", failed_model, 0

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str = "Describe this image in detail.",
        model: str = None
    ) -> Tuple[str, str, int]:
        """Analyze an image using Gemini Vision."""
        try:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_data))
            gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")
            response = await asyncio.to_thread(
                gemini_model.generate_content, [prompt, image]
            )
            tokens = len(prompt.split()) + len(response.text.split())
            return response.text, "gemini-2.0-flash", tokens * 2
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return f"Sorry, I couldn't analyze the image: {str(e)}", "gemini-2.0-flash", 0

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using Gemini."""
        try:
            import io
            # Use Gemini for audio transcription
            gemini_model = genai.GenerativeModel("models/gemini-2.0-flash")

            # Convert audio to base64 for Gemini
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            response = await asyncio.to_thread(
                gemini_model.generate_content,
                [
                    "Please transcribe the following audio. Only output the transcription, nothing else.",
                    {"mime_type": "audio/ogg", "data": audio_base64}
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return None

    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available AI models."""
        return [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "Google", "description": "Fast responses"},
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "Google", "description": "Latest flash model"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "Google", "description": "Most capable"},
        ]
