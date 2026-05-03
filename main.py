import os
import random
import time
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# DATABASE (in-memory)
# =========================

users = {}
pending_payments = {}

# =========================
# PLANS
# =========================

PLANS = {
    "monthly": {"price": 80, "duration": 30},
    "2weeks": {"price": 40, "duration": 14}
}

USDT_WALLET = "TA58ytiG9JLREiuyKWLXYmn3Zb17QBdsyE"
BTC_WALLET = "bc1qke9tt3kynst45hsak2rh9aesru4j44fpr2xp4w"

# =========================
# CHECK ACCESS
# =========================

def is_active(user_id):
    if user_id in users:
        return users[user_id]["expiry"] > time.time()
    return False

# =========================
# START + NUMBER VERIFICATION
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton("Share Phone Number", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    await update.message.reply_text(
        "Welcome to Gateway Tool 🔐\n\nPlease verify your number:",
        reply_markup=keyboard
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact

    if contact.user_id != update.effective_user.id:
        await update.message.reply_text("Please share your own number.")
        return

    users[update.effective_user.id] = {
        "phone": contact.phone_number,
        "expiry": 0
    }

    await update.message.reply_text("✅ Verified! Use /subscribe")

# =========================
# SUBSCRIPTION
# =========================

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose plan:\n\n"
        "/monthly - $80\n"
        "/two_weeks - $40"
    )

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan"] = "monthly"

    await update.message.reply_text(
        "💳 Pay using:\n\n"
        f"USDT (TRC20):\n{USDT_WALLET}\n\n"
        f"BTC:\n{BTC_WALLET}\n\n"
        "Then send: /paid TXID"
    )

async def two_weeks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["plan"] = "2weeks"

    await update.message.reply_text(
        "💳 Pay using:\n\n"
        f"USDT (TRC20):\n{USDT_WALLET}\n\n"
        f"BTC:\n{BTC_WALLET}\n\n"
        "Then send: /paid TXID"
    )

# =========================
# PAYMENT SUBMISSION
# =========================

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    txid = context.args[0] if context.args else None

    if not txid:
        await update.message.reply_text("Usage: /paid TXID")
        return

    plan = context.user_data.get("plan")

    if not plan:
        await update.message.reply_text("Choose a plan first.")
        return

    pending_payments[user_id] = {
        "txid": txid,
        "plan": plan
    }

    await update.message.reply_text("Payment submitted. Await approval.")

# =========================
# ADMIN APPROVAL
# =========================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = int(context.args[0])

    if user_id not in pending_payments:
        await update.message.reply_text("No payment found.")
        return

    plan = pending_payments[user_id]["plan"]
    duration = PLANS[plan]["duration"]

    users[user_id]["expiry"] = time.time() + (duration * 86400)

    await update.message.reply_text("User approved ✅")

# =========================
# TOOL FEATURES
# =========================

def simulate_payment(amount):
    return {
        "amount": amount,
        "status": random.choice(["SUCCESS", "FAILED", "PENDING"]),
        "txid": random.randint(100000, 999999)
    }

async def test_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_active(update.effective_user.id):
        await update.message.reply_text("Access denied.")
        return

    try:
        amount = context.args[0]
        result = simulate_payment(amount)

        await update.message.reply_text(
            f"🧪 Result\nAmount: {result['amount']}\n"
            f"Status: {result['status']}\nTxID: {result['txid']}"
        )
    except:
        await update.message.reply_text("Usage: /test_payment 100")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_active(update.effective_user.id):
        await update.message.reply_text("Not active.")
        return

    await update.message.reply_text(
        "📊 Gateway Tool\n\n/test_payment\n/docs"
    )

async def docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/test_payment amount\n/dashboard"
    )

# =========================
# BOT SETUP
# =========================

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

app.add_handler(CommandHandler("subscribe", subscribe))
app.add_handler(CommandHandler("monthly", monthly))
app.add_handler(CommandHandler("two_weeks", two_weeks))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("approve", approve))

app.add_handler(CommandHandler("test_payment", test_payment))
app.add_handler(CommandHandler("dashboard", dashboard))
app.add_handler(CommandHandler("docs", docs))

app.run_polling()
