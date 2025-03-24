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
from pydub import AudioSegment

activation_words = ["computador", "computada","computado" ]

# Set up audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # CD-quality audio
CHUNK = 1024
OUTPUT_FILENAME = "output.mp3"

# Silence detection config
SILENCE_THRESHOLD = 500  # Lower means more sensitive

whisperModel = WhisperModel("tiny")

GROQ_API_KEY = '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'

if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

def print_bars():
    print("Assistente: ", end="")
    for i in range(30):
        print("|", end="")
    os.system("clear")            
    for i in range(15):
            print("|", end="")
    time.sleep(1)
    os.system("clear")

def get_volume_bars(audio_file, chunk_size=1024, bar_length=30):
    # Load the audio file
    audio = AudioSegment.from_file(audio_file)

    # Break audio into small chunks (frames)
    samples = np.array(audio.get_array_of_samples())
    total_chunks = len(samples) // chunk_size

    # Analyze each chunk's volume
    for i in range(total_chunks):
        chunk = samples[i * chunk_size : (i + 1) * chunk_size]
        volume_level = np.linalg.norm(chunk) / chunk_size

        # Convert volume to bar representation
        bars = "|" * int(volume_level / 50 * bar_length)
        print(f"\r🔊 Volume: {bars.ljust(bar_length)}", end="")
        time.sleep(chunk_size / audio.frame_rate)

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

async def text_to_speech(text):
    rate = "+30%"  # Increase speed by 30%
    volume = "-80%"  # Slight volume boost
    voice = "pt-BR-FranciscaNeural"  # You can change the voice model
    output_file = "voz.mp3"

    # Create the TTS object and save the output as an MP3 file
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    await communicate.save(output_file)

    #print("Speech saved to:", output_file)

transcription_text = ""

                                            ## MAIN LOOP ##

while True:
    audio = pyaudio.PyAudio()
    os.system("clear")
    if transcription_text != "Responda em português. ":
        print("Diga 'OK computador' para ativar o assistente")
    else:
        print("Não foi possível identificar a pergunta, tente novamente. Diga OK computador")
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
            segments, info = whisperModel.transcribe("output.mp3", language="pt")
            requisition_text = "palavra" + " ".join([segment.text for segment in segments])
            #print(requisition_text)
            if any(word in requisition_text for word in activation_words):
                #print(requisition_text)
                break
    
    print("Pode perguntar.")
    asyncio.run(text_to_speech("Pode perguntar"))
    helloAudioProccess = subprocess.Popen(["play", "voz.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    
    while (helloAudioProccess.poll()):
        pass        
    while(True):
        data = stream.read(CHUNK)
        if( is_silent(data)):
            pass
        else:
            record_until_silence(2)
            segments, info = whisperModel.transcribe("output.mp3", language="pt")
            requisition_text = "palavra" + " ".join([segment.text for segment in segments])
            break

    #record_until_silence(4)

    start_whisper_time = time.time()
    segments, info = whisperModel.transcribe("output.mp3", language="pt")
    transcription_text = "Responda em português. " + " ".join([segment.text for segment in segments])
    end_whisper_time = time.time()
    whisper_elapsed_time = end_whisper_time - start_whisper_time
    #print(f"Tempo entre pergunta e resposta: {whisper_elapsed_time:.2f} segundos")
    print("Aguardando resposta da API.")

    if transcription_text == "Responda em português. ":
        print("Não foi possível identificar a pergunta, tente novamente.")
    else:
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

        end_time = time.time()
        elapsed_time = end_time - start_time
        #print(f"Tempo entre pergunta e resposta: {elapsed_time:.2f} segundos")

        # Run the async function
        asyncio.run(text_to_speech(clean_text2))
        playaudioProcess = subprocess.Popen(["play", "voz.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
        data = stream.read(CHUNK)

        os.system("clear")
        print("Assistente respondendo, para interromper fale qualquer coisa.")

        while playaudioProcess.poll() is None:
            data = stream.read(CHUNK)
            if( is_silent(data)):
                #print("voz nao detectada")
                #get_volume_bars("voz.mp3")
                #print("Assistente respondendo, para interromper fale qualquer coisa")
                #time.sleep(1)
                #os.system("clear")
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