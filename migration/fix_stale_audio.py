#!/usr/bin/env python3
"""
Delete stale audio files and clear their TTS timestamps in the CSV,
so process_words.py regenerates them on next run.
"""
import json
import os
from pathlib import Path

import pandas as pd
import yaml


def normalize_word(word):
    return word.split(',')[0].strip().capitalize()


def sanitize_filename(name):
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, '-')
    return name


def main():
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    csv_path = 'word_exercises_combined_with_the_other_two_files.csv'
    files_dir = Path(config['files']['directory'])
    df = pd.read_csv(csv_path, delimiter=';')

    # Build set of stale german_words from profile files
    stale_words = set()
    deleted_files = 0

    for profile_path in files_dir.glob('*_profile.json'):
        try:
            with open(profile_path) as f:
                profile = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        german_word = profile.get('german_word', '')
        if not german_word:
            continue

        media_name = sanitize_filename(normalize_word(german_word))
        profile_mtime = os.path.getmtime(profile_path)

        for i in range(1, 4):
            wav = files_dir / f"{media_name}_example_{i}.wav"
            if wav.exists() and os.path.getmtime(wav) < profile_mtime:
                stale_words.add(german_word)
                break

    if not stale_words:
        print("No stale audio found.")
        return

    # Delete stale wav files
    for word in sorted(stale_words):
        media_name = sanitize_filename(normalize_word(word))
        for i in range(1, 4):
            wav = files_dir / f"{media_name}_example_{i}.wav"
            if wav.exists():
                wav.unlink()
                deleted_files += 1

    # Clear TTS timestamps in CSV for matching rows
    cleared = 0
    for idx, row in df.iterrows():
        csv_word = row.iloc[0]
        csv_normalized = normalize_word(csv_word)

        # Match against stale words by normalized form
        for stale_word in stale_words:
            if normalize_word(stale_word) == csv_normalized:
                for col in ['tts_1_timestamp', 'tts_2_timestamp', 'tts_3_timestamp']:
                    if pd.notna(row.get(col)):
                        df.at[idx, col] = pd.NaT
                        cleared += 1
                break

    df.to_csv(csv_path, sep=';', index=False)

    print(f"Fixed {len(stale_words)} words:")
    print(f"  Deleted {deleted_files} stale wav files")
    print(f"  Cleared {cleared} TTS timestamps")
    print(f"\nRun process_words.py to regenerate TTS.")


if __name__ == '__main__':
    main()
