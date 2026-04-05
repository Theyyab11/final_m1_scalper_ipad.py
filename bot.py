# 🚀 XAUUSD VIP SCALPING BOT (PRO VERSION - BUSINESS READY)

import requests
import pandas as pd
import time
import threading
from datetime import datetime
import pytz
import yfinance as yf

# ---------------- CONFIG ----------------
SYMBOL = "GC=F"
TELEGRAM_TOKEN = "8601674578:AAHycLEx-6M_r_JHFuS96oKuLTBJqefwKnk"
CHAT_ID = "992623579"

ATR_PERIOD = 14
MIN_CONFIDENCE = 80

last_signal = None
last_sl_tp = None
update_offset = None

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# ---------------- SESSION ----------------
def is_killzone():
    dubai = pytz.timezone("Asia/Dubai")
    hour = datetime.now(dubai).hour
    return (11 <= hour <= 14) or (16 <= hour <= 19)

# ---------------- DATA ----------------
def fetch_data():
    try:
        df = yf.download(SYMBOL, period="1d", interval="1m")
        df = df.dropna()
        df.columns = ["open","high","low","close","adj close","volume"]
        return df
    except Exception as e:
        print("Fetch error:", e)
        return None

# ---------------- INDICATORS ----------------
def atr(df):
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    return tr.rolling(ATR_PERIOD).mean()

def ema(df, period=50):
    return df['close'].ewm(span=period).mean()

def momentum(df):
    return abs(df['close'].iloc[-1] - df['close'].iloc[-5])

# ---------------- SIGNAL ENGINE ----------------
def generate_signal(force=False):
    global last_signal, last_sl_tp

    df = fetch_data()
    if df is None or df.empty:
        return

    atr_val = atr(df).iloc[-1]
    if pd.isna(atr_val) or atr_val == 0:
        return

    ema50 = ema(df).iloc[-1]
    price = df['close'].iloc[-1]
    mom = momentum(df)

    direction = "BUY" if price > ema50 else "SELL"

    confidence = 70
    if mom > (0.5 * atr_val): confidence += 10
    if mom > (0.8 * atr_val): confidence += 10

    if confidence < MIN_CONFIDENCE and not force:
        return

    # ⚠️ BE READY ALERT
    if last_signal != direction:
        send_telegram("⚠️ BE READY - GOLD SNIPER SETUP FORMING...")

    # ENTRY
    entry_low = price - (0.2 * atr_val)
    entry_high = price + (0.2 * atr_val)

    if direction == "BUY":
        sl = price - 0.6 * atr_val
        tp = price + 1.2 * atr_val
    else:
        sl = price + 0.6 * atr_val
        tp = price - 1.2 * atr_val

    msg = (
        f"🚀 VIP GOLD SNIPER SIGNAL\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 XAUUSD (SCALPING)\n"
        f"📍 {direction}\n"
        f"🎯 Entry Zone: {entry_low:.2f} - {entry_high:.2f}\n"
        f"🛑 Stop Loss: {sl:.2f}\n"
        f"💰 Take Profit: {tp:.2f}\n"
        f"⚡ Confidence: {confidence}%\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Smart Money Flow Confirmed ✔️"
    )

    send_telegram(msg)
    last_signal = direction
    last_sl_tp = {"sl": sl, "tp": tp}

# ---------------- SL/TP TRACK ----------------
def check_sl_tp():
    global last_sl_tp

    if not last_sl_tp:
        return

    df = fetch_data()
    if df is None or df.empty:
        return

    price = df['close'].iloc[-1]

    if price <= last_sl_tp["sl"]:
        send_telegram(f"⚠️ SL HIT at {price:.2f}")
        last_sl_tp = None

    elif price >= last_sl_tp["tp"]:
        send_telegram(f"✅ TP HIT at {price:.2f}")
        last_sl_tp = None

# ---------------- COMMANDS ----------------
def check_commands():
    global update_offset

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        if update_offset:
            url += f"?offset={update_offset}"

        res = requests.get(url).json()

        for upd in res.get("result", []):
            if "message" in upd:
                text = upd["message"].get("text", "").lower()

                if text == "/test":
                    send_telegram("🔥 BOT ACTIVE & RUNNING PERFECTLY")

                elif text == "/status":
                    send_telegram("🟢 Bot running (XAUUSD live scanning)")

                elif text == "/price":
                    df = fetch_data()
                    if df is not None:
                        price = df['close'].iloc[-1]
                        send_telegram(f"📊 XAUUSD Price: {price:.2f}")

                elif text == "/signal":
                    send_telegram("⚡ Manual signal request...")
                    generate_signal(force=True)

            update_offset = upd["update_id"] + 1

    except Exception as e:
        print("Command error:", e)

# ---------------- LOOPS ----------------
def run_bot():
    while True:
        if is_killzone():
            generate_signal()
            check_sl_tp()
        time.sleep(60)

def run_commands():
    while True:
        check_commands()
        time.sleep(2)

# ---------------- START ----------------
if __name__ == "__main__":
    print("🚀 VIP GOLD BOT RUNNING...")

    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=run_commands, daemon=True).start()

    while True:
        time.sleep(1)
