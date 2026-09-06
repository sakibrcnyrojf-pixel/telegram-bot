import os
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
BOT_TOKEN = "8697610230:AAFwXt7o_9zW_EolaYYwSV54jYRNmYNOgAo"  # আপনার সম্পূর্ণ আসল বট টোকেনটি এখানে দিন

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salam! Send me any video link (FB, Insta, TikTok, YouTube), and I will download it for you.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("Downloading video, please wait...")
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'max_filesize': 50 * 1024 * 1024, # ৫০ এমবির বেশি হলে ডাউনলোড হবে না (টেলিগ্রাম লিমিট)
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
