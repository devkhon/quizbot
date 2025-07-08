from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from db import AsyncSessionLocal, redis
from helpers import create_keyboard, get_user_channels
from messages import Btn, Msg
from type import ChannelSettings, SettingsConfirmType, SettingsData, SettingsForm

router = Router()


async def start_settings(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        channels = await get_user_channels(session, message.from_user)

    if not channels:
        await message.answer(Msg.NO_CHANNELS, parse_mode=ParseMode.MARKDOWN_V2)
        return

    titles = [ch.title for ch in channels]
    await state.set_state(SettingsForm.select_channel)
    data = SettingsData(
        channels=channels,
        channel=None,
        pending_time=None,
        pending_quiz_count=None,
        confirm_type=None,
    )
    await state.set_data(data)
    keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
    await message.answer(
        Msg.PROMPT_CHANNEL, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def handle_select_channel(message: Message, state: FSMContext) -> None:
    data: SettingsData = await state.get_data()
    titles = [ch.title for ch in data["channels"]]

    if message.text not in titles:
        await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)
        return

    channel = data["channels"][titles.index(message.text)]
    await state.update_data(channel=channel)
    await state.set_state(SettingsForm.sleect_action)
    keyboard = create_keyboard(
        ([Btn.TIME, Btn.QUIZZES], 2), ([Btn.BACK, Btn.CANCEL], 2)
    )
    await message.answer(
        Msg.PROMPT_SETTINGS_ACTION,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def handle_select_action(message: Message, state: FSMContext) -> None:
    if message.text == Btn.BACK:
        data: SettingsData = await state.get_data()
        titles = [ch.title for ch in data["channels"]]
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await state.set_state(SettingsForm.select_channel)
        await message.answer(
            Msg.PROMPT_CHANNEL, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if message.text == Btn.TIME:
        await state.set_state(SettingsForm.enter_time)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.ENTER_TIME, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if message.text == Btn.QUIZZES:
        await state.set_state(SettingsForm.enter_quiz_count)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.ENTER_QUIZ_COUNT,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)


async def handle_enter_time(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(SettingsForm.sleect_action)
        keyboard = create_keyboard(
            ([Btn.TIME, Btn.QUIZZES], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.PROMPT_SETTINGS_ACTION,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    try:
        dt = datetime.strptime(message.text, "%H:%M")
        normalized = dt.strftime("%H:%M")
        await state.update_data(
            pending_time=normalized, confirm_type=SettingsConfirmType.TIME
        )
        await state.set_state(SettingsForm.confirm)
        keyboard = create_keyboard(
            ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.CONFIRM_TIME.format(time=normalized),
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except ValueError:
        await message.answer(Msg.INVALID_TIME_FORMAT, parse_mode=ParseMode.MARKDOWN_V2)


async def handle_enter_quiz_count(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(SettingsForm.sleect_action)
        keyboard = create_keyboard(
            ([Btn.TIME, Btn.QUIZZES], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.PROMPT_SETTINGS_ACTION,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text.isdigit() and int(message.text) > 0:
        await state.update_data(
            pending_quiz_count=int(message.text),
            confirm_type=SettingsConfirmType.QUIZZES,
        )
        await state.set_state(SettingsForm.confirm)
        keyboard = create_keyboard(
            ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.CONFIRM_QUIZ_COUNT.format(count=message.text),
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await message.answer(Msg.INVALID_QUIZ_COUNT, parse_mode=ParseMode.MARKDOWN_V2)


async def handle_confirm(message: Message, state: FSMContext) -> None:
    data: SettingsData = await state.get_data()

    if message.text == Btn.BACK:
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        if data["confirm_type"] == SettingsConfirmType.TIME:
            await state.set_state(SettingsForm.enter_time)
            await message.answer(
                Msg.REENTER_TIME,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return

        await state.set_state(SettingsForm.enter_quiz_count)
        await message.answer(
            Msg.REENTER_QUIZ_COUNT,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text == Btn.REJECT:
        await state.clear()
        await message.answer(
            Msg.REJECTED_SETTINGS,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text == Btn.APPROVE:
        settings: ChannelSettings = {}
        if data["pending_time"]:
            settings["time"] = data["pending_time"]
        if data["pending_quiz_count"]:
            settings["quiz_count"] = str(data["pending_quiz_count"])

        await redis.hset(data["channel"].id, mapping=settings)
        await state.clear()
        await message.answer(
            Msg.SAVED_SETTINGS,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)


async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        Msg.CANCELED,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


settings_state_filter = StateFilter(*SettingsForm.__all_states__)

router.message.register(start_settings, Command("settings"))
router.message.register(cancel, settings_state_filter, F.text == Btn.CANCEL)
router.message.register(handle_select_channel, SettingsForm.select_channel)
router.message.register(handle_select_action, SettingsForm.sleect_action)
router.message.register(handle_enter_time, SettingsForm.enter_time)
router.message.register(handle_enter_quiz_count, SettingsForm.enter_quiz_count)
router.message.register(handle_confirm, SettingsForm.confirm)
