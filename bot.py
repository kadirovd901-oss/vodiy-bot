import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# === SOZLAMALAR ===
BOT_TOKEN = "8226068762:AAG5Vr9zRmW_ZSWHcWYHUx-brar-tKXQeBc"
KANAL_ID = -1003981225754
ADMIN_ID = None  # Quyida /start bosganda avtomatik to'ldiriladi

logging.basicConfig(level=logging.INFO)

pending_ads = {}  # {message_id: (user_id, text, contact)}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    user = update.effective_user
    
    # Birinchi /start bosgan admin bo'ladi
    if ADMIN_ID is None:
        ADMIN_ID = user.id
        await update.message.reply_text(
            f"✅ Siz admin sifatida ro'yxatdan o'tdingiz!\n"
            f"Admin ID: {user.id}\n\n"
            f"Endi odamlar e'lon yuborishsa, sizga keladi."
        )
    else:
        await update.message.reply_text(
            "👋 Assalomu alaykum!\n\n"
            "📢 *Vodiyda Sotiladi* kanaliga e'lon berish uchun:\n\n"
            "1️⃣ Mahsulot nomini yozing\n"
            "2️⃣ Narxini yozing\n"
            "3️⃣ Telefon raqamingizni yozing\n"
            "4️⃣ Rasm yuboring (ixtiyoriy)\n\n"
            "Hammasini *bir xabarda* yozing yoki boshlang 👇",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    if user.id == ADMIN_ID:
        return  # Admin xabarlarini o'tkazib yuborish
    
    # Foydalanuvchi xabarini saqlash
    text = message.text or message.caption or ""
    
    # Adminga yuborish
    if ADMIN_ID:
        preview_text = (
            f"📩 *Yangi e'lon so'rovi*\n\n"
            f"👤 Foydalanuvchi: [{user.first_name}](tg://user?id={user.id})\n"
            f"🆔 ID: `{user.id}`\n"
            f"📝 Matn:\n{text}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{message.message_id}_{user.id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.message_id}_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Rasmli bo'lsa
        if message.photo:
            sent = await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=message.photo[-1].file_id,
                caption=preview_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            sent = await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=preview_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        # Keyinroq topish uchun saqlash
        pending_ads[f"{message.message_id}_{user.id}"] = {
            "user_id": user.id,
            "text": text,
            "photo": message.photo[-1].file_id if message.photo else None,
            "user_name": user.first_name
        }
        
        await message.reply_text(
            "✅ E'loningiz qabul qilindi!\n"
            "⏳ Tez orada ko'rib chiqiladi va kanalga joylashtiriladi."
        )
    else:
        await message.reply_text("⚙️ Bot sozlanmoqda, biroz kuting...")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    parts = data.split("_", 2)
    action = parts[0]
    key = f"{parts[1]}_{parts[2]}"
    
    if key not in pending_ads:
        await query.edit_message_text("⚠️ Bu e'lon topilmadi (eskirgan bo'lishi mumkin)")
        return
    
    ad = pending_ads[key]
    
    if action == "approve":
        # Kanalga chiqarish
        kanal_text = (
            f"🛒 *YANGI E'LON*\n\n"
            f"{ad['text']}\n\n"
            f"📞 Bog'lanish: [{ad['user_name']}](tg://user?id={ad['user_id']})\n\n"
            f"📢 @vodiyda\\_sotiladi"
        )
        
        if ad['photo']:
            await context.bot.send_photo(
                chat_id=KANAL_ID,
                photo=ad['photo'],
                caption=kanal_text,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=KANAL_ID,
                text=kanal_text,
                parse_mode="Markdown"
            )
        
        # Foydalanuvchiga xabar
        await context.bot.send_message(
            chat_id=ad['user_id'],
            text="🎉 E'loningiz kanalga joylashtirildi!\n👉 @vodiyda_sotiladi"
        )
        
        await query.edit_message_text(f"✅ E'lon tasdiqlandi va kanalga chiqarildi!")
        del pending_ads[key]
        
    elif action == "reject":
        await context.bot.send_message(
            chat_id=ad['user_id'],
            text="❌ Afsuski, e'loningiz qabul qilinmadi.\n\nSabablar:\n• Noto'g'ri format\n• Taqiqlangan tovar\n\nQayta urinib ko'ring."
        )
        await query.edit_message_text("❌ E'lon rad etildi.")
        del pending_ads[key]

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
