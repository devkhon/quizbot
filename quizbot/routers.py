from aiogram import Dispatcher, F, Router
from aiogram.enums import ChatType
from aiogram.filters import ChatMemberUpdatedFilter, Command, CommandStart, StateFilter
from constants import PROMOTED
from handlers import (
    cancel_quiz,
    confirm_quiz,
    handle_bot_join,
    handle_bot_leave,
    handle_confirm,
    handle_enter_quiz_count,
    handle_enter_time,
    handle_explanation,
    handle_option_input,
    handle_question_input,
    handle_select_action,
    handle_select_channel,
    handle_start_command,
    handle_user_demote,
    handle_user_promote,
    select_channel,
    select_correct_option,
    start_quiz_creation,
    start_settings,
)
from helpers import ChatTypeFilter
from messages import Btn
from type import QuizForm, SettingsForm

user_router = Router()
user_router.message.filter(ChatTypeFilter(ChatType.PRIVATE))

channel_router = Router()
channel_router.message.filter(ChatTypeFilter(ChatType.CHANNEL))


dp = Dispatcher()
dp.include_routers(user_router, channel_router)

quiz_state_filter = StateFilter(*QuizForm.__all_states__)

user_router.message.register(handle_start_command, CommandStart())
user_router.message.register(start_quiz_creation, Command("addquiz"))
user_router.message.register(cancel_quiz, quiz_state_filter, F.text == Btn.CANCEL)
user_router.message.register(select_channel, QuizForm.select_channel)
user_router.message.register(handle_question_input, QuizForm.question)
user_router.message.register(handle_option_input, QuizForm.collect_options)
user_router.message.register(select_correct_option, QuizForm.correct_option)
user_router.message.register(handle_explanation, QuizForm.explanation)
user_router.message.register(confirm_quiz, QuizForm.confirmation)
user_router.message.register(start_settings, Command("settings"))
user_router.message.register(handle_select_channel, SettingsForm.select_channel)
user_router.message.register(handle_select_action, SettingsForm.sleect_action)
user_router.message.register(handle_enter_time, SettingsForm.enter_time)
user_router.message.register(handle_enter_quiz_count, SettingsForm.enter_quiz_count)
user_router.message.register(handle_confirm, SettingsForm.confirm)

channel_router.my_chat_member.register(
    handle_bot_join, ChatMemberUpdatedFilter(PROMOTED)
)
channel_router.my_chat_member.register(
    handle_bot_leave, ChatMemberUpdatedFilter(~PROMOTED)
)
channel_router.chat_member.register(
    handle_user_promote, ChatMemberUpdatedFilter(PROMOTED)
)
channel_router.chat_member.register(
    handle_user_demote, ChatMemberUpdatedFilter(~PROMOTED)
)
