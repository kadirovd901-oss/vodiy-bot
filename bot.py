import requests
import time

BOT_TOKEN = "8226068762:AAG5Vr9zRmW_ZSWHcWYHUx-brar-tKXQeBc"
KANAL_ID = -1003981225754
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

ADMIN_ID = None
pending_ads = {}
offset = 0

def send(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        import json
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API}/sendMessage", data=data)

def send_photo(chat_id, photo, caption, reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo, "caption": caption}
    if reply_markup:
        import json
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"{API}/sendPhoto", data=data)

def answer_callback(callback_id):
    requests.post(f"{API}/answerCallbackQuery", data={"callback_query_id": callback_id})

def edit_message(chat_id, message_id, text):
    requests.post(f"{API}/editMessageText", data={"chat_id": chat_id, "message_id": message_id, "text": text})

def get_updates():
    global offset
    try:
        r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
        return r.json().get("result", [])
    except:
        return []

def handle_update(update):
    global ADMIN_ID, pending_ads

    if "callback_query" in update:
        cb = update["callback_query"]
        answer_callback(cb["id"])
        data = cb["data"]
        chat_id = cb["message"]["chat"]["id"]
        message_id = cb["message"]["message_id"]

        if data.startswith("approve_"):
            key = data[8:]
            if key in pending_ads:
                ad = pending_ads[key]
                text = f"YANGI ELON\n\n{ad['text']}\n\nMuallif: {ad['user_name']}\n@vodiyda_sotiladi"
                if ad.get("photo"):
                    send_photo(KANAL_ID, ad["photo"], text)
                else:
                    send(KANAL_ID, text)
                send(ad["user_id"], "Eloningiz kanalga joylashtirildi! @vodiyda_sotiladi")
                edit_message(chat_id, message_id, "Elon kanalga chiqarildi!")
                del pending_ads[key]

        elif data.startswith("reject_"):
            key = data[7:]
            if key in pending_ads:
                ad = pending_ads[key]
                send(ad["user_id"], "Eloningiz qabul qilinmadi. Qayta urinib koring.")
                edit_message(chat_id, message_id, "Elon rad etildi.")
                del pending_ads[key]
        return

    if "message" not in update:
        return

    msg = update["message"]
    user_id = msg["from"]["id"]
    user_name = msg["from"].get("first_name", "Foydalanuvchi")
    text = msg.get("text", "") or msg.get("caption", "") or "(Matn yoq)"

    if text == "/start":
        if ADMIN_ID is None:
            ADMIN_ID = user_id
            send(user_id, f"Admin sifatida sozlandingiz! ID: {user_id}")
        else:
            send(user_id, "Assalomu alaykum!\n\nVodiyda Sotiladi kanaliga elon berish uchun mahsulot nomi, narxi va telefon raqamingizni yuboring.")
        return

    if ADMIN_ID and user_id == ADMIN_ID:
        return

    msg_id = msg["message_id"]
    key = f"{msg_id}_{user_id}"
    photo = None
    if "photo" in msg:
        photo = msg["photo"][-1]["file_id"]

    pending_ads[key] = {"user_id": user_id, "text": text, "photo": photo, "user_name": user_name}

    if ADMIN_ID:
        caption = f"Yangi elon sorovi\n\nFoydalanuvchi: {user_name} (ID: {user_id})\nMatn: {text}"
        keyboard = {"inline_keyboard": [[
            {"text": "Tasdiqlash", "callback_data": f"approve_{key}"},
            {"text": "Rad etish", "callback_data": f"reject_{key}"}
        ]]}
        if photo:
            send_photo(ADMIN_ID, photo, caption, keyboard)
        else:
            send(ADMIN_ID, caption, keyboard)

    send(user_id, "Eloningiz qabul qilindi! Tez orada korib chiqiladi.")

print("Bot ishga tushdi!")
while True:
    try:
        updates = get_updates()
        for update in updates:
            offset = update["update_id"] + 1
            handle_update(update)
    except Exception as e:
        print(f"Xato: {e}")
        time.sleep(5)
