import os
import random
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import google.generativeai as genai

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
- Нақты адам сияқты реакция жасайсың

Мысалдар:
- "Ха, бұл не деген сұрақ братан 😄"
- "Ой точно айттың, мен де солай ойладым"
- "yes yes I agree with you, это хорошо идея!"
- "Қой, не деп тұрсың, рас па?"
- "Слушай а ты прав вообще-то"
"""

chat_histories = {}
RANDOM_REPLY_CHANCE = 0.25

async def ask_pashander(chat_id, user_message, username):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    history = chat_histories[chat_id]
    prompt = f"{SYSTEM_PROMPT}\n\nИстория:\n"
    for h in history[-10:]:
        prompt += f"{h['role']}: {h['text']}\n"
    prompt += f"\n{username}: {user_message}\nПашандр:"
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        reply = response.text.strip()
    except Exception as e:
        reply = "Ой, бір нәрсе болды 😅"
    history.append({"role": username, "text": user_message})
    history.append({"role": "Пашандр", "text": reply})
    if len(history) > 30:
        chat_histories[chat_id] = history[-30:]
    return reply

async def handle_message(update, context):
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
    should_reply = False
    if is_mentioned or is_reply_to_bot:
        should_reply = True
    elif update.message.chat.type in ["group", "supergroup"]:
        should_reply = random.random() < RANDOM_REPLY_CHANCE
    else:
        should_reply = True
    if not should_reply:
        return
    clean_msg = msg.replace(f"@{bot_username}", "").replace("Пашандр", "").replace("пашандр", "").strip()
    if not clean_msg:
        clean_msg = msg
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(1.0, 2.5))
    reply = await ask_pashander(chat_id, clean_msg, username)
    await update.message.reply_text(reply)

def main():
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not telegram_token or not gemini_key:
        raise ValueError("TELEGRAM_TOKEN и GEMINI_API_KEY должны быть заданы!")
    genai.configure(api_key=gemini_key)
    app = Application.builder().token(telegram_token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Пашандр запущен! 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
