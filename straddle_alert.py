from fyers_apiv3.FyersWebsocket import data_ws
import requests
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

# -------- EMAIL (SendGrid) --------
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("EMAIL")
TO_EMAIL = os.environ.get("TO_EMAIL", "barmanparigyan@gmail.com,abhigyanbarman@gmail.com").split(",")

# -------- GLOBALS --------
ce_price = 0
pe_price = 0
last_alerted = False

# -------- FUNCTIONS --------
def get_level():
    level = os.environ.get("LEVEL")
    return float(level) if level else None

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.get(url, params={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        if response.status_code == 200:
            print("Telegram sent ✔")
        else:
            print(f"Telegram error: {response.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")

def send_email(msg):
    try:
        print(f"Attempting to send email to {TO_EMAIL}...")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        for receiver in TO_EMAIL:
            email = Mail(
                from_email=FROM_EMAIL,
                to_emails=receiver,
                subject="🚀 Straddle Alert",
                plain_text_content=msg
            )
            response = sg.send(email)
            if response.status_code == 202:
                print(f"Email sent to {receiver} ✔")
            else:
                print(f"Email error: {response.status_code}")
    except Exception as e:
        print(f"Email error: {e}")

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
                print("🚀 BREAKOUT ALERT TRIGGERED")
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
                print("🔻 BREAKDOWN ALERT TRIGGERED")
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
