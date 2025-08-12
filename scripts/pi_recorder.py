#!/usr/bin/env python3
"""
Raspberry Pi 5 Audio Recorder and S3 Uploader
Records audio from microphone during specified hours and uploads to S3
"""

import os
import sys
import time
import wave
import pyaudio
import threading
from datetime import datetime, time as dt_time
from typing import TYPE_CHECKING, TypedDict
import boto3
from dotenv import load_dotenv

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

# Configuration
RECORDING_HOURS = (0, 23)  # 9 AM to 6 PM
RECORDING_DURATION = 60  # seconds

# Default audio settings (can be overridden by environment or device defaults)
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 2048  # larger buffer helps avoid input overflow
FORMAT = pyaudio.paInt16

# Directories
DIR_SCRIPT = os.path.dirname(os.path.realpath(__file__))
DIR_LOGGING = os.path.join(DIR_SCRIPT, "..", "logs")
DIR_TEMP_RECORDINGS = os.path.join(DIR_SCRIPT, "..", "temp_recordings")

class Config(TypedDict):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_OBJECT_KEY_PREFIX: str

def log_message(message: str):
    """Log messages with timestamp to daily log file"""
    log_dir = os.path.expanduser(DIR_LOGGING)
    os.makedirs(log_dir, exist_ok=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"pi_recorder_{today_date}.log")

    with open(log_file, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")
    
    # Also print to console for debugging
    print(f"[{timestamp}] {message}")

def get_config() -> Config:
    """Load configuration from environment variables"""
    load_dotenv()

    config: Config = {
        'AWS_ACCESS_KEY_ID': "",
        'AWS_SECRET_ACCESS_KEY': "",
        'S3_BUCKET_NAME': "",
        'S3_OBJECT_KEY_PREFIX': ""
    }
    
    for env_var in config.keys():
        value = os.environ.get(env_var, None) 
        print("Value: " + env_var + value)
        if value is None:
            log_message(f"Environment variable '{env_var}' not set! Exiting...")
            sys.exit(1)
        config[env_var] = value
    
    log_message(f"Configuration loaded. S3 Bucket: {config.get('S3_BUCKET_NAME')}")
    return config

def is_recording_time() -> bool:
    """Check if current time is within recording hours"""
    now = datetime.now().time()
    start_hour = min(max(RECORDING_HOURS[0], 0), 23)
    end_hour   = min(max(RECORDING_HOURS[1], 0), 23)
    start_time = dt_time(start_hour, 0)
    end_time   = dt_time(end_hour, 0)
    
    return start_time <= now <= end_time

def _int_from_env(name: str, default: int) -> int:
    try:
        value = os.getenv(name, "")
        return int(value) if value else default
    except Exception:
        return default

def resolve_input_device_index(p: pyaudio.PyAudio) -> int | None:
    try:
        info = p.get_default_input_device_info()
        return int(info["index"])
    except Exception:
        return None

def get_audio_settings(p: pyaudio.PyAudio) -> tuple[int, int, int, int | None]:
    """Determine audio settings, preferring env, then device defaults."""
    device_index = resolve_input_device_index(p)

    # sample rate
    sr_env = os.getenv("AUDIO_SAMPLE_RATE", "").strip()
    if sr_env.isdigit():
        sample_rate = int(sr_env)
    else:
        if device_index is not None:
            try:
                dev_info = p.get_device_info_by_index(device_index)
                log_message(f"Dev info {dev_info}")
                sample_rate = int(dev_info.get("defaultSampleRate", DEFAULT_SAMPLE_RATE))
                log_message(f"Using MIC sample rate: {sample_rate}")

            except Exception:
                log_message("Exception: Using default sample rate")
                sample_rate = DEFAULT_SAMPLE_RATE
        else:
            log_message("Using default sample rate")
            sample_rate = DEFAULT_SAMPLE_RATE

    channels   = _int_from_env("AUDIO_CHANNELS", DEFAULT_CHANNELS)
    chunk_size = _int_from_env("AUDIO_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)

    return sample_rate, channels, chunk_size, device_index

def record_audio(duration: int, output_filename: str, sample_rate: int, channels: int, chunk_size: int, device_index: int, p: pyaudio) -> bool:
    """Record audio for specified duration and save as WAV file"""
    try:
        # Create temp recordings directory
        os.makedirs(DIR_TEMP_RECORDINGS, exist_ok=True)
        


        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=device_index if device_index is not None else None,
        )
        
        chosen_dev = device_index if device_index is not None else "default"
        log_message(
            f"Starting recording for {duration} seconds"
        )
        
        frames = []
        total_chunks = int(sample_rate / chunk_size * duration)
        for _ in range(total_chunks):
            try:
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                # Log and continue to avoid bailing out on transient overflows
                log_message(f"[WARN] stream.read issue (continuing): {e}")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save the recorded data as a WAV file
        output_path = os.path.join(DIR_TEMP_RECORDINGS, output_filename)
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        log_message(f"Recording completed: {output_filename}")
        return True
        
    except Exception as e:
        log_message(f"[ERROR] Recording failed: {e}")
        return False

def upload_to_s3(client: "S3Client", config: Config, file_path: str, file_name: str):
    """Upload WAV file to S3"""
    try:
        created_at = datetime.now().isoformat()
        s3_key = f"{config['S3_OBJECT_KEY_PREFIX']}{created_at}/{file_name}"
        
        log_message(f"Uploading {file_name} to S3...")
        client.upload_file(
            Filename=file_path,
            Bucket=config['S3_BUCKET_NAME'],
            Key=s3_key
        )
        log_message(f"File {file_name} uploaded successfully!")
        
        # Clean up local file after successful upload
        os.remove(file_path)
        log_message(f"Local file {file_name} removed")
        
    except Exception as e:
        log_message(f"[ERROR] Upload failed for {file_name}: {e}")

def record_and_upload_session(config: Config, client: "S3Client"):
    """Record for one session duration and upload"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"
    
    p = pyaudio.PyAudio()
    sample_rate, channels, chunk_size, device_index = get_audio_settings(p)
    log_message(
        f"Microphone config: rate={sample_rate}Hz, channels={channels}, chunk={chunk_size}, device={device_index}"
    )

    if record_audio(RECORDING_DURATION, filename, sample_rate, channels, chunk_size, device_index, p):
        file_path = os.path.join(DIR_TEMP_RECORDINGS, filename)
        upload_to_s3(client, config, file_path, filename)
    else:
        log_message("Recording session failed, skipping upload")

def main():
    """Main function - runs continuously during recording hours"""
    log_message("Pi Audio Recorder started!")
    
    config = get_config()
        
    client: S3Client = boto3.client(
        's3',
        aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=config["AWS_SECRET_ACCESS_KEY"]
    )
    
    log_message(f"Recording hours: {RECORDING_HOURS[0]}:00 - {RECORDING_HOURS[1]}:00")
    log_message(f"Recording duration per session: {RECORDING_DURATION} seconds")
    
    while True:
        try:
            if is_recording_time():
                log_message("Starting recording session...")
                record_and_upload_session(config, client)
                
                # Wait a bit before next session
                # time.sleep(1)  # 1 sec break between sessions
            else:
                # Outside recording hours, sleep longer
                log_message("Outside recording hours, sleeping...")
                time.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            log_message("Recording stopped by user")
            break
        except Exception as e:
            log_message(f"[ERROR] Unexpected error: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main() 