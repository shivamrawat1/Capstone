import nest_asyncio
import asyncio
from deepgram import Deepgram
import sounddevice as sd
import numpy as np
from signal import SIGINT, SIGTERM
import logging
from deepgram.utils import verboselogs
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from dotenv import load_dotenv

load_dotenv()
nest_asyncio.apply()

# Buffer to store final results
is_finals = []

# Your personal API key from Deepgram
DEEPGRAM_API_KEY = 'c808d97be5d19017965cdba6186189754b2829a6'

async def main():
    try:
        loop = asyncio.get_event_loop()

        for signal in (SIGTERM, SIGINT):
            loop.add_signal_handler(
                signal,
                lambda: asyncio.create_task(shutdown(signal, loop, dg_connection, microphone)),
            )

        # Setup Deepgram Client with Options
        config: DeepgramClientOptions = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY, config)

        # Create WebSocket Connection
        dg_connection = deepgram.listen.asyncwebsocket.v("1")

        # Define event handlers for live transcription
        async def on_open(self, open, **kwargs):
            print("Connection Open")

        async def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            if result.is_final:
                # Append the final result to is_finals list
                is_finals.append(sentence)

        async def on_metadata(self, metadata, **kwargs):
            print(f"Metadata: {metadata}")

        async def on_speech_started(self, speech_started, **kwargs):
            print("Speech Started")

        async def on_utterance_end(self, utterance_end, **kwargs):
            global is_finals
            if len(is_finals) > 0:
                # Concatenate all sentences into one
                complete_transcription = " ".join(is_finals)
                print(f"Complete Transcription: {complete_transcription}")
                # Clear the buffer after printing
                is_finals = []

        async def on_close(self, close, **kwargs):
            print("Connection Closed")

        async def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        async def on_unhandled(self, unhandled, **kwargs):
            print(f"Unhandled Websocket Message: {unhandled}")

        # Register event handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        # Set up live transcription options
        options: LiveOptions = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300,
        )

        addons = {
            "no_delay": "true"
        }

        print("\n\nStart talking! Press Ctrl+C to stop...\n")
        if await dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        # Open microphone stream on default input device
        microphone = Microphone(dg_connection.send)
        microphone.start()

        # Wait until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            microphone.finish()
            await dg_connection.finish()

        print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

# Handle shutdown signals
async def shutdown(signal, loop, dg_connection, microphone):
    print(f"Received exit signal {signal.name}...")
    microphone.finish()
    await dg_connection.finish()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    print("Shutdown complete.")

asyncio.run(main())
