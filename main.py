import os
import requests
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ----------------- ১. চ্যানেল সেটআপ -----------------
CHANNEL_USERNAME = "@RMEarning9" 

# ----------------- ২. Render Port Timeout হ্যান্ডলার -----------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# ----------------- ৩. জয়েন ভেরিফিকেশন -----------------
async def is_user_joined(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Check Join Error: {e}")
        return False
    return False

# ----------------- ৪. বট কমান্ড হ্যান্ডলার -----------------
BOT_TOKEN = "8697610230:AAFUChryG7XjOt_Cu25tYXmWCKY0_colmq8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    joined = await is_user_joined(context.bot, user_id)
    
    if joined:
        await update.message.reply_text("Salam! Send me any TikTok, Facebook, YouTube, or Instagram video link to download.")
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ বটটি ব্যবহার করতে আপনাকে প্রথমে আমাদের চ্যানেলে জয়েন হতে হবে!", 
            reply_markup=reply_markup
        )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    joined = await is_user_joined(context.bot, user_id)
    
    if joined:
        await query.message.edit_text("✅ ধন্যবাদ! চ্যানেল জয়েন সফল হয়েছে। এখন যেকোনো লিংক পাঠাতে পারেন।")
    else:
        await query.message.reply_text("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন, তারপর আবার বোতামে চাপুন।")

# ----------------- ৫. অল-ইন-ওয়ান ভিডিও ডাউনলোডার -----------------
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if not url.startswith("http"):
        return

    # চ্যানেল জয়েন চেক
    joined = await is_user_joined(context.bot, user_id)
    if not joined:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ ভিডিও ডাউনলোড করতে আগে চ্যানেলে জয়েন করুন!", reply_markup=reply_markup)
        return

    msg = await update.message.reply_text("Downloading video, please wait...")

    try:
        # ১. TikTok ডাউনলোড
        if "tiktok.com" in url:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            res = requests.get(api_url).json()
            if res.get("code") == 0:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=res["data"]["play"], caption="✨ TikTok Video")
                await msg.delete()
            else:
                await msg.edit_text("টিকটক ভিডিওটি পাওয়া যায়নি!")

        # ২. Instagram ডাউনলোড
        elif "instagram.com" in url:
            api_url = f"https://aero-api.vercel.app/api/instagram?url={url}"
            res = requests.get(api_url).json()
            if "url" in res:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=res["url"], caption="✨ Instagram Video")
                await msg.delete()
            else:
                await msg.edit_text("ইনস্টাগ্রাম ভিডিও ডাউনলোড করা সম্ভব হয়নি!")

        # ৩. Facebook / YouTube ডাউনলোড (Universal API)
        elif "facebook.com" in url or "fb.watch" in url or "youtube.com" in url or "youtu.be" in url:
            api_url = f"https://api.cobalt.tools/api/json"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = {"url": url}
            
            res = requests.post(api_url, json=payload, headers=headers).json()
            if "url" in res:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=res["url"], caption="✨ Downloaded Video")
                await msg.delete()
            else:
                await msg.edit_text("ভিডিওটি প্রসেস করা সম্ভব হয়নি! লিংকটি সঠিক কিনা যাচাই করুন।")

        else:
            await msg.edit_text("শুধুমাত্র TikTok, Facebook, YouTube এবং Instagram এর লিংক সাপোর্ট করবে!")

    except Exception as e:
        await msg.edit_text("সার্ভার ত্রুটি! কিছুক্ষণ পর আবার চেষ্টা করুন।")

# ----------------- ৬. মেইন এক্সিকিউশন -----------------
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    print("Bot is running...")
    app.run_polling()
