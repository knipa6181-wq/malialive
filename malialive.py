import os
import asyncio
import random
import time
import urllib.parse
from datetime import datetime, date
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# আপডেট করা বট টোকেন
BOT_TOKEN = "8696806053:AAG33XwHl_RNFW7v3VED--eACneGDdXOxfo"

AD_URLS = [
    "https://example.com/your-adsterra-direct-link-1",
    "https://example.com/your-adsterra-direct-link-2",
    "https://example.com/your-adsterra-direct-link-3",
    "https://example.com/your-monetag-direct-link-4"
]

# আপডেট করা চ্যানেলের আইডি এবং লিংক
CHANNEL_1_ID = "@sofiya7298"
CHANNEL_2_ID = "@malina7228"
CHANNEL_1_URL = "https://t.me/sofiya7298"
CHANNEL_2_URL = "https://t.me/malina7228"

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

# --- Built-in Lightweight HTTP Server ---
async def handle_client(reader, writer):
    try:
        await reader.read(1024)
        body = b"Bot is alive!"
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n"
            b"Connection: close\r\n"
            b"\r\n" + body
        )
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    logger.info(f"Built-in HTTP server running on port {port}")
    asyncio.create_task(server.serve_forever())

# --- Helper Functions ---
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

    keyboard = [
        [
            InlineKeyboardButton("🔞 🫦 WATCH UNCENSORED 18+ 🍑 🔞", url=CHANNEL_1_URL)
        ],
        [
            InlineKeyboardButton("💋 🍒 VIP PRIVATE SHOW 🫦 💦", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("🔞 Hot Videos 18+ 🫦", url=CHANNEL_1_URL),
            InlineKeyboardButton("👄 Watch Full HD 💋", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("🫦 Adult Secrets 🔞", url=CHANNEL_1_URL),
            InlineKeyboardButton("🌶️ Spicy Content 👄", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("💋 Premium Clips 🍑", url=CHANNEL_1_URL),
            InlineKeyboardButton("🫦 Private Leaks 💦", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("👑 🔓 Unlock VIP (1000 Coins) 🫦 👑", callback_data="unlock_vip")
        ],
        [
            InlineKeyboardButton("🎰 🫦 Spin & Roll (3/day) 🍒", callback_data="spin_wheel"),
            InlineKeyboardButton("🏆 💋 Top 10 Earners 🔞", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("🎁 👄 Daily Bonus (+25) 🫦", callback_data="daily_bonus"),
            InlineKeyboardButton("👥 💋 Share to Friends (+20) 🌶️", url=official_share_url)
        ],
        [
            InlineKeyboardButton("🪙 🫦 Watch Ad (+10) 💋", callback_data="watch_ad"),
            InlineKeyboardButton("🪙 👄 Watch Ad (+10) 🫦", callback_data="watch_ad")
        ],
        [
            InlineKeyboardButton("🪙 🌶️ Watch Ad (+10) 🍑", callback_data="watch_ad"),
            InlineKeyboardButton("🪙 💋 Watch Ad (+10) 💦", callback_data="watch_ad")
        ],
        [
            InlineKeyboardButton("📢 🫦 Channel 1 💋", url=CHANNEL_1_URL),
            InlineKeyboardButton("📢 👄 Channel 2 🫦", url=CHANNEL_2_URL)
        ],
        [
            InlineKeyboardButton("✅ 💋 Verify & Claim (+50) 🫦 ✅", callback_data="claim_channel_bonus")
        ]
    ]
    
    return caption, InlineKeyboardMarkup(keyboard)

# Retention Alarm
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

    if query.data == "watch_ad":
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
        selected_ad = random.choice(AD_URLS)
        
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
    await start_web_server()
    asyncio.create_task(daily_retention_alarm_loop(application))

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot is starting...")
    app.run_polling()
