import telebot
import requests
import json

from types import SimpleNamespace
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage


BOT_TOKEN = '6541593701:AAHXFzuUCewjsDzAVPRcbBapCNkOC6d8EeE'
state_storage = StateMemoryStorage()

bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)


class States(StatesGroup):
    validate = State()
    send_feedback = State()


class FeedbackRequest:
    def __init__(self, telegramToken, feedbackText, telegramUsername):
        self.telegramToken = telegramToken
        self.feedbackText = feedbackText
        self.telegramUsername = telegramUsername


@bot.message_handler(commands=['help', 'start'])
def start(message):
    text = ("Hi! You're using Hotel Booking Feedback Bot!"
            "Enter your Telegram Token, so that we can be sure you are an acutal user of our service.")

    bot.set_state(message.from_user.id, States.validate, message.chat.id)
    bot.reply_to(message, text)


@bot.message_handler(state=States.validate)
def validate_step(message):
    if not is_telegram_token(message.text):
        bot.reply_to(message, "It doesn't look like a Telegram Token... Try again!")
        return

    bot.reply_to(message, "Checking your token...")
    if not is_valid_telegram_token(message.text):
        bot.reply_to(message, "Invalid token! Try again!")
        return
    bot.reply_to(message, "Your token has been validated")

    bot.set_state(message.from_user.id, States.send_feedback, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['telegramToken'] = message.text


@bot.message_handler(state=States.send_feedback)
def send_feedback_step(message):
    if not message.text:
        bot.reply_to(message, "Your feedback is empty! Try again!")
        return

    bot.reply_to(message, "Sending your feedback...")
    if not send_feedback(
        FeedbackRequest(
            telegramToken=data['telegramToken'],
            feedbackText=message.text,
            telegramUsername=bot.get_chat_member(message.chat.id, message.from_user.id).user.username
        )
    ):
        bot.reply_to(message, "Something went wrong :(")
        return
    bot.reply_to(message, "Your feedback is saved! Thank you!")

    bot.delete_state(message.from_user.id, message.chat.id)


def is_telegram_token(str):
    return len(str) == 6 and isupper(str) and isalpha(str)


def base_url(path: str):
    return 'http://localhost:8080/' + path;


def is_valid_telegram_token(token: str):
    url = base_url('auth_telegram')
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "telegramToken": message.text
    }

    response = requests.post(url, headers=headers, json=body)
    x = json.loads(response.json(), object_hook=lambda l: SimpleNamespace(**l))

    return x.success


def send_feedback(feedback):
    url = base_url('save_feedback')
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body = {
        "telegramToken": feedback.telegramToken,
        "feedbackText": feedback.feedbackText,
        "telegramUsername": feedback.telegramUsername
    }

    response = requests.post(url, headers=headers, json=body)
    x = json.loads(response.json(), object_hook=lambda l: SimpleNamespace(**l))

    return x.saved


bot.infinity_polling()