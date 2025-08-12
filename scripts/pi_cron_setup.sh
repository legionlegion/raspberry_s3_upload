#!/bin/bash
# Cron Setup Script for Pi Audio Recorder

echo "Setting up cron job for Pi Audio Recorder..."

# Get the current user's home directory
HOME_DIR=$(eval echo ~$USER)
SCRIPT_PATH="$HOME_DIR/VVRS-client/scripts/pi_recorder.py"
PYTHON_PATH="$HOME_DIR/pi_recorder_env/bin/python3"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Recorder script not found at $SCRIPT_PATH"
    echo "Please run setup_pi.sh first"
    exit 1
fi

# Check if Python environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python environment not found at $PYTHON_PATH"
    echo "Please run setup_pi.sh first"
    exit 1
fi

# Create the cron job entry
CRON_JOB="24 0 * * * $PYTHON_PATH $SCRIPT_PATH"
REBOOT_JOB="@reboot $PYTHON_PATH $SCRIPT_PATH"

echo "Adding cron jobs:"
echo "  $CRON_JOB"
echo "  $REBOOT_JOB"

# Append both jobs without overwriting existing ones
(crontab -l 2>/dev/null; echo "$CRON_JOB"; echo "$REBOOT_JOB") | crontab -

echo "Cron job added successfully!"
echo ""
echo "Current cron jobs:"
crontab -l
echo ""
echo "The recorder will now start automatically at 9:00 AM daily"
echo "To remove the cron job, run: crontab -e and delete the line" 