#!/usr/bin/env python3
"""
Test script for Raspberry Pi audio recording
Use this to verify microphone and recording functionality
"""

import os
import sys
import wave
import pyaudio
from datetime import datetime

# Audio settings
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
TEST_DURATION = 5  # 5 seconds for testing

def test_audio_devices():
    """List available audio input devices"""
    print("Available audio input devices:")
    p = pyaudio.PyAudio()
    
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:
            print(f"Device {i}: {dev_info['name']}")
            print(f"  - Max input channels: {dev_info['maxInputChannels']}")
            print(f"  - Default sample rate: {dev_info['defaultSampleRate']}")
    
    p.terminate()

def test_recording(duration=TEST_DURATION):
    """Test recording for specified duration"""
    print(f"Testing recording for {duration} seconds...")
    
    p = pyaudio.PyAudio()
    
    try:
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print("Recording started... (speak into microphone)")
        
        frames = []
        for i in range(0, int(SAMPLE_RATE / CHUNK_SIZE * duration)):
            data = stream.read(CHUNK_SIZE)
            frames.append(data)
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save test recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_filename = f"test_recording_{timestamp}.wav"
        
        with wave.open(test_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(frames))
        
        print(f"Test recording saved: {test_filename}")
        print(f"File size: {os.path.getsize(test_filename)} bytes")
        
        return True
        
    except Exception as e:
        print(f"Recording test failed: {e}")
        return False
    finally:
        p.terminate()

def main():
    print("Raspberry Pi Audio Recording Test")
    print("=" * 40)
    
    # Test 1: List audio devices
    print("\n1. Testing audio devices...")
    test_audio_devices()
    
    # Test 2: Test recording
    print(f"\n2. Testing recording ({TEST_DURATION} seconds)...")
    if test_recording():
        print("✓ Recording test passed!")
    else:
        print("✗ Recording test failed!")
        sys.exit(1)
    
    print("\n✓ All tests completed successfully!")
    print("The Pi is ready for audio recording.")

if __name__ == "__main__":
    main() 