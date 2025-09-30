
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)
kik_audio = "test_data/swahili2.mp3"
swahili_audios = [
    "test_data/swahili2.mp3",
    "test_data/swahilitz.mp3"
]
for filename in [kik_audio] + swahili_audios:
    print(f"Transcribing {filename}...")
    with open(filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
        )
        print(transcription)

      