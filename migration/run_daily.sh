#!/bin/bash
# Auto-run word processor - runs multiple times per day
# Logs to file for tracking progress

set -e

# Configuration
PROJECT_DIR="$HOME/Documents/Code/anki_assist_ai/migration"
LOG_FILE="$HOME/anki_processor.log"
CSV_FILE="word_exercises_combined_with_the_other_two_files.csv"
GRAMMAR_FILE="grammer.md"

# Log start
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "$(date): Starting automated word processing" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Check if Anki is running, if not start it
if ! pgrep -x "Anki" > /dev/null; then
    echo "$(date): Starting Anki..." >> "$LOG_FILE"
    open -a Anki
    # Wait for Anki to start
    sleep 10
else
    echo "$(date): Anki already running" >> "$LOG_FILE"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment and run
source $(poetry env info --path)/bin/activate

# Run the processor
echo "$(date): Running processor..." >> "$LOG_FILE"
poetry run python process_words.py \
    --csv "$CSV_FILE" \
    --grammar "$GRAMMAR_FILE" \
    --language English \
    --level B1.1 >> "$LOG_FILE" 2>&1

# Log completion
echo "$(date): Completed processing run" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
