# Raspberry Pi 5 Audio Recorder

This implementation adapts the VVRS client for Raspberry Pi 5 to record audio from a microphone and upload WAV files to S3 during specified hours (9 AM - 6 PM daily).

## Features

- **Automatic Recording**: Records audio during specified hours (9 AM - 6 PM)
- **S3 Upload**: Automatically uploads WAV files to AWS S3
- **Cron Integration**: Can be scheduled to start automatically
- **Logging**: Comprehensive logging with daily log files
- **Error Handling**: Robust error handling and recovery

## Hardware Requirements

- Raspberry Pi 5
- Microphone (USB or 3.5mm jack)
- Internet connection for S3 uploads
- SD card with sufficient storage

## Installation

### 1. Clone the Repository

```bash
cd ~
git clone <repository-url> VVRS-client
cd VVRS-client
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```

This script will:
- Update system packages
- Install audio dependencies (PyAudio, ALSA)
- Create Python virtual environment
- Install Python dependencies
- Create necessary directories
- Test audio input devices

### 3. Configure AWS Credentials

Copy the template and fill in your AWS credentials:

```bash
cp scripts/pi_config_template.env .env
nano .env
```

Edit the `.env` file with your AWS credentials

### 4. Test Audio Recording

Test the microphone and recording functionality:

```bash
python3 scripts/pi_test_recording.py
```

This will:
- List available audio input devices
- Record a 5-second test file
- Verify the recording works

## Usage

### Manual Testing

Test the recorder manually:

```bash
source ~/pi_recorder_env/bin/activate
python3 scripts/pi_recorder.py
```

The script will:
- Check if it's within recording hours (9 AM - 6 PM)
- Record 1-hour audio sessions
- Upload WAV files to S3
- Clean up local files after upload

### Automatic Startup with Cron

Set up automatic startup at 9 AM daily:

```bash
chmod +x scripts/pi_cron_setup.sh
./scripts/pi_cron_setup.sh
```

Or manually add to crontab:

```bash
crontab -e
```

Add this line:
```
0 9 * * * /home/pi/pi_recorder_env/bin/python3 /home/pi/VVRS-client/scripts/pi_recorder.py
```

## Configuration

### Recording Settings

Edit `scripts/pi_recorder.py` to modify:

- **Recording Hours**: Change `RECORDING_HOURS = (9, 18)` for different times
- **Session Duration**: Change `RECORDING_DURATION = 3600` for different session lengths
- **Audio Quality**: Modify `SAMPLE_RATE`, `CHANNELS`, `FORMAT` for different quality

## Monitoring

### Logs

Check daily logs:

```bash
tail -f logs/pi_recorder_$(date +%Y-%m-%d).log
```

### Cron Status

Check if cron is running:

```bash
crontab -l
```

### Process Status

Check if recorder is running:

```bash
ps aux | grep pi_recorder
pkill -f pi_recorder.py
```
