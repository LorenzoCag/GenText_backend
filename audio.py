import os
from openai import OpenAI
from dotenv import load_dotenv
import httpx

load_dotenv(".env.local")  # Load the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Create a custom HTTP client without proxy settings
http_client = httpx.Client(
    base_url="https://api.openai.com/v1",
    headers={"Authorization": f"Bearer {api_key}"},
    follow_redirects=True,
    timeout=30.0,
)

# Initialize OpenAI client with the custom HTTP client
client = OpenAI(
    api_key=api_key,
    http_client=http_client
)

def generate_voice_clips(convo, output_subdir="output/audio", user_voice="nova", other_voice="shimmer", model="tts-1"):
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, output_subdir)

    os.makedirs(output_dir, exist_ok=True)

    paths = []

    for i, msg in enumerate(convo):
        text = msg["text"]
        sender = msg["sender"]

        # Choose voice based on sender
        voice = user_voice if sender.lower() == "you" else other_voice

        output_path = os.path.join(output_dir, f"line_{i:03}.mp3")

        print(f"[INFO] Generating voice for '{sender}' (voice='{voice}')...")
        try:
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            response.stream_to_file(output_path)
            print(f"Saved to {output_path}")
            paths.append(output_path)
        except Exception as e:
            print(f"Skipping line {i} due to error: {e}")

    return paths
