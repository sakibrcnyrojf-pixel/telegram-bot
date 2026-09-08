import os
import requests
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Render-এর Port Timeout এরর বন্ধ করার জন্য ফেক ওয়েব সার্ভার
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# ----------------- বটের মূল কোড -----------------
BOT_TOKEN = "8697610230:AAFzzjFmO_VzOeC48v6Rf51uRkv2R15J23Q"  # আপনার সম্পূর্ণ আসল বট টোকেনটি এখানে দিন

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salam! Send me any video link (FB, Insta, TikTok, YouTube), and I will download it for you.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("Downloading video, please wait...")

    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        response = requests.get(api_url).json()

        if response.get("code") == 0:
            video_url = response["data"]["play"]
            caption = response["data"].get("title", "Downloaded Video")
            
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_url,
                caption=f"✨ {caption}"
            )
            await msg.delete()
        else:
            await msg.edit_text("ভিডিওটি পাওয়া যায়নি বা লিংকটি ভুল!")

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")

    msg = await update.message.reply_text("Downloading video, please wait...")
    ydl_opts = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    # TikTok IP Block bypass headers
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    },
    'extractor_args': {
        'tiktok': {
            'app_version': '30.8.4',
            'manifest_app_version': '30.8.4',
        }
    }
    }
        
    

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.edit_text("Uploading to Telegram...")
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)
        
        if os.path.exists(filename):
            os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")

def main():
    # ব্যাকগ্রাউন্ডে ওয়েব সার্ভার চালু রাখা
    threading.Thread(target=run_web_server, daemon=True).start()

    # বট সার্ভিস চালু
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("Bot speed testing & polling active...")
    app.run_polling()

if __name__ == "__main__":
    main()
