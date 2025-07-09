from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from db import AsyncSessionLocal
from helpers import create_keyboard, escape_markdown, get_user_channels
from messages import Btn, Msg
from models import Option, Quiz
from sqlalchemy.ext.asyncio import AsyncSession
from type import QuizData, QuizForm

router = Router()


async def save_quiz_to_db(session: AsyncSession, data: QuizData) -> Quiz:
    quiz = Quiz(
        question=data["question"],
        correct_order=data["correct_order"],
        explanation=data["explanation"],
        user_id=data["user_id"],
        channel_id=data["channel"].id,
    )
    session.add(quiz)
    await session.flush()

    session.add_all(
        [
            Option(option=op, order=i, quiz_id=quiz.id)
            for i, op in enumerate(data["options"])
        ]
    )

    return quiz


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


quiz_state_filter = StateFilter(*QuizForm.__all_states__)

router.message.register(start_quiz_creation, Command("addquiz"))
router.message.register(cancel_quiz, quiz_state_filter, F.text == Btn.CANCEL)
router.message.register(select_channel, QuizForm.select_channel)
router.message.register(handle_question_input, QuizForm.question)
router.message.register(handle_option_input, QuizForm.collect_options)
router.message.register(select_correct_option, QuizForm.correct_option)
router.message.register(handle_explanation, QuizForm.explanation)
router.message.register(confirm_quiz, QuizForm.confirmation)
