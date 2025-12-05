"""
Multi-language support with translations.
"""

from typing import Dict

# Supported languages
LANGUAGES = {
    "en": "English 🇬🇧",
    "ru": "Русский 🇷🇺",
    "es": "Español 🇪🇸",
    "fr": "Français 🇫🇷",
    "de": "Deutsch 🇩🇪",
    "zh": "中文 🇨🇳",
    "ar": "العربية 🇸🇦",
    "pt": "Português 🇧🇷",
}

# Translation strings
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "welcome": {
        "en": "👋 Welcome to AI Assistant Bot!\n\nI'm powered by ChatGPT and Gemini AI. Ask me anything!\n\n🎯 Features:\n• Chat with advanced AI\n• Analyze images\n• Transcribe voice messages\n• Multiple AI models\n\nUse /help to see all commands.",
        "ru": "👋 Добро пожаловать в AI Ассистент Бот!\n\nЯ работаю на ChatGPT и Gemini AI. Спрашивайте что угодно!\n\n🎯 Возможности:\n• Общение с продвинутым ИИ\n• Анализ изображений\n• Расшифровка голосовых сообщений\n• Несколько моделей ИИ\n\nИспользуйте /help для списка команд.",
        "es": "👋 ¡Bienvenido al Bot Asistente AI!\n\nEstoy impulsado por ChatGPT y Gemini AI. ¡Pregúntame lo que quieras!\n\nUsa /help para ver todos los comandos.",
    },
    "help": {
        "en": "📚 **Available Commands**\n\n🤖 **Chat Commands:**\n/start - Start the bot\n/new - New conversation\n/history - View history\n\n⚙️ **Settings:**\n/settings - Your preferences\n/model - Change AI model\n/language - Change language\n\n💎 **Premium:**\n/subscribe - View plans\n/status - Subscription status\n\n❓ Just send me a message to chat!",
        "ru": "📚 **Доступные команды**\n\n🤖 **Команды чата:**\n/start - Запустить бота\n/new - Новый разговор\n/history - История\n\n⚙️ **Настройки:**\n/settings - Ваши настройки\n/model - Сменить модель ИИ\n/language - Сменить язык\n\n💎 **Премиум:**\n/subscribe - Планы подписки\n/status - Статус подписки",
        "es": "📚 **Comandos Disponibles**\n\n🤖 **Comandos de Chat:**\n/start - Iniciar el bot\n/new - Nueva conversación\n/history - Ver historial\n\n⚙️ **Configuración:**\n/settings - Tus preferencias\n/model - Cambiar modelo AI\n/language - Cambiar idioma",
    },
    "new_conversation": {
        "en": "🔄 Conversation cleared! Let's start fresh.",
        "ru": "🔄 Разговор очищен! Начнём заново.",
        "es": "🔄 ¡Conversación borrada! Empecemos de nuevo.",
    },
    "thinking": {
        "en": "🤔 Thinking...",
        "ru": "🤔 Думаю...",
        "es": "🤔 Pensando...",
    },
    "error_general": {
        "en": "❌ An error occurred. Please try again.",
        "ru": "❌ Произошла ошибка. Попробуйте снова.",
        "es": "❌ Ocurrió un error. Por favor, inténtalo de nuevo.",
    },
    "rate_limited": {
        "en": "⏳ You've reached your message limit. Upgrade to Premium for unlimited access!",
        "ru": "⏳ Вы достигли лимита сообщений. Обновитесь до Премиум для безлимитного доступа!",
        "es": "⏳ Has alcanzado tu límite de mensajes. ¡Actualiza a Premium para acceso ilimitado!",
    },
    "banned": {
        "en": "🚫 You have been banned from using this bot.",
        "ru": "🚫 Вы заблокированы в этом боте.",
        "es": "🚫 Has sido bloqueado de usar este bot.",
    },
    "subscribe_info": {
        "en": "💎 **Premium Subscription**\n\n✨ Benefits:\n• Unlimited messages\n• All AI models\n• Voice & image support\n• Priority response\n\n💫 Choose your plan:",
        "ru": "💎 **Премиум Подписка**\n\n✨ Преимущества:\n• Безлимитные сообщения\n• Все модели ИИ\n• Голос и изображения\n• Приоритетный ответ\n\n💫 Выберите план:",
    },
    "settings_menu": {
        "en": "⚙️ **Settings**\n\nCurrent model: {model}\nLanguage: {lang_display}\nSubscription: {subscription}",
        "ru": "⚙️ **Настройки**\n\nТекущая модель: {model}\nЯзык: {lang_display}\nПодписка: {subscription}",
        "es": "⚙️ **Configuración**\n\nModelo actual: {model}\nIdioma: {lang_display}\nSuscripción: {subscription}",
    },
    "model_changed": {
        "en": "✅ AI model changed to: {model}",
        "ru": "✅ Модель ИИ изменена на: {model}",
        "es": "✅ Modelo AI cambiado a: {model}",
    },
    "language_changed": {
        "en": "✅ Language changed to English",
        "ru": "✅ Язык изменён на Русский",
        "es": "✅ Idioma cambiado a Español",
    },
    "premium_active": {
        "en": "✨ Premium active until: {date}",
        "ru": "✨ Премиум активен до: {date}",
        "es": "✨ Premium activo hasta: {date}",
    },
    "not_premium": {
        "en": "You're on the free plan. Use /subscribe to upgrade!",
        "ru": "Вы на бесплатном плане. Используйте /subscribe для обновления!",
        "es": "Estás en el plan gratuito. ¡Usa /subscribe para actualizar!",
    },
    "voice_transcribed": {
        "en": "🎤 Voice message: \"{text}\"\n\n",
        "ru": "🎤 Голосовое сообщение: \"{text}\"\n\n",
        "es": "🎤 Mensaje de voz: \"{text}\"\n\n",
    },
    "image_received": {
        "en": "📸 Analyzing image...",
        "ru": "📸 Анализирую изображение...",
        "es": "📸 Analizando imagen...",
    },
    "history_header": {
        "en": "📜 **Conversation History**\n\n",
        "ru": "📜 **История разговора**\n\n",
        "es": "📜 **Historial de Conversación**\n\n",
    },
    "no_history": {
        "en": "No conversation history yet. Start chatting!",
        "ru": "Истории пока нет. Начните общаться!",
        "es": "Sin historial aún. ¡Empieza a chatear!",
    },
    # Generation features
    "generate_menu": {
        "en": "🎨 **AI Generation**\n\nCreate amazing content with AI!\n\n🖼️ **Image Generation** - Create images from text\n🎬 **Video Generation** - Create short videos from text",
        "ru": "🎨 **AI Генерация**\n\nСоздавайте контент с помощью ИИ!\n\n🖼️ **Генерация изображений** - Создавайте изображения из текста\n🎬 **Генерация видео** - Создавайте короткие видео из текста",
        "es": "🎨 **Generación AI**\n\n¡Crea contenido increíble con IA!\n\n🖼️ **Generación de imágenes** - Crea imágenes desde texto\n🎬 **Generación de video** - Crea videos cortos desde texto",
    },
    "generate_image_btn": {
        "en": "Generate Image",
        "ru": "Создать изображение",
        "es": "Generar Imagen",
    },
    "generate_video_btn": {
        "en": "Generate Video",
        "ru": "Создать видео",
        "es": "Generar Video",
    },
    "generate_premium_required": {
        "en": "⚠️ Image and video generation are Premium features. Upgrade to unlock!",
        "ru": "⚠️ Генерация изображений и видео - Премиум функции. Обновитесь для доступа!",
        "es": "⚠️ La generación de imágenes y videos son funciones Premium. ¡Actualiza para desbloquear!",
    },
    "premium_required": {
        "en": "⭐ **Premium Required**\n\nThis feature is only available for Premium subscribers.\n\nUpgrade now to unlock:\n• Image generation\n• Video generation\n• Voice messages\n• Image analysis\n• And more!",
        "ru": "⭐ **Требуется Премиум**\n\nЭта функция доступна только для Премиум подписчиков.\n\nОбновитесь сейчас для доступа к:\n• Генерация изображений\n• Генерация видео\n• Голосовые сообщения\n• Анализ изображений\n• И многое другое!",
        "es": "⭐ **Premium Requerido**\n\nEsta función solo está disponible para suscriptores Premium.\n\n¡Actualiza ahora para desbloquear:\n• Generación de imágenes\n• Generación de videos\n• Mensajes de voz\n• Análisis de imágenes\n• ¡Y más!",
    },
    "upgrade_premium_btn": {
        "en": "Upgrade to Premium",
        "ru": "Обновить до Премиум",
        "es": "Actualizar a Premium",
    },
    "back_btn": {
        "en": "Back",
        "ru": "Назад",
        "es": "Volver",
    },
    "cancel_btn": {
        "en": "Cancel",
        "ru": "Отмена",
        "es": "Cancelar",
    },
    "image_prompt_request": {
        "en": "🖼️ **Image Generation**\n\nDescribe the image you want to create.\n\n💡 Tips:\n• Be specific and detailed\n• Include style (realistic, cartoon, etc.)\n• Mention colors, lighting, mood\n\nExample: \"A majestic lion in a sunset savanna, realistic photography style, golden hour lighting\"",
        "ru": "🖼️ **Генерация изображения**\n\nОпишите изображение, которое хотите создать.\n\n💡 Советы:\n• Будьте конкретны и детальны\n• Укажите стиль (реалистичный, мультяшный и т.д.)\n• Упомяните цвета, освещение, настроение\n\nПример: \"Величественный лев в саванне на закате, реалистичный стиль фотографии, золотой час\"",
        "es": "🖼️ **Generación de Imagen**\n\nDescribe la imagen que quieres crear.\n\n💡 Consejos:\n• Sé específico y detallado\n• Incluye el estilo (realista, caricatura, etc.)\n• Menciona colores, iluminación, ambiente\n\nEjemplo: \"Un león majestuoso en una sabana al atardecer, estilo fotografía realista, luz dorada\"",
    },
    "video_prompt_request": {
        "en": "🎬 **Video Generation**\n\nDescribe the video you want to create.\n\n💡 Tips:\n• Describe the scene and action\n• Keep it simple (5-8 second videos)\n• Include camera movement if desired\n\nExample: \"A butterfly landing on a flower in slow motion, macro shot, soft focus background\"",
        "ru": "🎬 **Генерация видео**\n\nОпишите видео, которое хотите создать.\n\n💡 Советы:\n• Опишите сцену и действие\n• Будьте проще (видео 5-8 секунд)\n• Укажите движение камеры при желании\n\nПример: \"Бабочка садится на цветок в замедленной съемке, макросъемка, размытый фон\"",
        "es": "🎬 **Generación de Video**\n\nDescribe el video que quieres crear.\n\n💡 Consejos:\n• Describe la escena y la acción\n• Mantenlo simple (videos de 5-8 segundos)\n• Incluye movimiento de cámara si lo deseas\n\nEjemplo: \"Una mariposa aterrizando en una flor en cámara lenta, toma macro, fondo desenfocado\"",
    },
    "generation_cancelled": {
        "en": "❌ Generation cancelled.",
        "ru": "❌ Генерация отменена.",
        "es": "❌ Generación cancelada.",
    },
    "generating_image": {
        "en": "🎨 Generating your image... This may take a moment.",
        "ru": "🎨 Создаю ваше изображение... Это может занять некоторое время.",
        "es": "🎨 Generando tu imagen... Esto puede tomar un momento.",
    },
    "generating_video": {
        "en": "🎬 Generating your video... This may take a few minutes.",
        "ru": "🎬 Создаю ваше видео... Это может занять несколько минут.",
        "es": "🎬 Generando tu video... Esto puede tomar unos minutos.",
    },
    "image_generated": {
        "en": "Image generated successfully!",
        "ru": "Изображение успешно создано!",
        "es": "¡Imagen generada exitosamente!",
    },
    "video_generated": {
        "en": "Video generated successfully!",
        "ru": "Видео успешно создано!",
        "es": "¡Video generado exitosamente!",
    },
    "image_generation_failed": {
        "en": "❌ Failed to generate image. Please try again with a different prompt.",
        "ru": "❌ Не удалось создать изображение. Попробуйте другой запрос.",
        "es": "❌ Error al generar imagen. Por favor intenta con otra descripción.",
    },
    "video_generation_failed": {
        "en": "❌ Failed to generate video. Please try again with a different prompt.",
        "ru": "❌ Не удалось создать видео. Попробуйте другой запрос.",
        "es": "❌ Error al generar video. Por favor intenta con otra descripción.",
    },
}


def get_text(key: str, language: str = "en", **kwargs) -> str:
    """
    Get translated text for a key.
    
    Args:
        key: Translation key
        language: Language code
        **kwargs: Format arguments
    
    Returns:
        Translated string
    """
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(language, translations.get("en", f"[{key}]"))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text

