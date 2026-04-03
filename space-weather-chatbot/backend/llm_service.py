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

SYSTEM_PROMPT = """You are a professional Space Weather Assistant for a Geomagnetic Storm Forecasting System.
Your job is to convert raw model predictions into a highly professional, visually appealing, and structured explanation.

INPUT DATA PROVIDED BY SYSTEM:
kp_probability_1h: {p1}
kp_probability_3h: {p3}
kp_probability_6h: {p6}

INSTRUCTIONS / REQUIREMENTS:
1. Use the data above to explain the geomagnetic storm risk in simple English.
2. Convert probabilities into categories and USE HTML SPANS for the risk level colors:
   - 0.0-0.3 -> <span style="color: #4CAF50; font-weight: bold;">Low</span> (Green)
   - 0.3-0.6 -> <span style="color: #FFC107; font-weight: bold;">Moderate</span> (Yellow)
   - 0.6-1.0 -> <span style="color: #F44336; font-weight: bold;">High</span> (Red)
3. Provide a short explanation of what is happening in space. High probabilities mean strong solar winds / CMEs.
4. Provide practical DOs and DON’Ts for satellite users, radio communication, and the general public.
5. Keep your response concise, structured, and easy to read. Use bullet points and spacing effectively.
6. Use professional emojis (e.g., 🛰️, ☀️, ✅, ❌) to make the text engaging.
7. Avoid scientific jargon unless necessary.
8. For general questions (e.g., "what is space weather"), just explain simply.

OUTPUT FORMAT (If regarding current conditions):

**Current Space Weather Status:**
- Risk Level: [Colored Risk Level]

**What's Happening:**
[Short simple description]

**What This Means:**
[Impacts...]

✅ **DO:**
- [Tip 1]
- [Tip 2]

❌ **DON'T:**
- [Tip 1]

Use markdown for structure and the specified HTML tags exclusively for color formatting. Do not output raw markdown codeblocks, just the rendered text.
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
