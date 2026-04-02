from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=api_key or "prevent_crash_dummy_key",
    base_url="https://api.groq.com/openai/v1",
    timeout=15.0
)

SYSTEM_PROMPT = """You are a Space Weather Assistant for a Geomagnetic Storm Forecasting System.
Your job is to convert raw model predictions into simple, clear, human-friendly explanations.

INPUT DATA PROVIDED BY SYSTEM:
kp_probability_1h: {p1}
kp_probability_3h: {p3}
kp_probability_6h: {p6}

INSTRUCTIONS / REQUIREMENTS:
1. If the user asks about space weather, use the data above to explain the geomagnetic storm risk in simple English (non-technical).
2. Convert probabilities into categories:
   - 0.0-0.3 -> Low Risk
   - 0.3-0.6 -> Moderate Risk
   - 0.6-1.0 -> High Risk
3. Give a short explanation of what is happening in space based on the probabilities. High probabilities mean strong solar winds / CMEs interacting with Earth.
4. Provide practical DOs and DON’Ts for satellite users, radio communication, and general public.
5. Keep your entire response short (5-8 lines max).
6. Be calm, informative, and slightly conversational.
7. Avoid scientific jargon unless necessary.
8. If the user asks general questions (e.g., "what is space weather"), explain simply, ignoring current probabilities.

OUTPUT FORMAT (If regarding current conditions):
Current Space Weather Status:
- Risk Level: [Low/Moderate/High]

What's happening:
- [Short simple description]

What this means:
- [Impacts...]

Do:
- [Tip 1]
- [Tip 2]

Don't:
- [Tip 1]

Always prioritize clarity over technical accuracy. Do not use markdown for headers, just use bolding or plain text.
"""

def generate_chat_response(user_message: str, prediction_data: dict) -> str:

    # Inject real-time predictions into the System Prompt
    sys_prompt = SYSTEM_PROMPT.format(
        p1=prediction_data.get("kp_probability_1h", 0.0),
        p3=prediction_data.get("kp_probability_3h", 0.0),
        p6=prediction_data.get("kp_probability_6h", 0.0)
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Warning: LLM API error: {e}"
