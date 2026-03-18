from flask import Flask, request, jsonify
import os
import httpx

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Yourami Gold Bot running 24/7 ✅"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No data"}), 400

        direction = str(data.get("direction", "")).upper()
        price = float(data.get("price", 0))

        if "BUY" in direction or "LONG" in direction:
            direction = "BUY"
        elif "SELL" in direction or "SHORT" in direction:
            direction = "SELL"
        else:
            return jsonify({"error": "Unknown direction"}), 400

        atr = price * 0.004
        sl = round(price - atr * 1.5 if direction == "BUY" else price + atr * 1.5, 2)
        tp = round(price + atr * 3 if direction == "BUY" else price - atr * 3, 2)

        analysis = get_ai(direction, price, sl, tp)
        email_result = send_email(direction, price, sl, tp, analysis)

        return jsonify({
            "status": "ok",
            "direction": direction,
            "price": price,
            "sl": sl,
            "tp": tp,
            "email": email_result
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

def get_ai(direction, price, sl, tp):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": f"XAU/USD {direction} signal. Price: ${price:.2f}, SL: ${sl}, TP: ${tp}. Write 3 sentences: why valid, key levels, risk warning. Be direct."}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"AI error: {e}")
        return f"{direction} XAU/USD ${price:.2f} | SL ${sl} | TP ${tp}"

def send_email(direction, price, sl, tp, analysis):
    try:
        resend_key = os.environ.get("RESEND_KEY")
        alert_email = os.environ.get("ALERT_EMAIL")

        subject = f"🎯 {direction} Signal | XAU/USD ${price:.2f}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 YOURAMI GOLD BOT
━━━━━━━━━━━━━━━━━━━━━━━━━
Direction  : {direction}
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

        print(f"Resend response: {response.status_code} — {response.text}")
        if response.status_code == 200 or response.status_code == 201:
            return "sent ✅"
        else:
            return f"failed: {response.text}"

    except Exception as e:
        print(f"Email error: {e}")
        return f"failed: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
