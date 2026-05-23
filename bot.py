import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "8226068762:AAG5Vr9zRmW_ZSWHcWYHUx-brar-tKXQeBc"
KANAL_ID = -1003981225754

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = None
pending_ads = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    user = update.effective_user
    if ADMIN_ID is None:
        ADMIN_ID = user.id
        await update.message.reply_text(f"Admin sifatida sozlandingiz! ID: {user.id}")
    else:
        await update.message.reply_text(
            "Assalomu alaykum!\n\n"
            "Vodiyda Sotiladi kanaliga elon berish uchun:\n"
            "- Mahsulot nomi\n"
            "- Narxi\n"
            "- Telefon raqam\n"
            "- Rasm (ixtiyoriy)\n\n"
            "Hammasini bir xabarda yuboring!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    user = update.effective_user
    message = update.message

    if ADMIN_ID and user.id == ADMIN_ID:
        return

    text = message.text or message.caption or "(Matn yoq)"
    key = f"{message.message_id}_{user.id}"

    pending_ads[key] = {
        "user_id": user.id,
        "text": text,
        "photo": message.photo[-1].file_id if message.photo else None,
        "user_name": user.first_name or "Foydalanuvchi"
    }

    if ADMIN_ID:
        caption = f"Yangi elon sorovi\n\nFoydalanuvchi: {user.first_name} (ID: {user.id})\nMatn: {text}"
        keyboard = [[
            InlineKeyboardButton("Tasdiqlash", callback_data=f"approve_{key}"),
            InlineKeyboardButton("Rad etish", callback_data=f"reject_{key}")
        ]]
        markup = InlineKeyboardMarkup(keyboard)

        if message.photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=markup)
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=markup)

    await message.reply_text("Eloningiz qabul qilindi! Tez orada korib chiqiladi.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        key = data[8:]
        action = "approve"
    elif data.startswith("reject_"):
        key = data[7:]
        action = "reject"
    else:
        return

    if key not in pending_ads:
        await query.edit_message_text("Bu elon topilmadi.")
        return

    ad = pending_ads[key]

    if action == "approve":
        kanal_text = f"YANGI ELON\n\n{ad['text']}\n\nMuallif: {ad['user_name']}\n@vodiyda_sotiladi"
        if ad["photo"]:
            await context.bot.send_photo(chat_id=KANAL_ID, photo=ad["photo"], caption=kanal_text)
        else:
            await context.bot.send_message(chat_id=KANAL_ID, text=kanal_text)
        await context.bot.send_message(chat_id=ad["user_id"], text="Eloningiz kanalga joylashtirildi! @vodiyda_sotiladi")
        await query.edit_message_text("Elon kanalga chiqarildi!")
    else:
        await context.bot.send_message(chat_id=ad["user_id"], text="Eloningiz qabul qilinmadi. Qayta urinib koring.")
        await query.edit_message_text("Elon rad etildi.")

    del pending_ads[key]

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
