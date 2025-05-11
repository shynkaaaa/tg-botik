import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.config import Config
from commands.start import register_start_handlers
from commands.schedule import register_schedule_handlers
from middlewares.antispam_middleware import AntiSpamMiddleware
from middlewares.checkowner_middleware import CheckOwnerMiddleware

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
dp.message.middleware(AntiSpamMiddleware())
dp.callback_query.middleware(AntiSpamMiddleware())
dp.callback_query.middleware(CheckOwnerMiddleware())

register_start_handlers(dp)
register_schedule_handlers(dp)

if __name__ == '__main__':
    dp.run_polling(bot)