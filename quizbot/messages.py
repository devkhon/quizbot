class Msg:
    START = (
        "👋 Hello! I'm here to help you create quizzes for your channels. "
        "Use /addquiz to begin."
    )

    NO_CHANNELS = (
        "⚠️ You don't have any channels where I'm an admin.\n\n"
        "Please add me as an **admin** to your channel and try again."
    )

    PROMPT_CHANNEL = "📢 Select a channel to post your quiz in:"
    PROMPT_QUESTION = "❓What's the quiz question?"
    QUESTION_TOO_LONG = (
        "❗The question is too long. Please limit it to **300 characters or fewer**"
    )

    PROMPT_OPTION = "✏️ Send me one possible answer:"
    OPTION_TOO_LONG = (
        "❗The option is too long. Please limit it to **100 characters or fewer**"
    )

    NEED_TWO_OPTIONS = "⚠️ Add at least 2 options before finishing."
    MAX_OPTIONS_REACHED = "🚫 You've reached the maximum of 10 options."
    OPTION_ADDED = "✅ Option added!\n\nSend another one."
    PROMPT_SELECT_CORRECT = "✅ Pick the correct answer from the list below:"
    PROMPT_EXPLANATION = "💬 Send an explanation for this quiz (or tap {skip_btn})."
    EXPLANATION_TOO_LONG = (
        "❗The explanation is too long. Please limit it to **200 characters or fewer**"
    )

    PREVIEW = (
        "📝 *Quiz Preview*\n\n"
        "📢 Channel: {channel}\n"
        "❓ Question: {question}\n"
        "🔢 Options: \n{options}\n"
        "✅ Correct: {correct}\n"
        "ℹ️ Explanation: {explanation}\n\n"
        "Do you want to approve this quiz?"
    )

    SAVED = "🎉 Quiz saved!"
    CANCELED = "🚫 Quiz creation {status}."
    INVALID_RESPONSE = "❗ Invalid response. Please use one of the provided buttons."


class Btn:
    BACK = "↩️ Back"
    CANCEL = "❌ Cancel"
    FINISH = "🎯 Done"
    SKIP = "⏭️ Skip"
    APPROVE = "✅ Approve"
    REJECT = "🗑️ Disapprove"


OPTION_EMOJIS = [
    "0️⃣",
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🔟",
]
