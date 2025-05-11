from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from typing import Callable, Awaitable, Dict, Any

class CheckOwnerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        cb_data = event.data
        user_id = event.from_user.id

        # Ожидаем формат: "action:owner_id"
        if ":" in cb_data:
            action, owner_id_str = cb_data.split(":", 1)
            try:
                owner_id = int(owner_id_str)
                if owner_id != user_id:
                    await event.answer("Это не твоя кнопка ДУРА!", show_alert=True)
                    return  # Блокируем
            except ValueError:
                pass  # fallback — невалидный формат, пропускаем
        return await handler(event, data)
