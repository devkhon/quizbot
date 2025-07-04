import asyncio
from datetime import datetime

from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatMemberUpdated, Message, ReplyKeyboardRemove
from bot import bot
from db import AsyncSessionLocal
from helpers import (
    add_channel_admins,
    create_keyboard,
    delete_channel_admins,
    escape_markdown,
    get_user_channels,
    save_quiz_to_db,
    upsert_channel,
    upsert_user,
)
from messages import Btn, Msg
from type import QuizData, QuizForm, SettingsForm


async def handle_bot_join(event: ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat, True)
        await asyncio.sleep(1)
        admins = await bot.get_chat_administrators(channel.id)
        admin_users = [admin.user for admin in admins]
        await add_channel_admins(session, channel.id, admin_users)
        await session.commit()


async def handle_bot_leave(event: ChatMemberUpdated) -> None:
    async with AsyncSessionLocal() as session:
        channel = await upsert_channel(session, event.chat, False)
        await delete_channel_admins(session, channel.id)
        await session.commit()


async def handle_user_promote(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await add_channel_admins(session, event.chat.id, [user])
        await session.commit()


async def handle_user_demote(event: ChatMemberUpdated) -> None:
    user = event.new_chat_member.user
    async with AsyncSessionLocal() as session:
        await delete_channel_admins(session, event.chat.id, [user.id])
        await session.commit()


async def handle_start_command(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        await upsert_user(session, message.from_user)
        await session.commit()
    await message.answer(Msg.START, parse_mode=ParseMode.MARKDOWN_V2)


async def start_quiz_creation(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        channels = await get_user_channels(session, message.from_user)
        if not channels:
            await message.answer(Msg.NO_CHANNELS, parse_mode=ParseMode.MARKDOWN_V2)
            return

        titles = [ch.title for ch in channels]
        data: QuizData = QuizData(
            channels=channels,
            user_id=message.from_user.id,
            channel=None,
            question=None,
            options=None,
            correct_order=None,
            explanation=None,
        )
        await state.set_data(data)
        await state.set_state(QuizForm.select_channel)
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await message.answer(
            Msg.PROMPT_CHANNEL, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )


async def select_channel(message: Message, state: FSMContext) -> None:
    data: QuizData = await state.get_data()
    titles = [ch.title for ch in data["channels"]]
    if message.text not in titles:
        await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)
        return

    channel = data["channels"][titles.index(message.text)]
    await state.update_data(channel=channel)
    await state.set_state(QuizForm.question)
    keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(
        Msg.PROMPT_QUESTION, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def handle_question_input(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.select_channel)
        data: QuizData = await state.get_data()
        titles = [ch.title for ch in data["channels"]]
        keyboard = create_keyboard((titles, 2), ([Btn.CANCEL], 1))
        await message.answer(
            Msg.PROMPT_CHANNEL, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if len(message.text) > 300:
        await message.answer(Msg.QUESTION_TOO_LONG, parse_mode=ParseMode.MARKDOWN_V2)
        return

    await state.update_data(question=message.text, options=[])
    await state.set_state(QuizForm.collect_options)
    keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(
        Msg.PROMPT_OPTION, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def handle_option_input(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.question)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_QUESTION, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    if len(message.text) > 100:
        await message.answer(Msg.OPTION_TOO_LONG, parse_mode=ParseMode.MARKDOWN_V2)
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.FINISH:
        if len(data["options"]) < 2:
            await message.answer(Msg.NEED_TWO_OPTIONS, parse_mode=ParseMode.MARKDOWN_V2)
            return

        await state.set_state(QuizForm.correct_option)
        keyboard = create_keyboard((data["options"], 2), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_SELECT_CORRECT,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if len(data["options"]) >= 10:
        await message.answer(Msg.MAX_OPTIONS_REACHED, parse_mode=ParseMode.MARKDOWN_V2)
        return

    data["options"].append(message.text)
    await state.update_data(options=data["options"])
    keyboard = create_keyboard(
        ([Btn.FINISH] if len(data["options"]) >= 2 else [], 1),
        ([Btn.BACK, Btn.CANCEL], 2),
    )
    await message.answer(
        Msg.OPTION_ADDED, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )


async def select_correct_option(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if message.text == Btn.BACK:
        await state.set_state(QuizForm.collect_options)
        keyboard = create_keyboard(([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_OPTION, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    data: QuizData = await state.get_data()
    if message.text not in data["options"]:
        await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)
        return

    await state.update_data(correct_order=data["options"].index(message.text))
    await state.set_state(QuizForm.explanation)
    keyboard = create_keyboard(([Btn.SKIP], 1), ([Btn.BACK, Btn.CANCEL], 2))
    await message.answer(
        Msg.PROMPT_EXPLANATION.format(skip_btn=Btn.SKIP),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def handle_explanation(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    if len(message.text) > 200:
        await message.answer(Msg.EXPLANATION_TOO_LONG, parse_mode=ParseMode.MARKDOWN_V2)
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.BACK:
        await state.set_state(QuizForm.correct_option)
        keyboard = create_keyboard((data["options"], 2), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_SELECT_CORRECT,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    explanation = None if message.text == Btn.SKIP else message.text
    await state.update_data(explanation=explanation)
    await state.set_state(QuizForm.confirmation)

    keyboard = create_keyboard(
        ([Btn.APPROVE, Btn.REJECT], 2), ([Btn.BACK, Btn.CANCEL], 2)
    )
    await message.answer(
        Msg.PREVIEW.format(
            channel=escape_markdown(data["channel"].title),
            question=escape_markdown(data["question"]),
            options="\n".join(
                [escape_markdown(f"\t\t- {opt}") for opt in data["options"]]
            ),
            correct=escape_markdown(data["options"][data["correct_order"]]),
            explanation=escape_markdown(explanation) if explanation else "",
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def confirm_quiz(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    data: QuizData = await state.get_data()
    if message.text == Btn.BACK:
        await state.set_state(QuizForm.explanation)
        keyboard = create_keyboard(([Btn.SKIP], 1), ([Btn.BACK, Btn.CANCEL], 2))
        await message.answer(
            Msg.PROMPT_EXPLANATION.format(skip_btn=Btn.SKIP),
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text == Btn.REJECT:
        await state.clear()
        await message.answer(
            Msg.REJECTED,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    if message.text == Btn.APPROVE:
        async with AsyncSessionLocal() as session:
            await save_quiz_to_db(session, data)
            await session.commit()
        await state.clear()
        await message.answer(
            Msg.SAVED,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await message.answer(Msg.INVALID_RESPONSE, parse_mode=ParseMode.MARKDOWN_V2)


async def cancel_quiz(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        Msg.CANCELED,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


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
