import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union

# Настройки антиспама
COOLDOWN_SECONDS = 10  # Время между действиями

# Временные метки пользователей
user_timestamps_message: Dict[int, float] = {}
user_timestamps_callback: Dict[int, float] = {}

class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        # Получаем ID пользователя
        user_id = event.from_user.id
        now = time.time()
        if isinstance(event, Message):
            last_time = user_timestamps_message.get(user_id) 
        elif isinstance(event, CallbackQuery):
            last_time = user_timestamps_callback.get(user_id) 
        if last_time and now - last_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            # Ответ зависит от типа события
            if isinstance(event, Message):
                await event.answer(f"Лее куда лезешь. Падажди еще {remaining} секунд хохлина тупая.")
            elif isinstance(event, CallbackQuery):
                await event.answer(f"Лее куда лезешь. Падажди еще {remaining} секунд хохлина тупая.", show_alert=True)
            return  # Блокируем

        # Обновляем время
        if isinstance(event, Message):
            user_timestamps_message[user_id] = now
        elif isinstance(event, CallbackQuery):
            user_timestamps_callback[user_id] = now
        return await handler(event, data)
