from pydoc import text
import pyaudio
import wave
from faster_whisper import WhisperModel
import os
from groq import Groq
import edge_tts
import asyncio
from playsound import playsound
import numpy as np

# Set up audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # CD-quality audio
CHUNK = 1024
RECORD_SECONDS = 5
OUTPUT_FILENAME = "output.mp3"

# Silence detection config
SILENCE_THRESHOLD = 500  # Lower means more sensitive
SILENCE_DURATION = 4  # Seconds of silence before stopping

model = WhisperModel("tiny")

GROQ_API_KEY = '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'

if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

def is_silent(data):
    """ Returns True if the audio data is below the silence threshold. """
    return np.abs(np.frombuffer(data, np.int16)).mean() < SILENCE_THRESHOLD

def record_until_silence():
    frames = []
    silence_count = 0
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    os.system("clear")
    print("Fale sua pergunta agora... Threshold de silêncio: %d segundos" % SILENCE_DURATION)

    while True:
        data = stream.read(CHUNK)
        frames.append(data)

        if is_silent(data):
            silence_count += 1
        else:
            silence_count = 0

        # Stop recording if silence lasts long enough
        if silence_count > (SILENCE_DURATION * RATE / CHUNK):
            print("Speech ended.")
            break

    # Clean up
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio (optional)
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print("Audio saved")

while True:
    botao = input("Pressione enter para fazer sua pergunta")
    if botao == "exit":
        break
    record_until_silence()
    print("Waiting for answer")

    segments, info = model.transcribe("output.mp3", language="pt")
    transcription_text = "Responda em português. " + " ".join([segment.text for segment in segments])

    print(transcription_text)
    #for segment in segments:
    #    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[
            {
                "role": "user",
                "content": transcription_text
            }
        ]
    )

    parts = completion.choices[0].message.content.split("</think>")
    clean_text = parts[1].replace("*", "")
    #print(clean_text)
    async def text_to_speech():
        rate = "+30%"  # Increase speed by 30%
        volume = "-80%"  # Slight volume boost
        voice = "pt-BR-FranciscaNeural"  # You can change the voice model
        output_file = "voz.mp3"

        # Create the TTS object and save the output as an MP3 file
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate, volume=volume)
        await communicate.save(output_file)

        #print("Speech saved to:", output_file)

    # Run the async function
    asyncio.run(text_to_speech())
    os.system("play voz.mp3")
    os.system("clear")
