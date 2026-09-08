import os
import requests
import asyncio
import threading
import yt_dlp
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ----------------- ১. চ্যানেল সেটআপ -----------------
CHANNEL_USERNAME = "@rm_download_bot" 

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
BOT_TOKEN = "8697610230:AAGUKFrXlDBpboeQJQppGaO17TzilvIoeAU"

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

# ----------------- ৫. ভিডিও ডাউনলোডার ফাংশন -----------------
def get_video_direct_url(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('url'), info.get('title', 'Video')

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
        # ১. TikTok (Tikwm API দিয়ে ফাস্ট ডাউনলোড)
        if "tiktok.com" in url:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            res = requests.get(api_url).json()
            if res.get("code") == 0:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=res["data"]["play"], caption="✨ TikTok Video")
                await msg.delete()
                return

        # ২. FB / IG / YT / অন্যান্য সব লিংক (yt-dlp দিয়ে)
        loop = asyncio.get_event_loop()
        video_url, title = await loop.run_in_executor(None, get_video_direct_url, url)

        if video_url:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_url,
                caption=f"✨ {title[:100]}"
            )
            await msg.delete()
        else:
            await msg.edit_text("ভিডিওর লিংক প্রসেস করা সম্ভব হয়নি!")

    except Exception as e:
        await msg.edit_text("ভিডিওটি প্রসেস করতে সমস্যা হয়েছে। অন্য কোনো পাবলিক ভিডিও লিংক চেষ্টা করুন!")

# ----------------- ৬. মেইন এক্সিকিউশন -----------------
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    print("Bot is running...")
    app.run_polling()
