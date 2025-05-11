import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union

# Настройки антиспама
COOLDOWN_SECONDS = 10  # Время между действиями

# Временные метки пользователей
user_timestamps: Dict[int, float] = {}

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

        last_time = user_timestamps.get(user_id)
        if last_time and now - last_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            # Ответ зависит от типа события
            if isinstance(event, Message):
                await event.answer(f"Лее куда лезешь. Падажди еще {remaining} секунд хохлина тупая.")
            elif isinstance(event, CallbackQuery):
                await event.answer(f"Лее куда лезешь. Падажди еще {remaining} секунд хохлина тупая.", show_alert=True)
            return  # Блокируем

        # Обновляем время
        user_timestamps[user_id] = now
        return await handler(event, data)
