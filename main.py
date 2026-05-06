import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# Power Automate HTTP trigger URL
POWER_AUTOMATE_URL = os.environ.get(
    "POWER_AUTOMATE_URL",
    "https://defaultf0afb5868cc040ebbbd15496432980.b8.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e6fb22158dc54f2ba8f143a68378f060/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Nrg0ELiCwDE4Cwq7Iakw8yv88R9nr40GB7OaX14ZFe4"
)


def analyze_startup(startup_name):
    """The 'Skeptic' Brain — this is where your AI/scraping logic will go."""
    red_flags = [
        "Burn rate is 4x revenue.",
        "No proprietary IP.",
        "Founder was previously sued for fraud."
    ]
    score = "1/10"
    return score, red_flags


def build_adaptive_card(startup_name, score, red_flags):
    """Build an Adaptive Card payload for Teams."""
    red_flags_text = "\n\n".join(f"{i+1}. {flag}" for i, flag in enumerate(red_flags))

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Large",
                            "weight": "Bolder",
                            "text": "🔍 Skeptic Bot Report"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**Startup:** {startup_name}",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**Score:** {score}",
                            "wrap": True,
                            "color": "Attention"
                        },
                        {
                            "type": "TextBlock",
                            "text": "**Red Flags:**",
                            "weight": "Bolder",
                            "spacing": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": red_flags_text,
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }


@app.get("/")
async def health():
    return {"status": "Skeptic Bot is alive 🔍"}


@app.post("/webhook")
async def teams_webhook(request: Request):
    """Receive a startup name, analyze it, and send result to Teams via Power Automate."""
    data = await request.json()

    # Debug: log full payload
    print(f"📦 Full payload: {data}")

    # Try multiple possible field names from Power Automate
    startup_name = (
        data.get("startup_name")
        or data.get("messageText")
        or data.get("text")
        or data.get("message")
        or str(data)
    )

    # Strip /analyze prefix if present
    if "/analyze" in startup_name:
        startup_name = startup_name.split("/analyze", 1)[-1].strip()

    if not startup_name:
        startup_name = "Unknown Startup"

    print(f"📩 Received request to analyze: {startup_name}")

    # Analyze
    score, red_flags = analyze_startup(startup_name)

    # Build and send Adaptive Card to Teams
    payload = build_adaptive_card(startup_name, score, red_flags)
    response = requests.post(POWER_AUTOMATE_URL, json=payload)

    if response.status_code == 202:
        print(f"✅ Report for '{startup_name}' sent to Teams.")
        return {"status": "success", "startup": startup_name, "score": score}
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return {"status": "error", "code": response.status_code, "detail": response.text}