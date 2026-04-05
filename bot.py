# 🚀 XAUUSD VIP SCALPING BOT (REAL MARKET - STABLE VERSION)

import requests
import pandas as pd
import time
import threading
from datetime import datetime
import pytz
import yfinance as yf

# ---------------- CONFIG ----------------
SYMBOL = "GC=F"   # Gold Futures (XAUUSD)
TELEGRAM_TOKEN = "8601674578:AAHycLEx-6M_r_JHFuS96oKuLTBJqefwKnk"
CHAT_ID = "992623579"

ATR_PERIOD = 14
MIN_CONFIDENCE = 80

last_signal = None
last_sl_tp = None

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
def generate_signal():
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

    if confidence < MIN_CONFIDENCE:
        return

    # 🚨 BE READY ALERT
    if last_signal != direction:
        send_telegram("⚠️ BE READY - GOLD SETUP FORMING...")

    # ENTRY
    entry_low = price - (0.2 * atr_val)
    entry_high = price + (0.2 * atr_val)

    if direction == "BUY":
        sl = price - 0.6 * atr_val
        tp = price + 1.2 * atr_val
    else:
        sl = price + 0.6 * atr_val
        tp = price - 1.2 * atr_val

    # SEND SIGNAL
    msg = (
        f"🚀 VIP GOLD SCALPING SIGNAL\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 XAUUSD (1M)\n"
        f"📍 {direction}\n"
        f"🎯 Entry: {entry_low:.2f} - {entry_high:.2f}\n"
        f"🛑 SL: {sl:.2f}\n"
        f"💰 TP: {tp:.2f}\n"
        f"⚡ Confidence: {confidence}%\n"
        f"━━━━━━━━━━━━━━━"
    )

    send_telegram(msg)
    last_signal = direction
    last_sl_tp = {"sl": sl, "tp": tp}

# ---------------- LOOP ----------------
def run_bot():
    while True:
        if is_killzone():
            generate_signal()
        time.sleep(60)

# ---------------- START ----------------
if __name__ == "__main__":
    print("🚀 GOLD SCALPING BOT RUNNING...")
    run_bot()
