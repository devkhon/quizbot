from aiogram import Dispatcher, F, Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command, CommandStart, StateFilter
from handlers import (
    cancel,
    confirm_quiz,
    handle_addquiz_command,
    handle_bot_status_change,
    handle_explanation,
    handle_option_input,
    handle_question_input,
    handle_start_command,
    handle_user_status_change,
    select_channel,
    select_correct_option,
)
from helpers import ChatTypeFilter
from messages import Btn
from type import QuizForm

user_router = Router()
user_router.message.filter(ChatTypeFilter(ChatType.PRIVATE))

channel_router = Router()
channel_router.message.filter(ChatTypeFilter(ChatType.CHANNEL))


dp = Dispatcher()

dp.include_routers(user_router, channel_router)

quiz_state_filter = StateFilter(*QuizForm.__all_states__)

user_router.message.register(handle_start_command, CommandStart())
user_router.message.register(handle_addquiz_command, Command("addquiz"))
user_router.message.register(cancel, quiz_state_filter, F.text == Btn.CANCEL)
user_router.message.register(select_channel, QuizForm.select_channel)
user_router.message.register(handle_question_input, QuizForm.question)
user_router.message.register(handle_option_input, QuizForm.collect_options)
user_router.message.register(select_correct_option, QuizForm.correct_option)
user_router.message.register(handle_explanation, QuizForm.explanation)
user_router.message.register(confirm_quiz, QuizForm.confirmation)

channel_router.my_chat_member.register(handle_bot_status_change)
channel_router.chat_member.register(handle_user_status_change)
