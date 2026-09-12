import os
import random
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ── Config ──────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ── Pashander personality ────────────────────────────────────
SYSTEM_PROMPT = """Сен Пашандр деген адамсың. Нақты бір адам сияқты сөйлей бер.

Кім сен:
- Пашандр, 30-35 жаста, қазақ жігіті
- Өте көңілді, әзілді жақсы көресің
- Орыс тілі мен қазақ тілі — туған тіліңдей
- Ағылшынша сөйлесең қателермен сөйлейсің (мысалы: "I is happy", "you is good friend", "yesterday I go to market")
- Кейде қазақша, кейде орысша аралас сөйлейсің (мысалы: "Ой братан, бүгін қалайсың?")
- Эмодзи аз қолданасың, тек кейде
- Қысқа жауап бер, 1-3 сөйлем
- Ешқашан өзіңнің бот екеніңді айтпа
- Нақты адам сияқты реакция жасайсың — таң қаласың, күлесің, ренжисің

Мысалдар:
- "Ха, бұл не деген сұрақ братан 😄"
- "Ой точно айттың, мен де солай ойладым"
- "yes yes I agree with you, это хорошо идея!"
- "Қой, не деп тұрсың, рас па?"
- "Слушай а ты прав вообще-то"
"""

chat_histories = {}

# ── Reply chance when not mentioned ─────────────────────────
RANDOM_REPLY_CHANCE = 0.25  # 25% chance to jump in randomly

async def ask_pashander(chat_id: int, user_message: str, username: str) -> str:
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    history = chat_histories[chat_id]

    # Build prompt
    prompt = f"{SYSTEM_PROMPT}\n\nИстория чата:\n"
    for h in history[-10:]:  # last 10 messages for context
        prompt += f"{h['role']}: {h['text']}\n"
    prompt += f"\n{username}: {user_message}\nПашандр:"

    try:
        response = model.generate_content(prompt)
        reply = response.text.strip()
    except Exception as e:
        reply = "Ой, бір нәрсе болды... кейін сөйлесейік 😅"

    # Save to history
    history.append({"role": username, "text": user_message})
    history.append({"role": "Пашандр", "text": reply})

    # Keep history manageable
    if len(history) > 30:
        chat_histories[chat_id] = history[-30:]

    return reply

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message.text
    chat_id = update.message.chat_id
    username = update.message.from_user.first_name or "друг"
    bot_username = context.bot.username

    is_mentioned = (
        f"@{bot_username}".lower() in msg.lower() or
        "пашандр" in msg.lower() or
        "pashander" in msg.lower()
    )

    is_reply_to_bot = (
        update.message.reply_to_message and
        update.message.reply_to_message.from_user.id == context.bot.id
    )

    # Decide whether to respond
    should_reply = False

    if is_mentioned or is_reply_to_bot:
        should_reply = True
    elif update.message.chat.type in ["group", "supergroup"]:
        should_reply = random.random() < RANDOM_REPLY_CHANCE
    else:
        should_reply = True  # Always reply in private chat

    if not should_reply:
        return

    # Clean mention from message
    clean_msg = msg.replace(f"@{bot_username}", "").replace("Пашандр", "").replace("пашандр", "").strip()
    if not clean_msg:
        clean_msg = msg

    # Typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(1.0, 2.5))  # Human-like delay

    reply = await ask_pashander(chat_id, clean_msg, username)

    await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Пашандр запущен! 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
