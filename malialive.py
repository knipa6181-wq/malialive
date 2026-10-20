import os
import threading
import asyncio
import random
import time
import urllib.parse
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# --- Render Web Server (501 Not Implemented Fix) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def _send_ok(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', '13')
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def do_GET(self):
        self._send_ok()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', '13')
        self.end_headers()

    def do_POST(self):
        self._send_ok()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Allow', 'GET, HEAD, POST, OPTIONS')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def log_message(self, format, *args):
        return  # অতিরিক্ত লগ বন্ধ রাখা

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- Configuration ---
BOT_TOKEN = "8838722017:AAFVBXpLpojx4090_UkWM8lDK8qlWLZ_QuU"

# আলাদা আলাদা ৪টি বিজ্ঞাপন লিংক
AD_URLS = {
    "ad_1": "https://auctionr.org/4/e6164d8130c07e4f4dcb8a1d486e367e",
    "ad_2": "https://auctionr.org/4/935f34c5d14c5616973249d5ca5e1a4e",
    "ad_3": "https://asiafilm.org/4/94ee730f3d01052ac1a7301e79c205cc",
    "ad_4": "https://uplcm.com/4/12077063"
}

CHANNEL_1_ID = "@your_channel_1"
CHANNEL_2_ID = "@your_channel_2"
CHANNEL_1_URL = "https://t.me/your_channel_1"
CHANNEL_2_URL = "https://t.me/your_channel_2"

VIP_SECRET_LINK = "https://example.com/exclusive-vip-access-link"
GIF_URL = "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif"

# Data Storage
user_coins = {}
user_names = {}
daily_claims = {}
spin_records = {}
ad_last_click = {}
channel_bonus_claimed = set()
referred_users = set()

# Retention tracking
user_last_active = {}
user_last_reminded = {}

