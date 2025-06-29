import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from bot import bot
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
from type import ChangeType, QuizData, QuizForm


async def command_start(message: types.Message) -> None:
    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer("Hello World!")


async def bot_status_change(update: types.ChatMemberUpdated) -> None:
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


async def user_status_change(update: types.ChatMemberUpdated) -> None:
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


async def command_addquiz(message: types.Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        channels = await get_user_channels(session, message.from_user)
        titles = [ch.title for ch in channels]
        if not channels:
            await message.answer("You have no channels to add a quiz to.")
            return
        await state.set_data({"channels": channels, "titles": titles})
        await state.set_state(QuizForm.channel)
        keyboard = create_keyboard((titles, 2), (["cancel"], 1))
        await message.answer("Select a channel:", reply_markup=keyboard)


async def select_channel(message: types.Message, state: FSMContext) -> None:
    data: QuizData = await state.get_data()
    if message.text not in data["titles"]:
        await message.answer("Invalid channel. Please select again.")
        return

    channel = data["channels"][data["titles"].index(message.text)]
    keyboard = create_keyboard((["go back", "cancel"], 2))
    await state.set_state(QuizForm.question)
    await state.update_data(channel=channel)
    await message.answer("What is the quiz question?", reply_markup=keyboard)


async def enter_question(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text.lower() == "go back":
        data: QuizData = await state.get_data()
        keyboard = create_keyboard((data["titles"], 2), (["cancel"], 1))
        await state.set_state(QuizForm.channel)
        await message.answer("Select a channel:", reply_markup=keyboard)
        return

    if len(message.text) > 300:
        await message.answer("Questions must be 300 characters or shorter.")
        return

    keyboard = create_keyboard((["go back", "cancel"], 2))
    await state.update_data(question=message.text, options=[])
    await state.set_state(QuizForm.options)
    await message.answer("Send a quiz option: ", reply_markup=keyboard)


async def enter_options(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text.lower() == "go back":
        keyboard = create_keyboard((["go back", "cancel"], 2))
        await state.set_state(QuizForm.question)
        await message.answer("What is the quiz question?", reply_markup=keyboard)
        return

    data: QuizData = await state.get_data()

    if message.text.lower() == "finish adding options":
        if len(data["options"]) < 2:
            await message.answer("Please add at least two options before finishing.")
            return

        keyboard = create_keyboard((data["options"], 2), (["go back", "cancel"], 2))
        await state.set_state(QuizForm.correct)
        await message.answer("Select the correct option: ", reply_markup=keyboard)
        return

    if len(message.text) > 100:
        await message.answer("Options must be 100 characters or shorter.")
        return

    if len(data["options"]) >= 10:
        await message.answer("You can add at most 10 options.")
        return

    data["options"].append(message.text)
    keyboard = create_keyboard(
        (["finish adding options"] if len(data["options"]) >= 2 else [], 1),
        (["go back", "cancel"], 2),
    )
    await state.update_data(options=data["options"])
    await message.answer("Option added. Send another or stop: ", reply_markup=keyboard)


async def select_correct_option(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text.lower() == "go back":
        keyboard = create_keyboard((["go back", "cancel"], 2))
        await state.set_state(QuizForm.options)
        await message.answer("Send a quiz optons: ", reply_markup=keyboard)
        return

    data: QuizData = await state.get_data()

    if message.text not in data["options"]:
        await message.answer("Invalid option. Please select again.")
        return

    keyboard = create_keyboard(
        (["approve", "disapprove"], 2), (["go back", "cancel"], 2)
    )

    data["correct"] = data["options"].index(message.text)

    await state.update_data(correct=data["correct"])
    await state.set_state(QuizForm.confirm)
    await message.answer(
        f"Confirm quiz\n"
        f"Channel: {data['channel'].title}\n"
        f"Question: {data['question']}\n"
        f"Options: {', '.join(data['options'])}\n"
        f"Correct: {data['options'][data['correct']]}\n",
        reply_markup=keyboard,
    )


async def confirm_quiz(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    data: QuizData = await state.get_data()

    if message.text.lower() == "go back":
        keyboard = create_keyboard((data["options"], 2), (["go back", "cancel"], 2))
        await state.set_state(QuizForm.correct)
        await message.answer("Select the correct option: ", reply_markup=keyboard)
        return

    if message.text.lower() == "disapprove":
        await state.clear()
        await message.answer("Quiz discarded.", reply_markup=ReplyKeyboardRemove())
        return

    if message.text.lower() == "approve":
        async with AsyncSessionLocal() as session:
            quiz = await add_quiz(session, data)
            print(quiz)
            await session.commit()
        await state.clear()
        await message.answer(
            "Quiz added to database.", reply_markup=ReplyKeyboardRemove()
        )
        return

    await message.answer("Invalid response. Please choose one of the buttons.")


async def cancel(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Adding a quiz to channel canceled.", reply_markup=ReplyKeyboardRemove()
    )
