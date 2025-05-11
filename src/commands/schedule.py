import time

from aiogram import types
from aiogram.filters import Command
from aiogram.dispatcher.router import Router

from config.keyboards import get_inline_keyboard
from utils.metro_parser import parse_schedule
router = Router()

@router.message(Command("schedule"))
async def cmd_schedule(message: types.Message):
    await message.answer(
        "Выберите станцию или общее расписание:",
        reply_markup=get_inline_keyboard(message.from_user.id)
    )

@router.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data.split(":")[0]
    schedule = parse_schedule()
    response = "Расписание метро:\n\n"

    if data.startswith("station_"): 
        id = int(data.split("_")[1])
        print(f"ID: {id}\n")
        response += f"🚉 Станция: {schedule[id]['station']}\n"
        response += f"⏱ Время прибытия (Райымбек батыра - Б.Момышулы): {schedule[id]['time_to']}\n"
        response += f"⏱ Время прибытия (Б.Момышулы - Райымбек батыра): {schedule[id]['time_from']}\n\n"

    elif data == "general_schedule":
        for entry in schedule:
            response += f"🚉 Станция: {entry['station']}\n"
            response += f"⏱ Время прибытия (Райымбек батыра - Б.Момышулы): {entry['time_to']}\n"
            response += f"⏱ Время прибытия (Б.Момышулы - Райымбек батыра): {entry['time_from']}\n\n"

    await callback.message.reply(response)
    await callback.answer()

def register_schedule_handlers(dp):
    dp.include_router(router)