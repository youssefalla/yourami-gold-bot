from flask import Flask, request, jsonify
import os
import httpx
import json

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Yourami Gold Bot running 24/7 ✅"})

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    try:
        # Try JSON first
        data = request.get_json(force=True, silent=True)

        # If not JSON, try raw
        if not data:
            raw = request.data.decode('utf-8')
            print(f"Raw data received: {raw}")
            try:
                data = json.loads(raw)
            except:
                data = {"direction": raw, "price": 0, "symbol": "XAUUSD", "time": "now"}

        print(f"Data received: {data}")

        direction = str(data.get("direction", "")).upper()
        price     = float(data.get("price", 0))
        type_str  = str(data.get("type", ""))
        rsi_val   = data.get("rsi", "N/A")
        ict_val   = data.get("ict", "N/A")

        if "BUY" in direction or "LONG" in direction:
            direction = "BUY"
        elif "SELL" in direction or "SHORT" in direction:
            direction = "SELL"
        else:
            print(f"Unknown direction: {direction}")
            return jsonify({"status": "received", "note": "no trade signal"}), 200

        # ── Use SL/TP from Pine Script if available ──
        sl = float(data.get("sl", 0))
        tp = float(data.get("tp", 0))

        # Fallback ila Pine mabewsathomch
        if sl == 0 or tp == 0:
            atr = price * 0.004
            sl  = round(price - atr * 1.5 if direction == "BUY" else price + atr * 1.5, 2)
            tp  = round(price + atr * 3   if direction == "BUY" else price - atr * 3,   2)

        analysis     = get_ai(direction, price, sl, tp, type_str, rsi_val, ict_val)
        email_result = send_email(direction, price, sl, tp, analysis, type_str, rsi_val, ict_val)

        return jsonify({"status": "ok", "direction": direction, "price": price, "sl": sl, "tp": tp, "email": email_result})

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"status": "ok", "note": str(e)}), 200

def get_ai(direction, price, sl, tp, type_str, rsi_val, ict_val):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=350,
            messages=[{"role": "user", "content": f"""XAU/USD {direction} signal detected:
Type: {type_str}
Price: ${price:.2f}
Stop Loss: ${sl}
Take Profit: ${tp}
RSI: {rsi_val}
ICT Confluence Score: {ict_val}/4

Write 3 sentences:
1) Why this setup is valid based on RSI and ICT score
2) Key price levels to watch
3) Risk warning

Be direct and professional."""}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"AI error: {e}")
        return f"{direction} XAU/USD ${price:.2f} | SL ${sl} | TP ${tp}"

def send_email(direction, price, sl, tp, analysis, type_str, rsi_val, ict_val):
    try:
        resend_key  = os.environ.get("RESEND_KEY")
        alert_email = os.environ.get("ALERT_EMAIL")

        rr = round(abs(tp - price) / abs(price - sl), 1) if abs(price - sl) > 0 else 0

        subject = f"🎯 {direction} Signal | XAU/USD ${price:.2f}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 YOURAMI GOLD BOT
━━━━━━━━━━━━━━━━━━━━━━━━━
Direction   : {direction} ({type_str})
Entry       : ${price:.2f}
Stop Loss   : ${sl}
Take Profit : ${tp}
R:R Ratio   : 1:{rr}
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SIGNAL DETAILS
RSI         : {rsi_val}
ICT Score   : {ict_val}/4
━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 CLAUDE AI ANALYSIS
{analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Max risk 1-2% per trade.
Yourami Gold Bot — powered by Claude AI
"""
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Yourami Gold Bot <onboarding@resend.dev>",
                "to": [alert_email],
                "subject": subject,
                "text": body
            },
            timeout=30
        )
        print(f"Email result: {response.status_code}")
        return "sent ✅" if response.status_code in [200, 201] else f"failed: {response.text}"
    except Exception as e:
        print(f"Email error: {e}")
        return f"failed: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
