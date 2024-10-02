# -*- coding: utf-8 -*-
"""SpeechToText

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1sl0nXl--HwvTuyf14HRWA7YYEOZ1hKhf
"""

pip install pydub requests

import os
import subprocess
import requests

# Step 1: Extract audio from video using ffmpeg
def extract_audio(video_file_path, audio_file_path):
    try:
        # Command to extract audio
        command = f"ffmpeg -i {video_file_path} -vn -acodec mp3 {audio_file_path}"
        subprocess.run(command, shell=True, check=True)
        print(f"Audio extracted successfully: {audio_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")

# Step 2: Perform speech to text using Deepgram API
def speech_to_text(audio_file_path, deepgram_api_key):
    deepgram_url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {deepgram_api_key}",
        "Content-Type": "audio/mp3"
    }

    with open(audio_file_path, "rb") as audio_file:
        response = requests.post(deepgram_url, headers=headers, data=audio_file)

    if response.status_code == 200:
        transcription = response.json()
        return transcription.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return ""

# Main script
if __name__ == "__main__":
    video_file_path = "your_video.mp4"  # Replace with your video file path
    audio_file_path = "output_audio.mp3"
    deepgram_api_key = "YOUR_DEEPGRAM_API_KEY"  # Replace with your Deepgram API key

    # Extract audio
    extract_audio(video_file_path, audio_file_path)

    # Perform speech to text
    transcript = speech_to_text(audio_file_path, deepgram_api_key)

    if transcript:
        print("Transcription:")
        print(transcript)