async def safe_delete_message(bot, chat_id, message_id, delay_seconds: int = 5):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def is_user_member(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError:
        return False

def get_main_menu(user_id, user_name, bot_username=""):
    coins = user_coins.get(user_id, 0)
    
    caption = (
        f"💋 <b>Welcome, {user_name}!</b> 🫦\n"
        f"👤 <b>User:</b> {user_name} | 💰 <b>Balance:</b> <code>{coins} Coins</code>\n"
        f"💄 <i>Spin, watch ads, climb the leaderboard & unlock VIP treats!</i>"
    )
    
    refer_link = f"https://t.me/{bot_username}?start=ref_{user_id}" if bot_username else "https://t.me/"
    raw_share_text = (
        "🔞 <b>WATCH EXCLUSIVE 18+ UNCENSORED VIDEOS!</b> 🫦💦\n\n"
        "💋 <i>Join right now to watch hot private leaks, spicy models & secret clips!</i> 🍑🔥\n\n"
        "👉 <b>Tap here to enter VIP room:</b>"
    )
    
    encoded_url = urllib.parse.quote(refer_link)
    encoded_text = urllib.parse.quote(raw_share_text)
    official_share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"

    # বাটনগুলোর সেটআপ
    keyboard = [
        # ১ নং ওয়েবসাইট
        [
            InlineKeyboardButton("🔞 🫦 WATCH UNCENSORED 18+ 🍑 🔞", url="https://tikpic.loveup.top/")
        ],
        # ২ নং ওয়েবসাইট
        [
            InlineKeyboardButton("💋 🍒 VIP PRIVATE SHOW 🫦 💦", url="https://loveup.top/")
        ],
        # ৩ ও ৪ নং ওয়েবসাইট
        [
            InlineKeyboardButton("🔞 Hot Videos 18+ 🫦", url="https://insta.loveup.top/"),
            InlineKeyboardButton("👄 Watch Full HD 💋", url="https://whatsup.loveup.top/")
        ],
        # ৫ ও ৬ নং ওয়েবসাইট
        [
            InlineKeyboardButton("🫦 Adult Secrets 🔞", url="https://call.loveup.top/"),
            InlineKeyboardButton("🌶️ Spicy Content 👄", url="https://tikreels.loveup.top/")
        ],
        # ৭ নং ওয়েবসাইট
        [
            InlineKeyboardButton("💋 Premium Clips 👙", url="https://hotstepsis.blogspot.com/?m=1")
        ],
        # VIP বাটন
        [
            InlineKeyboardButton("👑 🔓 Unlock VIP (1000 Coins) 🫦 👑", callback_data="unlock_vip")
        ],
        # গেম ও লিডারবোর্ড
        [
            InlineKeyboardButton("🎰 🫦 Spin & Roll (3/day) 🍒", callback_data="spin_wheel"),
            InlineKeyboardButton("🏆 💋 Top 10 Earners 🔞", callback_data="leaderboard")
        ],
        # বোনাস ও শেয়ার
        [
            InlineKeyboardButton("🎁 👄 Daily Bonus (+25) 🫦", callback_data="daily_bonus"),
            InlineKeyboardButton("👥 💋 Share to Friends (+20) 🔞", url=official_share_url)
        ],
        # আলাদা আলাদা ৪টি বিজ্ঞাপন বাটন
        [
            InlineKeyboardButton("🪙 🫦 Watch Ad 1 (+10) 💋", callback_data="watch_ad_1"),
            InlineKeyboardButton("🪙 👄 Watch Ad 2 (+10) 🫦", callback_data="watch_ad_2")
        ],
        [
            InlineKeyboardButton("🪙 🌶️ Watch Ad 3 (+10) 🍑", callback_data="watch_ad_3"),
            InlineKeyboardButton("🪙 💋 Watch Ad 4 (+10) 💦", callback_data="watch_ad_4")
        ],
        # চ্যানেল জয়েনিং
        [
            InlineKeyboardButton("📢 🫦 Channel 1 💋", url=CHANNEL_1_URL),
            InlineKeyboardButton("📢 👄 Channel 2 🫦", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("✅ 💋 Verify & Claim (+50) 🫦 ✅", callback_data="claim_channel_bonus")
        ]
    ]
    
    return caption, InlineKeyboardMarkup(keyboard)

async def daily_retention_alarm_loop(app):
    await asyncio.sleep(10)
    while True:
        now = time.time()
        one_day = 86400

        for uid, last_active in list(user_last_active.items()):
            last_sent = user_last_reminded.get(uid, 0)
            if (now - last_active >= one_day) and (now - last_sent >= one_day):
                try:
                    name = user_names.get(uid, "Lover")
                    reminder_text = (
                        f"🔞 <b>Fresh 18+ VIP Clips Just Dropped!</b> 🫦💦\n\n"
                        f"Hey <b>{name}</b>, your daily rewards are waiting! 💋\n"
                        f"🎁 Claim your <b>Daily Bonus (+25 Coins)</b> & <b>Lucky Spins</b> now.\n\n"
                        f"👇 Tap below to jump straight in:"
                    )
                    bot_username = (await app.bot.get_me()).username
                    bot_link = f"https://t.me/{bot_username}?start=wake"
                    
                    btn = InlineKeyboardMarkup([
                        [InlineKeyboardButton("💋 Enter VIP Room Now 🫦", url=bot_link)]
                    ])

                    await app.bot.send_message(
                        chat_id=uid,
                        text=reminder_text,
                        parse_mode="HTML",
                        reply_markup=btn
                    )
                    user_last_reminded[uid] = now
                except Exception:
                    pass
                await asyncio.sleep(0.5)

        await asyncio.sleep(1800)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name

    user_names[user_id] = user_name
    user_last_active[user_id] = time.time()
    bot_username = (await context.bot.get_me()).username

    if context.args and len(context.args) > 0:
        referrer_str = context.args[0]
        if referrer_str.startswith("ref_"):
            try:
                referrer_id = int(referrer_str.replace("ref_", ""))
                if referrer_id != user_id and user_id not in referred_users and user_id not in user_coins:
                    referred_users.add(user_id)
                    user_coins[referrer_id] = user_coins.get(referrer_id, 0) + 20
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 <b>Referral Success!</b> A new friend joined with your link. You got <b>+20 Coins</b>! 🫦",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
            except ValueError:
                pass

    if user_id not in user_coins:
        user_coins[user_id] = 0

    caption, reply_markup = get_main_menu(user_id, user_name, bot_username)

    await update.message.reply_animation(
        animation=GIF_URL,
        caption=caption,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    user_name = user.first_name

    user_names[user_id] = user_name
    user_last_active[user_id] = time.time()
    if user_id not in user_coins:
        user_coins[user_id] = 0

    today_str = str(date.today())
    now = time.time()
    bot_username = (await context.bot.get_me()).username

    # আলাদা আলাদা ৪টি বিজ্ঞাপনের হ্যান্ডলার
    if query.data in ["watch_ad_1", "watch_ad_2", "watch_ad_3", "watch_ad_4", "watch_ad"]:
        last_ad_time = ad_last_click.get(user_id, 0)
        cooldown = 30
        if now - last_ad_time < cooldown:
            remaining = int(cooldown - (now - last_ad_time))
            await query.answer(
                text=f"⏳ Please wait {remaining} more seconds before watching another ad! 🫦",
                show_alert=True
            )
            return

        ad_last_click[user_id] = now
        user_coins[user_id] += 10
        
        # নির্দিষ্ট বাটন অনুযায়ী নির্দিষ্ট এড লিংক নির্বাচন
        ad_key = query.data.replace("watch_", "")
        selected_ad = AD_URLS.get(ad_key, AD_URLS["ad_1"])
        
        await query.answer(
            text="🎉 +10 Coins Added! Opening ad... 💋",
            show_alert=True
        )
        sent_ad_msg = await context.bot.send_message(
            chat_id=user_id,
            text=f"👉 <b>Watch your video/ad here:</b> 🫦\n🔗 <a href='{selected_ad}'>Click Here To Watch</a>\n\n<i>(This message will disappear in 10 seconds)</i>",
            parse_mode="HTML"
        )
        asyncio.create_task(safe_delete_message(context.bot, user_id, sent_ad_msg.message_id, 10))

    elif query.data == "spin_wheel":
        user_spin = spin_records.get(user_id, {"date": today_str, "count": 0})
        if user_spin["date"] != today_str:
            user_spin = {"date": today_str, "count": 0}

        if user_spin["count"] >= 3:
            await query.answer(
                text="❌ You reached your daily limit of 3 spins! Come back tomorrow. 🫦",
                show_alert=True
            )
            return

        user_spin["count"] += 1
        spin_records[user_id] = user_spin
        remaining_spins = 3 - user_spin["count"]

        await query.answer(text="🎰 Spinning the Slot Machine... 🫦")

        animation_frames = [
            "🎰 [ 🍒 | 🍇 | 🍋 ] <i>Rolling...</i> 🫦",
            "🎰 [ 💎 | 🍒 | 🔔 ] <i>Spinning...</i> 🔥",
            "🎰 [ 7️⃣ | 💎 | 🍒 ] <i>Almost stopped...</i> 💋"
        ]

        for frame in animation_frames:
            try:
                await query.edit_message_caption(
                    caption=f"{frame}\n\n⏳ <b>User:</b> {user_name} | 💰 <b>Balance:</b> {user_coins[user_id]} Coins",
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.7)
            except Exception:
                pass

        prizes = [10, 15, 20, 25, 50, 100]
        won = random.choice(prizes)
        user_coins[user_id] += won

        jackpot_tag = "🔥 <b>777 JACKPOT!</b> 🔥" if won >= 50 else "🎉 <b>YOU WON!</b> 🍒"

        result_caption = (
            f"{jackpot_tag}\n\n"
            f"🎁 <b>Prize:</b> +{won} Coins! 💋\n"
            f"🔄 <b>Remaining spins today:</b> {remaining_spins}\n\n"
            f"<i>(Refreshing menu in 3 seconds...)</i>"
        )

        try:
            await query.edit_message_caption(
                caption=result_caption,
                parse_mode="HTML"
            )
        except Exception:
            pass

        await asyncio.sleep(3)
        caption, reply_markup = get_main_menu(user_id, user_name, bot_username)
        try:
            await query.edit_message_caption(
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception:
            pass

    elif query.data == "leaderboard":
        sorted_users = sorted(user_coins.items(), key=lambda item: item[1], reverse=True)[:10]
        leaderboard_text = "🏆 <b>TOP 10 COIN EARNERS</b> 🏆\n\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        rank = 0
        for uid, coins in sorted_users:
            name = user_names.get(uid, f"User_{uid}")
            leaderboard_text += f"{medals[rank]} <b>{name}</b> — <code>{coins} Coins</code>\n"
            rank += 1

        leaderboard_text += "\n💡 <i>Invite more friends and watch ads to get on top!</i> 🫦\n\n<i>(This message will disappear in 7 seconds)</i>"
        await query.answer()
        
        leader_msg = await context.bot.send_message(
            chat_id=user_id,
            text=leaderboard_text,
            parse_mode="HTML"
        )
        asyncio.create_task(safe_delete_message(context.bot, user_id, leader_msg.message_id, 7))

    elif query.data == "daily_bonus":
        last_claimed = daily_claims.get(user_id)
        if last_claimed == today_str:
            await query.answer(
                text="⏳ You have already claimed today's bonus! Come back tomorrow. 🫦",
                show_alert=True
            )
        else:
            daily_claims[user_id] = today_str
            user_coins[user_id] += 25
            await query.answer(
                text="🎉 Congratulations! You received +25 Daily Bonus Coins! 💋",
                show_alert=True
            )
            caption, reply_markup = get_main_menu(user_id, user_name, bot_username)
            try:
                await query.edit_message_caption(
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception:
                pass

    elif query.data == "claim_channel_bonus":
        if user_id in channel_bonus_claimed:
            await query.answer(
                text="⚠️ You have already claimed your 50 Coins channel bonus! 🫦",
                show_alert=True
            )
        else:
            is_ch1 = await is_user_member(context.bot, CHANNEL_1_ID, user_id)
            is_ch2 = await is_user_member(context.bot, CHANNEL_2_ID, user_id)

            if is_ch1 and is_ch2:
                channel_bonus_claimed.add(user_id)
                user_coins[user_id] += 50
                await query.answer(
                    text="🎉 Verified! You joined all channels. +50 Coins added! 💋",
                    show_alert=True
                )
                caption, reply_markup = get_main_menu(user_id, user_name, bot_username)
                try:
                    await query.edit_message_caption(
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                except Exception:
                    pass
            else:
                await query.answer(
                    text="❌ You haven't joined both channels yet! Please join Channel 1 & Channel 2 first. 🫦",
                    show_alert=True
                )

    elif query.data == "unlock_vip":
        if user_coins[user_id] >= 1000:
            user_coins[user_id] -= 1000
            await query.answer(
                text="🔓 VIP UNLOCKED! 1000 Coins deducted. 💋",
                show_alert=True
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"👑 <b>VIP ACCESS UNLOCKED!</b> 🫦\n\n"
                    f"Here is your private VIP link:\n"
                    f"👉 <a href='{VIP_SECRET_LINK}'><b>Click Here For VIP Content</b></a>\n\n"
                    f"<i>Enjoy premium access!</i> 💋"
                ),
                parse_mode="HTML"
            )
            caption, reply_markup = get_main_menu(user_id, user_name, bot_username)
            try:
                await query.edit_message_caption(
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception:
                pass
        else:
            needed = 1000 - user_coins[user_id]
            await query.answer(
                text=f"❌ Not enough coins! You have {user_coins[user_id]} coins. Need {needed} more coins to unlock VIP (1000 Coins). 🫦",
                show_alert=True
            )

async def post_init(application):
    asyncio.create_task(daily_retention_alarm_loop(application))

if __name__ == '__main__':
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot is running...")
    app.run_polling()
