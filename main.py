import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Replace with your actual Bot Token from BotFather
BOT_TOKEN = "8697610230:AAFwXt7o_9zW_EolaYYwSV54jYRNmYNOgAo"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **স্বাগতম!**\n\n"
        "আমি একটি ভিডিও ডাউনলোডার বট। আমাকে Facebook, Instagram, TikTok, "
        "বা YouTube-এর যেকোনো ভিডিওর Public Link পাঠান, আমি সেটি আপনাকে ডাউনলোড করে দেব।"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Video downloader function
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ এটি কোনো সঠিক ভিডিও লিংক নয়। অনুগ্রহ করে একটি সঠিক লিংক পাঠান।")
        return

    status_msg = await update.message.reply_text("⏳ ভিডিওটি প্রসেস করা হচ্ছে, অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন...")

    output_filename = f"video_{update.message.message_id}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_filename,
        'max_filesize': 50 * 1024 * 1024,  # 50MB telegram bot limit
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await status_msg.edit_text("📤 ভিডিও ডাউনলোড সম্পন্ন! এখন টেলিগ্রামে আপলোড করা হচ্ছে...")

        with open(output_filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ **আপনার ডাউনলোডেড ভিডিও!**",
                parse_mode="Markdown"
            )

        if os.path.exists(output_filename):
            os.remove(output_filename)
            
        await status_msg.delete()

    except yt_dlp.utils.MaxDownloadsReached:
        await status_msg.edit_text("❌ ফাইলটির সাইজ ৫০MB-এর বেশি হওয়ায় টেলিগ্রামে পাঠানো সম্ভব হচ্ছে না।")
    except Exception as e:
        await status_msg.edit_text("❌ ভিডিওটি ডাউনলোড করা যায়নি। ভিডিওটি প্রাইভেট হতে পারে অথবা লিংকটি কাজ করছে না।")
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot speed testing & polling active...")
    app.run_polling()
