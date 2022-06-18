import logging
import os
import sys
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ContentType
from aiogram.utils.callback_data import CallbackData
from dotenv import load_dotenv
from aiogram.contrib.fsm_storage.memory import MemoryStorage


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
#ENDPOINT = os.getenv('ENDPOINT')
ENDPOINT = 'https://aztro.sameerkumar.website/'
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

AVAILABLE_COMMANDS = (
    '/start',
    '/horoscope',
    '/share',
    '/help',
    '/share@horoscopes_robot',
    '/horoscope@horoscopes_robot',
    '/help@horoscopes_robot',
    '/start@horoscopes_robot')
HELP_TEXT = (
    "/start — send me this command to get basic info about how i work\n"
    "/help — send this command to get list of available commands\n"
    "/horoscope — send this command to get horoscope\n"
    "/share — i'll send u link to share me with friends\n"
)
ZODIACS = (
    'Aries ♈', 'Taurus ♉', 'Gemini ♊', 'Cancer ♋',
    'Leo ♌', 'Virgo ♍', 'Libra ♎', 'Scorpio ♏',
    'Sagittarius ♐', 'Capricorn ♑', 'Aquarius ♒', 'Pisces ♓'
)
DAYS = ('Horoscope for today', 'Horoscope for tomorrow')


# Class for holding users data
class UserData(StatesGroup):
    chosen_zodiac = State()
    chosen_day = State()


def get_sign_keyboard():
    """Creating keyboard for choosing zodiac sign."""
    zodiac_keyboard = ReplyKeyboardMarkup(selective=True)
    zodiac_keyboard.add(
        KeyboardButton(text='Aries ♈', ),
        KeyboardButton(text='Taurus ♉', ),
        KeyboardButton(text='Gemini ♊', ),
        KeyboardButton(text='Cancer ♋', ),
        KeyboardButton(text='Leo ♌', ),
        KeyboardButton(text='Virgo ♍', ),
        KeyboardButton(text='Libra ♎', ),
        KeyboardButton(text='Scorpio ♏', ),
        KeyboardButton(text='Sagittarius ♐', ),
        KeyboardButton(text='Capricorn ♑', ),
        KeyboardButton(text='Aquarius ♒', ),
        KeyboardButton(text='Pisces ♓', ),
    )
    return zodiac_keyboard


def get_day_keyboard():
    """Creating keyboard for choosing day."""
    day_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    day_keyboard.add(
        KeyboardButton(text='Horoscope for today', ),
        KeyboardButton(text='Horoscope for tomorrow', ),
    )
    return day_keyboard


@dp.message_handler(
    lambda message: message.text not in AVAILABLE_COMMANDS,
    content_types=ContentType.ANY
)
async def reply_unknown_command(message: types.Message):
    """
    This handler will be called when user sends unknown command or
    unknown type of content.
    """
    await message.reply(
        "Sorry, i don't know what to answer 😥"
        "Please, choose command from this list:\n" + HELP_TEXT
    )


@dp.message_handler(commands='start', )
async def reply_start_msg(message: types.Message):
    """This handler will be called when user sends `/start` command."""
    await message.reply(
        f"Hello, <b>{message.from_user.full_name}</b>! I'm Horoscope Bot!\n"
        f"To get info about my abilities and available commands just "
        f"send me /help command. Or...\n"
        f"Let's look for some /horoscope!",
        parse_mode=types.ParseMode.HTML,
    )


@dp.message_handler(commands='share', )
async def reply_share_msg(message: types.Message):
    """This handler will be called when user sends `/share` command."""
    share_btn = InlineKeyboardMarkup()
    share_btn.add(InlineKeyboardButton(
        text='Horoscope Bot',
        switch_inline_query="Check this bot!")
    )
    await message.reply(text='Sharing link below ⬇', reply_markup=share_btn, )


@dp.message_handler(commands='help', )
async def reply_help_msg(message: types.Message):
    """This handler will be called when user sends `/help` command."""
    await message.reply(
        f"<b>{message.from_user.full_name}</b>! I'm Horoscope Bot!\n"
        f"Check my commands list: \n" + HELP_TEXT,
        # f"Also you can add me to your channels and get actual horoscope "
        # f"information in any chat! \n"
        parse_mode=types.ParseMode.HTML
    )


@dp.message_handler(commands='horoscope', )
async def reply_horoscope_msg(message: types.Message, ):
    """This handler will be called when user sends `/horoscope` command."""
    await message.reply(
        f"<b>{message.from_user.full_name}</b>! Choose your sign:",
        reply_markup=get_sign_keyboard(),
        parse_mode=types.ParseMode.HTML,
    )
    await UserData.chosen_zodiac.set()


@dp.message_handler(state=UserData.chosen_zodiac, content_types=ContentType.ANY)
async def choose_zodiac(message: types.Message, state: FSMContext):
    """This handler will be called when user press zodiac btn"""
    if message.text not in ZODIACS or message.content_type != ContentType.TEXT:
        await message.reply(
            f"<b>{message.from_user.full_name}</b>! Please, choose your sign from keyboard below:",
            reply_markup=get_sign_keyboard(),
            parse_mode=types.ParseMode.HTML,
        )
        return
    await state.update_data(chosen_zodiac=message.text)
    await UserData.chosen_day.set()
    await message.reply(
        text='<b>Choose one of the options:</b>',
        reply_markup=get_day_keyboard(),
        parse_mode=types.ParseMode.HTML
    )


@dp.message_handler(state=UserData.chosen_day, content_types=ContentType.ANY)
async def get_full_parse_data(message: types.Message, state: FSMContext):
    """This handler will be called when user press day btn."""
    if message.text not in DAYS or message.content_type != ContentType.TEXT:
        await message.reply(
            f"<b>{message.from_user.full_name}</b>! Please, choose day from keyboard below:",
            reply_markup=get_day_keyboard(),
            parse_mode=types.ParseMode.HTML,
        )
        return
    await state.update_data(chosen_day=message.text[14:])
    data = await state.get_data()
    user_params = (
            ('sign', data['chosen_zodiac'].lower()[0:-2]),
            ('day', data['chosen_day']),
        )
    try:
        response = requests.post(ENDPOINT, params=user_params)
        horoscope_data = response.json()
        await message.reply(
            f'<b>{data["chosen_zodiac"]} for {horoscope_data.get("current_date")}: \n</b>'
            f'<b>Horoscope</b> — {horoscope_data.get("description")} \n'
            f'<b>Compatibility</b> — {horoscope_data.get("compatibility")} \n'
            f'<b>Mood</b> — {horoscope_data.get("mood")} \n'
            f'<b>Color</b> — {horoscope_data.get("color")} \n'
            f'<b>Lucky number</b> — {horoscope_data.get("lucky_number")} \n'
            f'<b>Lucky time</b> — {horoscope_data.get("lucky_time")} \n\n'
            f'I want one more /horoscope!',
            parse_mode=types.ParseMode.HTML,
            reply_markup=types.ReplyKeyboardRemove()
        )
    except ConnectionError as error:
        logging.error('Endpoint is unreachable')
        await message.reply(
            "I'm sorry, my friend! My magic crystal ball is broken 🥺 "
            "Let's try next time!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        if message.from_user.id != TELEGRAM_CHAT_ID:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text='Hey, Master! Horoscopes endpoint is unreachable 😣 '
                     'Assistance is required!'
            )
    await state.finish()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s, тип лога - %(levelname)s, функция - %(funcName)s, '
            'строка - %(lineno)d, сообщение - "%(message)s" || %(name)s'
        ),
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
        ],
    )
    executor.start_polling(dp, skip_updates=True)
