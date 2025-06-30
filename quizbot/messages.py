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
    OPTION_ADDED = "✅ Option added!\n\nSend another option or tap *{finish_btn}*."
    PROMPT_SELECT_CORRECT = "✅ Pick the correct answer in:"
    PREVIEW = (
        "📝 *Quiz Preview*\n\n"
        "📢 Channel: *{channel}*\n"
        "❓ Question: *{question}*\n"
        "🔢 Options:\n{options}\n\n"
        "✅ Correct: *{correct}*\n\n"
        "Do you want to approve this quiz?"
    )
    SAVED = "🎉 Quiz saved!"
    CANCELED = "🚫 Quiz creation {status}."
    INVALID_RESPONSE = "❗ Invalid response. Please use one of the provided buttons."


class Btn:
    GO_BACK = "↩️ Go back"
    CANCEL = "❌ Cancel"
    FINISH = "🎯 Done"
    APPROVE = "✅ Approve"
    DISAPPROVE = "❌ Disapprove"
