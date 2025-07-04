from datetime import datetime

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from db import AsyncSessionLocal
from helpers import create_keyboard, get_user_channels
from messages import Btn, Msg
from type import SettingsForm

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
    await state.set_data({"channels": channels})
    keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
    await message.answer(
        Msg.PROMPT_CHANNEL, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def handle_select_channel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    titles = [ch.title for ch in data["channels"]]

    if message.text == Btn.CANCEL:
        await state.clear()
        await message.answer(
            Msg.CANCELED,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text not in titles:
        await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)
        return

    selected = data["channels"][titles.index(message.text)]
    await state.update_data(channel=selected)
    await state.set_state(SettingsForm.sleect_action)
    keyboard = create_keyboard(
        ([Btn.TIME, Btn.QUIZZES], 2), ([Btn.BACK, Btn.CANCEL], 2)
    )
    await message.answer(Msg.PROMPT_SETTINGS_ACTION, reply_markup=keyboard)


async def handle_select_action(message: Message, state: FSMContext) -> None:
    if message.text == Btn.CANCEL:
        await state.clear()
        await message.answer(Msg.CANCELED, reply_markup=ReplyKeyboardRemove())
        return

    if message.text == Btn.BACK:
        data = await state.get_data()
        titles = [ch.title for ch in data["channels"]]
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await state.set_state(SettingsForm.select_channel)
        await message.answer(Msg.PROMPT_CHANNEL, reply_markup=keyboard)
        return

    if message.text == Btn.TIME:
        await state.set_state(SettingsForm.enter_time)
        await message.answer(Msg.ENTER_TIME)
    elif message.text == Btn.QUIZZES:
        await state.set_data(SettingsForm.enter_quiz_count)
        await message.answer(Msg.ENTER_QUIZ_COUNT)
    else:
        await message.answer(Msg.INVALID_RESPONSE)


async def handle_enter_time(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(penting_time=message.text, confirm_type="time")
        await state.set_state(SettingsForm.confirm)
        keyboard = create_keyboard(
            ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.CONFIRM_TIME.format(time=message.text), reply_markup=keyboard
        )
    except ValueError:
        await message.answer(Msg.INVALID_TIME_FORMAT)


async def handle_enter_quiz_count(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text.isdigit() and int(message.text) > 0:
        await state.update_data(
            pending_quiz_count=int(message.text), confirm_type="quizzes"
        )
        await state.set_state(SettingsForm.confirm)
        keyboard = create_keyboard(
            ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
        )
        await message.answer(
            Msg.CONFIRM_QUIZ_COUNT.format(count=message.text), reply_markup=keyboard
        )
    else:
        await message.answer(Msg.INVALID_QUIZ_COUNT)


async def handle_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    if message.text == Btn.CANCEL:
        await state.clear()
        await message.answer(Msg.CANCELED, reply_markup=ReplyKeyboardRemove())
        return

    if message.text == Btn.BACK:
        if data["confirm_type"] == "time":
            await state.set_state(SettingsForm.enter_time)
            await message.answer(Msg.REENTER_TIME)
        else:
            await state.set_state(SettingsForm.enter_quiz_count)
            await message.answer(Msg.REENTER_QUIZ_COUNT)
        return

    if message.text == Btn.REJECT:
        await state.clear()
        await message.answer(Msg.REJECTED_SETTINGS, reply_markup=ReplyKeyboardRemove())
        return

    if message.text == Btn.APPROVE:
        # Save db logic
        await state.clear()
        await message.answer(Msg.SAVED_SETTINGS, reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(Msg.INVALID_RESPONSE)


router.message.register(start_settings, Command("settings"))
router.message.register(handle_select_channel, SettingsForm.select_channel)
router.message.register(handle_select_action, SettingsForm.sleect_action)
router.message.register(handle_enter_time, SettingsForm.enter_time)
router.message.register(handle_enter_quiz_count, SettingsForm.enter_quiz_count)
router.message.register(handle_confirm, SettingsForm.confirm)
