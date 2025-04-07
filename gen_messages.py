import openai
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

load_dotenv(dotenv_path=".env.local")


dotenv_path = os.path.join(os.path.dirname(__file__), ".env.local")
load_dotenv(dotenv_path=dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("[DEBUG] Loaded OPENAI_API_KEY:", OPENAI_API_KEY[:10] if OPENAI_API_KEY else "NOT FOUND")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found!")

def generate_fake_convo(names=("Alice", "You"), n_messages=20, style="light and funny", prompt=None):
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not found! Please set your API key in one of two ways:\n"
            "1. Set the OPENAI_API_KEY environment variable:\n"
            "   Windows: set OPENAI_API_KEY=your-api-key-here\n"
            "   Linux/Mac: export OPENAI_API_KEY=your-api-key-here\n"
            "2. Or modify this code to directly set the API key:\n"
            "   openai.api_key = 'your-api-key-here'"
        )

    openai.api_key = api_key
    current_time = datetime.now()

    # Create system prompt with optional user prompt
    system_prompt = f"""
    You are simulating a text message conversation between two people named {names[0]} and {names[1]}.
    Write a back-and-forth chat with {n_messages} messages total.
    Keep the tone {style}.
    """

    if prompt:
        system_prompt += f"\nThe conversation should be about: {prompt}"

    system_prompt += """
    Format it as a JSON list of dicts like this:
    [{"sender": "Alice", "text": "Hey!"}, ...]
    Only return the JSON. Do not include explanations or markdown.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.9
    )

    try:
        convo_data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise ValueError("OpenAI did not return valid JSON.")

    # Add timestamps
    convo = []
    for msg in convo_data:
        current_time += timedelta(minutes=1)
        convo.append({
            "sender": msg["sender"],
            "text": msg["text"],
            "time": current_time.strftime("%I:%M %p")
        })

    return convo
