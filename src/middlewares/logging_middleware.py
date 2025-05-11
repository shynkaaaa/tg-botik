import logging

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        logging.info(f"User {event.from_user.id} sent a message: {event.text}")
        return await handler(event, data)