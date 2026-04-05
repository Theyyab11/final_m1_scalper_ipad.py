# 🚀 VIP PRO ELITE SIGNAL BOT (TRADINGVIEW TA VERSION)

import pandas as pd
import time
import threading
from datetime import datetime
import pytz
import requests
from tradingview_ta import TA_Handler, Interval, Exchange

# ---------------- CONFIG ----------------
SCALPING_SYMBOLS = ["XAUUSD", "BTCUSD", "ETHUSD", "SOLUSD"]  # TradingView symbols
FUTURES_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
SPOT_SYMBOLS = ["ETHUSDT", "BTCUSDT", "SOLUSDT", "ADAUSDT"]

TELEGRAM_TOKEN = "8601674578:AAHycLEx-6M_r_JHFuS96oKuLTBJqefwKnk"
CHAT_ID = "992623579"  # Your personal Telegram ID

ATR_PERIOD = 14
MIN_CONFIDENCE = 90  # PRO signals only

last_signal = {}
last_sl_tp = {}
update_offset = None

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# ---------------- SESSION FILTER ----------------
def is_killzone():
    dubai = pytz.timezone("Asia/Dubai")
    hour = datetime.now(dubai).hour
    return (11 <= hour <= 14) or (16 <= hour <= 19)

# ---------------- DATA FETCH ----------------
def fetch_data(symbol, interval):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto" if "USDT" in symbol else "forex",
            exchange="BINANCE" if "USDT" in symbol else "FX_IDC",
            interval=interval
        )
        analysis = handler.get_analysis()
        # Create a simple DataFrame for last 50 closes
        df = pd.DataFrame({
            "close": analysis.indicators["close"][-50:] if "close" in analysis.indicators else [analysis.indicators["close"]],
        })
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"[FETCH ERROR] {symbol} ({interval}): {e}")
        return None

# ---------------- INDICATORS ----------------
def atr(df):
    df['high'] = df['close']  # Simplified for TradingView
    df['low'] = df['close']
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
def generate_signal(symbol, interval, label):
    df = fetch_data(symbol, interval)
    if df is None or df.empty:
        return

    atr_val = atr(df).iloc[-1]
    if pd.isna(atr_val) or atr_val == 0:
        return

    ema50 = ema(df, 50).iloc[-1]
    price = df['close'].iloc[-1]

    trend_dir = "BUY" if price > ema50 else "SELL"
    mom = momentum(df)

    confidence = 100 if mom > (0.8 * atr_val) else 90

    direction = trend_dir
    key = f"{symbol}_{label}"

    # Only send new signal if direction changed
    if last_signal.get(key) == direction:
        return

    # ENTRY ZONE
    entry_low = price - (0.2 * atr_val)
    entry_high = price + (0.2 * atr_val)

    if direction == "BUY":
        sl = price - 0.6 * atr_val
        tp = price + 1.2 * atr_val
    else:
        sl = price + 0.6 * atr_val
        tp = price - 1.2 * atr_val

    # Save last SL/TP for tracking
    last_sl_tp[key] = {'sl': sl, 'tp': tp}

    # --- CONSOLE DEBUG ---
    print(f"[SIGNAL] {symbol} ({label}) | Direction: {direction} | "
          f"Entry: {entry_low:.2f}-{entry_high:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | Confidence: {confidence}%")

    # SEND TELEGRAM
    msg = (
        f"🚀 VIP PRO SIGNAL\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📊 {symbol} ({label})\n"
        f"📍 {direction}\n"
        f"🎯 Entry Zone: {entry_low:.2f} - {entry_high:.2f}\n"
        f"🛑 SL: {sl:.2f}\n"
        f"💰 TP: {tp:.2f}\n"
        f"⚡ Confidence: {confidence}%\n"
        f"━━━━━━━━━━━━━━━"
    )
    send_telegram(msg)
    last_signal[key] = direction

# ---------------- LOOPS ----------------
def run_scalping():
    while True:
        if is_killzone():
            for s in SCALPING_SYMBOLS:
                generate_signal(s, Interval.INTERVAL_1_MINUTE, "SCALPING")
        time.sleep(60)

def run_futures():
    while True:
        for s in FUTURES_SYMBOLS:
            generate_signal(s, Interval.INTERVAL_30_MINUTES, "FUTURES")
        time.sleep(1800)

def run_spot():
    while True:
        for s in SPOT_SYMBOLS:
            generate_signal(s, Interval.INTERVAL_1_HOUR, "SPOT")
        time.sleep(3600)

# ---------------- START ----------------
if __name__ == "__main__":
    print("🚀 VIP PRO BOT RUNNING ON TRADINGVIEW TA...")

    threading.Thread(target=run_scalping, daemon=True).start()
    threading.Thread(target=run_futures, daemon=True).start()
    threading.Thread(target=run_spot, daemon=True).start()

    while True:
        time.sleep(1)
