import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from bot import bot
from constants import ChangeType
from db import AsyncSessionLocal
from helpers import (
    add_channel_admins,
    add_quiz,
    create_keyboard,
    delete_channel_admins,
    detect_bot_change,
    detect_user_change,
    get_user_channels,
    upsert_channel,
    upsert_user,
)
from messages import Btn, Msg
from type import QuizData, QuizForm


async def handle_bot_status_change(update: types.ChatMemberUpdated) -> None:
    change_type = detect_bot_change(update)

    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, update.chat)
        if change_type == ChangeType.BECAME_ADMIN:
            await asyncio.sleep(1)
            admins = await bot.get_chat_administrators(channel.id)
            admin_users = [admin.user for admin in admins]
            await add_channel_admins(session, channel.id, admin_users)
        elif change_type == ChangeType.LEFT_ADMIN:
            await delete_channel_admins(session, channel.id)

        await session.commit()


async def handle_user_status_change(update: types.ChatMemberUpdated) -> None:
    change_type = detect_user_change(update)
    user = update.new_chat_member.user

    if change_type is None:
        return

    async with AsyncSessionLocal() as session:
        if change_type == ChangeType.BECAME_ADMIN:
            await add_channel_admins(session, update.chat.id, [user])
        elif change_type == ChangeType.LEFT_ADMIN:
            await delete_channel_admins(session, update.chat.id, [user.id])

        await session.commit()


async def handle_start_command(message: types.Message) -> None:
    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer(Msg.START)


async def handle_addquiz_command(message: types.Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        channels = await get_user_channels(session, message.from_user)
        if not channels:
            await message.answer(Msg.NO_CHANNELS)
            return

        await state.set_state(QuizForm.channel)
        titles = [ch.title for ch in channels]
        await state.set_data({"channels": channels, "titles": titles})
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await message.answer(Msg.PROMPT_CHANNEL, reply_markup=keyboard)


async def select_channel(message: types.Message, state: FSMContext) -> None:
    data: QuizData = await state.get_data()
    if message.text not in data["titles"]:
        await message.answer(Msg.INVALID_RESPONSE)
        return

    await state.set_state(QuizForm.question)
    channel = data["channels"][data["titles"].index(message.text)]
    await state.update_data(channel=channel)
    keyboard = create_keyboard(([Btn.GO_BACK, Btn.CANCEL], 2))
    await message.answer(Msg.PROMPT_QUESTION, reply_markup=keyboard)


async def handle_question_input(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.GO_BACK:
        await state.set_state(QuizForm.channel)
        data: QuizData = await state.get_data()
        keyboard = create_keyboard((data["titles"], 2), ([Btn.CANCEL], 1))
        await message.answer(Msg.PROMPT_CHANNEL, reply_markup=keyboard)
        return

    if len(message.text) > 300:
        await message.answer(Msg.QUESTION_TOO_LONG)
        return

    await state.set_state(QuizForm.options)
    await state.update_data(question=message.text, options=[])
    keyboard = create_keyboard(([Btn.GO_BACK, Btn.CANCEL], 2))
    await message.answer(Msg.PROMPT_OPTION, reply_markup=keyboard)


async def handle_option_input(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.GO_BACK:
        await state.set_state(QuizForm.question)
        keyboard = create_keyboard(([Btn.GO_BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_QUESTION, reply_markup=keyboard)
        return

    data: QuizData = await state.get_data()

    if message.text == Btn.FINISH:
        if len(data["options"]) < 2:
            await message.answer(Msg.NEED_TWO_OPTIONS)
            return

        await state.set_state(QuizForm.correct)
        keyboard = create_keyboard((data["options"], 2), ([Btn.GO_BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_SELECT_CORRECT, reply_markup=keyboard)
        return

    if len(message.text) > 100:
        await message.answer(Msg.OPTION_TOO_LONG)
        return

    if len(data["options"]) >= 10:
        await message.answer(Msg.MAX_OPTIONS_REACHED)
        return

    data["options"].append(message.text)
    await state.update_data(options=data["options"])
    keyboard = create_keyboard(
        ([Btn.FINISH] if len(data["options"]) >= 2 else [], 1),
        ([Btn.GO_BACK, Btn.CANCEL], 2),
    )
    await message.answer(
        Msg.OPTION_ADDED.format(finish_btn=Btn.FINISH), reply_markup=keyboard
    )


async def select_correct_option(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.GO_BACK:
        await state.set_state(QuizForm.options)
        keyboard = create_keyboard(([Btn.GO_BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_OPTION, reply_markup=keyboard)
        return

    data: QuizData = await state.get_data()

    if message.text not in data["options"]:
        await message.answer(Msg.INVALID_RESPONSE)
        return

    await state.set_state(QuizForm.confirmation)
    data["correct"] = data["options"].index(message.text)
    await state.update_data(correct=data["correct"])

    keyboard = create_keyboard(
        ([Btn.APPROVE, Btn.DISAPPROVE], 2), ([Btn.GO_BACK, Btn.CANCEL], 2)
    )
    await message.answer(
        Msg.PREVIEW.format(
            channel=data["channel"].title,
            question=data["question"],
            options="\n".join(
                [f"\t{i + 1}. {opt}" for i, opt in enumerate(data["options"])]
            ),
            correct=data["options"][data["correct"]],
        ),
        reply_markup=keyboard,
    )


async def confirm_quiz(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    data: QuizData = await state.get_data()

    if message.text == Btn.GO_BACK:
        await state.set_state(QuizForm.correct)
        keyboard = create_keyboard((data["options"], 2), ([Btn.GO_BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_SELECT_CORRECT, reply_markup=keyboard)
        return

    if message.text == Btn.DISAPPROVE:
        await state.clear()
        await message.answer(
            Msg.CANCELED.format(status="disapproves"),
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if message.text == Btn.APPROVE:
        async with AsyncSessionLocal() as session:
            await add_quiz(session, data)
            await session.commit()
        await state.clear()
        await message.answer(Msg.SAVED, reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(Msg.INVALID_RESPONSE)


async def cancel(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        Msg.CANCELED.format(status="Canceled"), reply_markup=ReplyKeyboardRemove()
    )
