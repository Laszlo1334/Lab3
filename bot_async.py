import asyncio
import requests
import json

from types import SimpleNamespace
from telebot.async_telebot import AsyncTeleBot
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage


BOT_TOKEN = '6541593701:AAHXFzuUCewjsDzAVPRcbBapCNkOC6d8EeE'
state_storage = StateMemoryStorage()

bot = AsyncTeleBot(BOT_TOKEN, state_storage=state_storage)


class States(StatesGroup):
    validate = State()
    send_feedback = State()


class FeedbackRequest:
    def __init__(self, telegramToken, feedbackText, telegramUsername):
        self.telegramToken = telegramToken
        self.feedbackText = feedbackText
        self.telegramUsername = telegramUsername


@bot.message_handler(commands=['help', 'start'])
async def start(message):
    text = ("Hi! You're using Hotel Booking Feedback Bot!"
            "Enter your Telegram Token, so that we can be sure you are an acutal user of our service.")

    await bot.set_state(message.from_user.id, States.validate, message.chat.id)
    await bot.reply_to(message, text)


@bot.message_handler(state=States.validate)
async def validate_step(message):
    if not await is_telegram_token(message.text):
        await bot.reply_to(message, "It doesn't look like a Telegram Token... Try again!")
        return

    await bot.reply_to(message, "Checking your token...")
    if not await is_valid_telegram_token(message.text):
        await bot.reply_to(message, "Invalid token! Try again!")
        return
    await bot.reply_to(message, "Your token has been validated")

    await bot.set_state(message.from_user.id, States.send_feedback, message.chat.id)
    with await bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['telegramToken'] = message.text


@bot.message_handler(state=States.send_feedback)
async def send_feedback_step(message):
    if not message.text:
        await bot.reply_to(message, "Your feedback is empty! Try again!")
        return

    await bot.reply_to(message, "Sending your feedback...")
    if not await send_feedback(
        FeedbackRequest(
            telegramToken=data['telegramToken'],
            feedbackText=message.text,
            telegramUsername=bot.get_chat_member(message.chat.id, message.from_user.id).user.username
        )
    ):
        await bot.reply_to(message, "Something went wrong :(")
        return
    await bot.reply_to(message, "Your feedback is saved! Thank you!")

    await bot.delete_state(message.from_user.id, message.chat.id)


async def is_telegram_token(str):
    return len(str) == 6 and isupper(str) and isalpha(str)


async def base_url(path: str):
    return 'http://localhost:8080/' + path;


async def is_valid_telegram_token(token: str):
    url = base_url('auth_telegram')
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "telegramToken": message.text
    }

    response = await requests.post(url, headers=headers, json=body)
    x = await json.loads(await response.json(), object_hook=lambda l: SimpleNamespace(**l))

    return x.success


async def send_feedback(feedback):
    url = base_url('save_feedback')
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "telegramToken": feedback.telegramToken,
        "feedbackText": feedback.feedbackText,
        "telegramUsername": feedback.telegramUsername
    }

    response = await requests.post(url, headers=headers, json=body)
    x = await json.loads(await response.json(), object_hook=lambda l: SimpleNamespace(**l))

    return x.saved


asyncio.run(bot.polling())