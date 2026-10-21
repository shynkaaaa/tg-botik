import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config.config import Config
from commands.start import register_start_handlers
from commands.schedule import register_schedule_handlers
from commands.faceit import register_faceit_handlers
from middlewares.antispam_middleware import AntiSpamMiddleware
from middlewares.checkowner_middleware import CheckOwnerMiddleware

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    )
)

dp = Dispatcher()


async def discard_pending_updates(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start_zhata", description="Приветствие"),
        BotCommand(command="schedule", description="Расписание метро"),
        BotCommand(command="faceit_me", description="Моя статистика FACEIT"),
        BotCommand(command="faceit_top", description="Топ FACEIT по Elo"),
    ])


dp.startup.register(discard_pending_updates)
dp.startup.register(set_bot_commands)
dp.message.middleware(AntiSpamMiddleware())
dp.callback_query.middleware(CheckOwnerMiddleware())
dp.callback_query.middleware(AntiSpamMiddleware())

register_start_handlers(dp)
register_schedule_handlers(dp)
register_faceit_handlers(dp)

if __name__ == '__main__':
    dp.run_polling(bot)
