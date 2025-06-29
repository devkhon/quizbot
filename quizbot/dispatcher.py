from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from handlers import (
    bot_status_change,
    cancel,
    command_addquiz,
    command_start,
    confirm_quiz,
    enter_options,
    enter_question,
    select_channel,
    select_correct_option,
    user_status_change,
)
from type import QuizForm

dp = Dispatcher()

quiz_state_filter = StateFilter(*QuizForm.__all_states__)

dp.message.register(command_start, CommandStart())
dp.message.register(command_addquiz, Command("addquiz"))
dp.message.register(cancel, quiz_state_filter, F.text.casefold() == "cancel")
dp.message.register(select_channel, QuizForm.channel)
dp.message.register(enter_question, QuizForm.question)
dp.message.register(enter_options, QuizForm.options)
dp.message.register(select_correct_option, QuizForm.correct)
dp.message.register(confirm_quiz, QuizForm.confirm)
dp.my_chat_member.register(bot_status_change)
dp.chat_member.register(user_status_change)
