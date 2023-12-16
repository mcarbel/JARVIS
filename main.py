import os
from os import PathLike
import asyncio
from dotenv import load_dotenv
from typing import List, Optional, TypeVar, Union, IO

import openai
from deepgram import Deepgram
from gtts import gTTS
import pygame
from pygame import mixer
import elevenlabs

from record import SpeechToText


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))
RECORDING_PATH = "wavs/recording.wav"

gpt_client = openai.Client(api_key=OPENAI_API_KEY)
context = "You are Jarvis, Alex's helpful and witty assistant. Your answers should be limited to 1-2 short sentences."

mixer.init()


def request_gpt(prompt: str) -> str:
    """
    Send a prompt to the GPT-3 API and return the response.

    Args:
        - state: The current state of the app.
        - prompt: The prompt to send to the API.

    Returns:
        The response from the API.
    """
    response = gpt_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content


async def transcribe(
    file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
):
    """
    Transcribe audio using Deepgram API.

    Args:
        - file_name: The name of the file to transcribe.

    Returns:
        The response from the API.
    """
    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = await deepgram.transcription.prerecorded(source)
        return response["results"]["channels"][0]["alternatives"][0]["words"]


if __name__ == "__main__":
    while True:
        # Record audio
        print("Listening...", end="")
        SpeechToText()
        # Transcribe audio
        print("Transcribing...")
        deepgram = Deepgram(DEEPGRAM_API_KEY)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        # Get response from GPT-3
        print("Generating response...")
        context += f"\nAlex: {string_words}\nJarvis: "
        response = request_gpt(context)
        context += response
        # Convert response to audio
        print("Converting to audio...")
        audio = elevenlabs.generate(
            text=response, voice="Adam", model="eleven_monolingual_v1"
        )
        elevenlabs.save(audio, "wavs/response.wav")
        # Play response
        print("Speaking...")
        sound = mixer.Sound("wavs/response.wav")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USER: {string_words}\n --- JARVIS: {response}\n")