from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from handlers import (
    cancel,
    confirm_quiz,
    handle_addquiz_command,
    handle_bot_status_change,
    handle_option_input,
    handle_question_input,
    handle_start_command,
    handle_user_status_change,
    select_channel,
    select_correct_option,
)
from messages import Btn
from type import QuizForm

dp = Dispatcher()

quiz_state_filter = StateFilter(*QuizForm.__all_states__)

dp.message.register(handle_start_command, CommandStart())
dp.message.register(handle_addquiz_command, Command("addquiz"))
dp.message.register(cancel, quiz_state_filter, F.text == Btn.CANCEL)
dp.message.register(select_channel, QuizForm.channel)
dp.message.register(handle_question_input, QuizForm.question)
dp.message.register(handle_option_input, QuizForm.options)
dp.message.register(select_correct_option, QuizForm.correct)
dp.message.register(confirm_quiz, QuizForm.confirmation)
dp.my_chat_member.register(handle_bot_status_change)
dp.chat_member.register(handle_user_status_change)
