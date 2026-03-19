from flask import Flask, request, jsonify
import os
import httpx

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Yourami Gold Bot running 24/7 ✅"})

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    try:
        # Try JSON first
        data = request.get_json(force=True, silent=True)
        
        # If not JSON, try form data or raw
        if not data:
            raw = request.data.decode('utf-8')
            print(f"Raw data received: {raw}")
            # Try to parse manually
            import json
            try:
                data = json.loads(raw)
            except:
                # TradingView sometimes sends plain text
                data = {"direction": raw, "price": 0, "symbol": "XAUUSD", "time": "now"}

        print(f"Data received: {data}")

        direction = str(data.get("direction", "")).upper()
        price     = float(data.get("price", 0))
        type_str  = str(data.get("type", ""))
        
        if "BUY" in direction or "LONG" in direction:
            direction = "BUY"
        elif "SELL" in direction or "SHORT" in direction:
            direction = "SELL"
        else:
            print(f"Unknown direction: {direction}")
            return jsonify({"status": "received", "note": "no trade signal"}), 200

        atr = price * 0.004
        sl  = round(price - atr * 1.5 if direction == "BUY" else price + atr * 1.5, 2)
        tp  = round(price + atr * 3   if direction == "BUY" else price - atr * 3,   2)

        analysis     = get_ai(direction, price, sl, tp, type_str)
        email_result = send_email(direction, price, sl, tp, analysis, type_str)

        return jsonify({"status": "ok", "direction": direction, "price": price, "email": email_result})

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"status": "ok", "note": str(e)}), 200

def get_ai(direction, price, sl, tp, type_str):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": f"XAU/USD {direction} signal ({type_str}). Price: ${price:.2f}, SL: ${sl}, TP: ${tp}. Write 3 sentences: why valid, key levels, risk warning. Be direct."}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"AI error: {e}")
        return f"{direction} XAU/USD ${price:.2f} | SL ${sl} | TP ${tp}"

def send_email(direction, price, sl, tp, analysis, type_str):
    try:
        resend_key = os.environ.get("RESEND_KEY")
        alert_email = os.environ.get("ALERT_EMAIL")

        subject = f"🎯 {direction} Signal | XAU/USD ${price:.2f}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 YOURAMI GOLD BOT
━━━━━━━━━━━━━━━━━━━━━━━━━
Direction  : {direction} ({type_str})
Entry      : ${price:.2f}
Stop Loss  : ${sl}
Take Profit: ${tp}
━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 CLAUDE AI ANALYSIS
{analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Max risk 1-2% per trade.
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
