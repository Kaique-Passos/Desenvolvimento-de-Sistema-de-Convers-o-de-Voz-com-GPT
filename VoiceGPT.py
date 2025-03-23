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
import time
import subprocess

activation_words = ["computador", "computada","computado" ]

# Set up audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # CD-quality audio
CHUNK = 1024
OUTPUT_FILENAME = "output.mp3"

# Silence detection config
SILENCE_THRESHOLD = 500  # Lower means more sensitive
#SILENCE_DURATION = 3  # Seconds of silence before stopping

model = WhisperModel("tiny")

GROQ_API_KEY = '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'

if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

def is_silent(data):
    """ Returns True if the audio data is below the silence threshold. """
    return np.abs(np.frombuffer(data, np.int16)).mean() < SILENCE_THRESHOLD


                                # GRAVAÇÃO DE ÁUDIO
def record_until_silence(silence_duration):
    frames = []
    silence_count = 0
    while True:
        data = stream.read(CHUNK)
        frames.append(data)

        if is_silent(data):
            silence_count += 1
        else:
            silence_count = 0

        # Stop recording if silence lasts long enough
        if silence_count > (silence_duration * RATE / CHUNK):
            #print("Speech ended.")
            break

    # Save the recorded audio (optional)
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

while True:
    audio = pyaudio.PyAudio()
    os.system("clear")
    print("Diga computador para ativar o assistente")
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    data = stream.read(CHUNK)
    while(True):
        data = stream.read(CHUNK)
        if( is_silent(data)):
            pass
        else:
            record_until_silence(1)
            segments, info = model.transcribe("output.mp3", language="pt")
            requisition_text = "palavra" + " ".join([segment.text for segment in segments])
            #print(requisition_text)
            if any(word in requisition_text for word in activation_words):
                #print(requisition_text)
                break
    
    print("Olá, Como posso ajudar? faça sua pergunta")
    record_until_silence(4)
    print("Aguardando resposta da API.")

    start_whisper_time = time.time()
    segments, info = model.transcribe("output.mp3", language="pt")
    transcription_text = "Responda em português. " + " ".join([segment.text for segment in segments])
    end_whisper_time = time.time()
    whisper_elapsed_time = end_whisper_time - start_whisper_time
    #print(f"Tempo entre pergunta e resposta: {whisper_elapsed_time:.2f} segundos")

    print(transcription_text)
    start_time = time.time()
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
    clean_text2 = clean_text.replace("\\", "")
    #print(clean_text)
    async def text_to_speech():
        rate = "+30%"  # Increase speed by 30%
        volume = "-80%"  # Slight volume boost
        voice = "pt-BR-FranciscaNeural"  # You can change the voice model
        output_file = "voz.mp3"

        # Create the TTS object and save the output as an MP3 file
        communicate = edge_tts.Communicate(clean_text2, voice, rate=rate, volume=volume)
        await communicate.save(output_file)

        #print("Speech saved to:", output_file)

    end_time = time.time()
    elapsed_time = end_time - start_time
    #print(f"Tempo entre pergunta e resposta: {elapsed_time:.2f} segundos")

    # Run the async function
    asyncio.run(text_to_speech())

#    with wave.open("voz.mp3", "r") as audio:
#        frames = audio.getnframes()
#        rate = audio.getframerate()
#        duration_seconds = frames / float(rate)
#        print(f"Duration: {duration_seconds} seconds")

    playaudioProcess = subprocess.Popen(["play", "voz.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    #playaudioProcess.wait()

    #audio = pyaudio.PyAudio()
    #stream = audio.open(format=FORMAT, channels=CHANNELS,
    #                    rate=RATE, input=True,
    #                    frames_per_buffer=CHUNK)
    data = stream.read(CHUNK)
    os.system("clear")
    while playaudioProcess.poll() is None:
        data = stream.read(CHUNK)
        if( is_silent(data)):
            #print("voz nao detectada")
            pass
        else:
            print("voz detectada")
            playaudioProcess.terminate()
            break
        
    if playaudioProcess.poll():
        playaudioProcess.terminate()
    stream.stop_stream()
    stream.close()
    audio.terminate()
    #playaudioProcess.terminate()
    #os.system("play voz.mp3")
    #os.system("clear")