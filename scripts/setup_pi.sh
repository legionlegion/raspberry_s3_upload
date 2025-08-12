#!/bin/bash
# Raspberry Pi 5 Audio Recorder Setup Script

echo "Setting up Raspberry Pi 5 Audio Recorder..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies for audio recording
echo "Installing audio dependencies..."
sudo apt install -y python3-pip python3-venv portaudio19-dev python3-pyaudio

# Install ALSA utilities for audio device management
echo "Installing ALSA utilities..."
sudo apt install -y alsa-utils

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ~/pi_recorder_env
source ~/pi_recorder_env/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements-pi.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p ~/VVRS-client/logs
mkdir -p ~/VVRS-client/temp_recordings

# Make the recorder script executable
echo "Making recorder script executable..."
chmod +x ~/VVRS-client/scripts/pi_recorder.py

# Test audio input
echo "Testing audio input..."
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
print('Available audio input devices:')
for i in range(p.get_device_count()):
    dev_info = p.get_device_info_by_index(i)
    if dev_info['maxInputChannels'] > 0:
        print(f'Device {i}: {dev_info[\"name\"]}')
p.terminate()
"

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a .env file with your AWS credentials"
echo "2. Test the recorder: python3 ~/VVRS-client/scripts/pi_recorder.py"
echo "3. Set up cron job for automatic startup"