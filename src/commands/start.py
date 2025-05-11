from aiogram.types import Message
from aiogram.filters import Command
from aiogram.dispatcher.router import Router

router = Router()

@router.message(Command("start_zhata"))
async def cmd_start(message: Message):
    await message.answer("салам шошкалар")

def register_start_handlers(dp):
    dp.include_router(router)