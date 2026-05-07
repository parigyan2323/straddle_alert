from fyers_apiv3.FyersWebsocket import data_ws
import requests
import smtplib
from email.mime.text import MIMEText
import os

# -------- CONFIG --------
CLIENT_ID = os.environ.get("CLIENT_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
FULL_TOKEN = CLIENT_ID + ":" + ACCESS_TOKEN

# -------- USER INPUT --------
expiry_day = os.environ.get("EXPIRY_DAY", "12")
expiry_month = os.environ.get("EXPIRY_MONTH", "05")
expiry_year = os.environ.get("EXPIRY_YEAR", "26")
strike = os.environ.get("STRIKE", "24200")

# -------- SYMBOL BUILD --------
expiry_code = expiry_year + str(int(expiry_month)) + expiry_day
CE_SYMBOL = f"NSE:NIFTY{expiry_code}{strike}CE"
PE_SYMBOL = f"NSE:NIFTY{expiry_code}{strike}PE"
SYMBOLS = [CE_SYMBOL, PE_SYMBOL]
print("\nUsing Symbols:")
print(CE_SYMBOL)
print(PE_SYMBOL)

# -------- TELEGRAM --------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# -------- EMAIL --------
EMAIL = os.environ.get("EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
TO_EMAIL = ["barmanparigyan@gmail.com", "abhigyanbarman@gmail.com"]

# -------- GLOBALS --------
ce_price = 0
pe_price = 0
last_alerted = False

# -------- FUNCTIONS --------
def get_level():
    level = os.environ.get("level")
    return float(level) if level else None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

def send_email(msg):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        for receiver in TO_EMAIL:
            message = MIMEText(msg)
            message["Subject"] = "🚀 Straddle Alert"
            message["From"] = EMAIL
            message["To"] = receiver
            server.sendmail(EMAIL, receiver, message.as_string())
        server.quit()
        print("Email sent ✔")
    except Exception as e:
        print("Email error:", e)

# -------- WEBSOCKET --------
def onmessage(msg):
    global ce_price, pe_price, last_alerted
    if 'ltp' not in msg:
        return
    symbol = msg['symbol']
    price = msg['ltp']
    if "CE" in symbol:
        ce_price = price
    elif "PE" in symbol:
        pe_price = price
    if ce_price and pe_price:
        combined = ce_price + pe_price
        level = get_level()
        print(f"Combined: {combined} | Level: {level}")
        if level:
            # 🚀 BREAKOUT
            if combined > level and not last_alerted:
                alert_msg = (
                    f"🚀 Straddle Breakout\n\n"
                    f"Strike : {strike}\n"
                    f"Expiry Date : {expiry_day} {expiry_month} 20{expiry_year}\n\n"
                    f"Stoploss Level : {level}\n\n"
                    f"Combined: {round(combined,2)}\n"
                    f"CE: {ce_price} | PE: {pe_price}"
                )
                send_telegram(alert_msg)
                send_email(alert_msg)
                last_alerted = True
            # 🔻 BREAKDOWN
            elif combined < level and last_alerted:
                alert_msg = (
                    f"🔻 Straddle Breakdown\n\n"
                    f"Strike : {strike}\n"
                    f"Expiry Date : {expiry_day} {expiry_month} 20{expiry_year}\n\n"
                    f"Stoploss Level : {level}\n\n"
                    f"Combined: {round(combined,2)}\n"
                    f"CE: {ce_price} | PE: {pe_price}"
                )
                send_telegram(alert_msg)
                send_email(alert_msg)
                last_alerted = False

def onopen():
    print("\nConnected to Fyers WebSocket")
    fyers.subscribe(symbols=SYMBOLS, data_type="SymbolUpdate")
    fyers.keep_running()

def onerror(msg):
    print("Error:", msg)

def onclose(msg):
    print("Connection closed:", msg)

# -------- START --------
fyers = data_ws.FyersDataSocket(
    access_token=FULL_TOKEN,
    on_connect=onopen,
    on_message=onmessage,
    on_error=onerror,
    on_close=onclose,
    reconnect=True
)
fyers.connect()