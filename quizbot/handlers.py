import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from bot import bot
from db import AsyncSessionLocal
from helpers import (
    add_channel_admins,
    create_keyboard,
    delete_channel_admins,
    get_user_channels,
    save_quiz_to_db,
    upsert_channel,
    upsert_user,
)
from messages import OPTION_EMOJIS, Btn, Msg
from type import QuizData, QuizForm


async def handle_bot_join(event: types.ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat)
        await asyncio.sleep(1)
        admins = await bot.get_chat_administrators(channel.id)
        admin_users = [admin.user for admin in admins]
        await add_channel_admins(session, channel.id, admin_users)
        await session.commit()


async def handle_bot_leave(event: types.ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat)
        await delete_channel_admins(session, channel.id)
        await session.commit()


async def handle_user_promote(event: types.ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await add_channel_admins(session, event.chat.id, [user])
        await session.commit()


async def handle_user_demote(event: types.ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await delete_channel_admins(session, event.chat.id, [user.id])
        await session.commit()


async def handle_start_command(message: types.Message) -> None:
    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer(Msg.START)


async def start_quiz_creation(message: types.Message, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        channels = await get_user_channels(session, message.from_user)
        if not channels:
            await message.answer(Msg.NO_CHANNELS)
            return

        titles = [ch.title for ch in channels]
        await state.set_data({"channels": channels, "titles": titles})
        await state.set_state(QuizForm.select_channel)
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await message.answer(Msg.PROMPT_CHANNEL, reply_markup=keyboard)


async def select_channel(message: types.Message, state: FSMContext) -> None:
    data: QuizData = await state.get_data()
    if message.text not in data["titles"]:
        await message.answer(Msg.INVALID_RESPONSE)
        return

    channel = data["channels"][data["titles"].index(message.text)]
    await state.update_data(channel=channel)
    await state.set_state(QuizForm.question)
    keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(Msg.PROMPT_QUESTION, reply_markup=keyboard)


async def handle_question_input(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.select_channel)
        data: QuizData = await state.get_data()
        keyboard = create_keyboard((data["titles"], 2), ([Btn.CANCEL], 1))
        await message.answer(Msg.PROMPT_CHANNEL, reply_markup=keyboard)
        return

    if len(message.text) > 300:
        await message.answer(Msg.QUESTION_TOO_LONG)
        return

    await state.update_data(question=message.text, options=[])
    await state.set_state(QuizForm.collect_options)
    keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(Msg.PROMPT_OPTION, reply_markup=keyboard)


async def handle_option_input(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.question)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_QUESTION, reply_markup=keyboard)
        return

    if len(message.text) > 100:
        await message.answer(Msg.OPTION_TOO_LONG)
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.FINISH:
        if len(data["options"]) < 2:
            await message.answer(Msg.NEED_TWO_OPTIONS)
            return

        await state.set_state(QuizForm.correct_option)
        keyboard = create_keyboard((data["options"], 2), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_SELECT_CORRECT, reply_markup=keyboard)
        return

    if len(data["options"]) >= 10:
        await message.answer(Msg.MAX_OPTIONS_REACHED)
        return

    data["options"].append(message.text)
    await state.update_data(options=data["options"])
    keyboard = create_keyboard(
        ([Btn.FINISH] if len(data["options"]) >= 2 else [], 1),
        ([Btn.BACK, Btn.CANCEL], 2),
    )
    await message.answer(Msg.OPTION_ADDED, reply_markup=keyboard)


async def select_correct_option(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.collect_options)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_OPTION, reply_markup=keyboard)
        return

    data: QuizData = await state.get_data()
    if message.text not in data["options"]:
        await message.answer(Msg.INVALID_RESPONSE)
        return

    await state.update_data(correct_index=data["options"].index(message.text))
    await state.set_state(QuizForm.explanation)
    keyboard = create_keyboard(([Btn.SKIP], 1), ([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(
        Msg.PROMPT_EXPLANATION.format(skip_btn=Btn.SKIP), reply_markup=keyboard
    )


async def handle_explanation(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    if len(message.text) > 200:
        await message.answer(Msg.EXPLANATION_TOO_LONG)
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.BACK:
        await state.set_state(QuizForm.correct_option)
        keyboard = create_keyboard((data["options"], 2), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(Msg.PROMPT_SELECT_CORRECT, reply_markup=keyboard)
        return

    explanation = None if message.text == Btn.SKIP else message.text
    await state.update_data(explanation=explanation)
    await state.set_state(QuizForm.confirmation)

    keyboard = create_keyboard(
        ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
    )
    await message.answer(
        Msg.PREVIEW.format(
            channel=data["channel"].title,
            question=data["question"],
            options="\n".join(
                [
                    f"\t\t{OPTION_EMOJIS[i + 1]} {opt}"
                    for i, opt in enumerate(data["options"])
                ]
            ),
            correct=data["options"][data["correct_index"]],
            explanation=explanation if explanation else "",
        ),
        reply_markup=keyboard,
    )


async def confirm_quiz(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.BACK:
        await state.set_state(QuizForm.explanation)
        keyboard = create_keyboard(([Btn.SKIP], 1), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_EXPLANATION.format(skip_btn=Btn.SKIP), reply_markup=keyboard
        )
        return

    if message.text == Btn.REJECT:
        await state.clear()
        await message.answer(
            Msg.CANCELED.format(status="disapproved"),
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if message.text == Btn.APPROVE:
        async with AsyncSessionLocal() as session:
            await save_quiz_to_db(session, data)
            await session.commit()
        await state.clear()
        await message.answer(Msg.SAVED, reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(Msg.INVALID_RESPONSE)


async def cancel_quiz(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        Msg.CANCELED.format(status="Canceled"), reply_markup=ReplyKeyboardRemove()
    )
