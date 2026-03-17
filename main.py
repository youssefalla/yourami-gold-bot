from flask import Flask, request, jsonify
import anthropic, smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY")
GMAIL_SENDER  = os.environ.get("GMAIL_SENDER")
GMAIL_PASS    = os.environ.get("GMAIL_PASS")
ALERT_EMAIL   = os.environ.get("ALERT_EMAIL")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Yourami Gold Bot running 24/7 ✅"})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    direction = data.get("direction", "").upper()
    price     = float(data.get("price", 0))
    time_str  = data.get("time", str(datetime.now()))

    if "BUY" in direction or "LONG" in direction:
        direction = "BUY"
    elif "SELL" in direction or "SHORT" in direction:
        direction = "SELL"
    else:
        return jsonify({"error": "Unknown direction"}), 400

    atr   = price * 0.004
    sl    = round(price - atr * 1.5 if direction == "BUY" else price + atr * 1.5, 2)
    tp    = round(price + atr * 3   if direction == "BUY" else price - atr * 3,   2)

    analysis = get_ai(direction, price, sl, tp)
    send_email(direction, price, sl, tp, analysis, time_str)

    return jsonify({"status": "ok", "direction": direction, "price": price})

def get_ai(direction, price, sl, tp):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=350,
            messages=[{"role": "user", "content": f"""XAU/USD signal from TradingView:
Direction: {direction} | Price: ${price:.2f} | SL: ${sl} | TP: ${tp}
Strategy: EMA 20/50 + RSI + Pivot Points
3 sentences: 1) Why valid 2) Key levels 3) Risk warning. Direct, no bullets."""}]
        )
        return msg.content[0].text
    except:
        return f"{direction} XAU/USD ${price:.2f} | SL ${sl} | TP ${tp}"

def send_email(direction, price, sl, tp, analysis, time_str):
    try:
        subject = f"🎯 {direction} Signal | XAU/USD ${price:.2f}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 YOURAMI GOLD BOT
━━━━━━━━━━━━━━━━━━━━━━━━━

Direction  : {direction}
Entry      : ${price:.2f}
Stop Loss  : ${sl}
Take Profit: ${tp}
Time       : {time_str}
Source     : TradingView

━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 CLAUDE AI ANALYSIS
{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Max risk 1-2% per trade.
"""
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_SENDER
        msg["To"]      = ALERT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_SENDER, GMAIL_PASS)
            s.sendmail(GMAIL_SENDER, ALERT_EMAIL, msg.as_string())
        print(f"📧 Email sent: {direction} @ ${price:.2f}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

---

**Fichier 2: `requirements.txt`**

Click **"Add file"** → **"Create new file"** → smiyh `requirements.txt` → copy-paste:
```
flask
anthropic
gunicorn
```

---

### 2️⃣ Deploy sur Railway

1. Mchi **railway.app**
2. **"New Project"** → **"Deploy from GitHub"**
3. Select repo **"yourami-gold-bot"**
4. Wait hta يدeploy (2-3 dqayeq) ✅

---

### 3️⃣ Zid Environment Variables

F Railway → click على projet → **"Variables"** → zid had 4:
```
ANTHROPIC_KEY = sk-ant-... (jdida)
GMAIL_SENDER  = contact.yourami@gmail.com
GMAIL_PASS    = (App Password jdida)
ALERT_EMAIL   = contact.yourami@gmail.com
```

---

### 4️⃣ Generate Domain

Railway → **"Settings"** → **"Networking"** → **"Generate Domain"**

Ghadi tشوف URL bhal:
```
yourami-gold-bot-production.railway.app
