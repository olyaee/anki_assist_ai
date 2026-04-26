#!/usr/bin/env python3
"""
Validate generated files for each word in the CSV.

Checks that files referenced by timestamps actually exist and aren't corrupted.
Clears timestamps for missing/corrupt files so the next process_words.py run
regenerates them.

Uses the same file path logic as process_words.py:
  - Profile: normalize_word(csv_word) -> "{Normalized}_profile.json"
  - Image/TTS: reads german_word from profile JSON, then
    sanitize_filename(normalize_word(german_word)) -> filenames

Usage:
    poetry run python validate_files.py --csv "word_exercises_combined_with_the_other_two_files.csv"
    poetry run python validate_files.py --csv "word_exercises_combined_with_the_other_two_files.csv" --dry-run
"""
import argparse
import json
import wave
from pathlib import Path

import pandas as pd
import yaml


def normalize_word(word):
    """Extract base word: 'himmel, der, -' -> 'Himmel'"""
    return word.split(',')[0].strip().capitalize()


def sanitize_filename(name):
    """Remove/replace characters invalid in file paths."""
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, '-')
    return name


def validate_json(path):
    """Check if file is valid JSON."""
    try:
        with open(path, 'r') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def validate_wav(path):
    """Check if file is a valid, non-empty WAV."""
    try:
        with wave.open(str(path), 'rb') as w:
            return w.getnframes() > 0
    except (wave.Error, EOFError, OSError):
        return False


def validate_jpg(path):
    """Check if file is a valid JPEG (starts with FF D8 and has reasonable size)."""
    try:
        if path.stat().st_size < 100:
            return False
        with open(path, 'rb') as f:
            header = f.read(2)
            return header == b'\xff\xd8'
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(description='Validate generated files and clean CSV timestamps')
    parser.add_argument('--csv', required=True, help='Path to the CSV file')
    parser.add_argument('--dry-run', action='store_true', help='Only report issues, do not modify CSV')
    args = parser.parse_args()

    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    files_dir = Path(config['files']['directory'])
    df = pd.read_csv(args.csv, delimiter=';')

    cleared = 0
    issues = []

    for idx, row in df.iterrows():
        word = row.iloc[0]

        # --- Profile check (same path as process_words.py) ---
        # Profile uses: normalize_word(csv_word)
        profile_normalized = normalize_word(word)
        profile_path = files_dir / f"{profile_normalized}_profile.json"

        if pd.notna(row.get('profile_timestamp')):
            if not profile_path.exists():
                reason = 'missing'
            elif not validate_json(profile_path):
                reason = 'corrupted'
            else:
                reason = None

            if reason:
                issues.append((word, 'profile_timestamp', profile_path.name, reason))
                if not args.dry_run:
                    # Clear profile + all downstream
                    for col in ['profile_timestamp', 'image_timestamp', 'tts_1_timestamp', 'tts_2_timestamp', 'tts_3_timestamp']:
                        if pd.notna(row.get(col)):
                            df.at[idx, col] = pd.NaT
                            cleared += 1
                continue  # Skip image/TTS checks if profile is bad or missing

        # --- Image/TTS checks ---
        # These use: sanitize_filename(normalize_word(profile['german_word']))
        # So we need to read german_word from the profile JSON
        if not profile_path.exists():
            continue

        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        german_word = profile_data.get('german_word', '')
        if not german_word:
            continue

        media_normalized = sanitize_filename(normalize_word(german_word))

        # Image check
        if pd.notna(row.get('image_timestamp')):
            image_path = files_dir / f"{media_normalized}_image.jpg"
            if not image_path.exists():
                reason = 'missing'
            elif not validate_jpg(image_path):
                reason = 'corrupted'
            else:
                reason = None

            if reason:
                issues.append((word, 'image_timestamp', image_path.name, reason))
                if not args.dry_run:
                    df.at[idx, 'image_timestamp'] = pd.NaT
                    cleared += 1

        # TTS checks
        examples = profile_data.get('examples', [])
        tts_bad = False
        for i, col in enumerate(['tts_1_timestamp', 'tts_2_timestamp', 'tts_3_timestamp']):
            if pd.isna(row.get(col)):
                continue

            # Only check if there's actually an example for this index
            if i < len(examples) and examples[i].get('german_example', ''):
                wav_path = files_dir / f"{media_normalized}_example_{i+1}.wav"
                if not wav_path.exists():
                    reason = 'missing'
                elif not validate_wav(wav_path):
                    reason = 'corrupted'
                else:
                    continue

                issues.append((word, col, wav_path.name, reason))
                tts_bad = True

        # If any TTS is bad, clear all TTS timestamps
        if tts_bad and not args.dry_run:
            for col in ['tts_1_timestamp', 'tts_2_timestamp', 'tts_3_timestamp']:
                if pd.notna(row.get(col)):
                    df.at[idx, col] = pd.NaT
                    cleared += 1

    # Report
    if issues:
        print(f"\nFound {len(issues)} issue(s):\n")
        for word, col, filename, reason in issues:
            print(f"  [{reason.upper():9s}] {word:<40s} {col:<20s} -> {filename}")
    else:
        print("\nAll files OK - nothing to fix.")

    if not args.dry_run and issues:
        df.to_csv(args.csv, sep=';', index=False)
        print(f"\nCleared {cleared} timestamp(s) in CSV. Run process_words.py to regenerate.")
    elif args.dry_run and issues:
        print(f"\n(Dry run - would clear {len(issues)} timestamp(s). Run without --dry-run to apply.)")


if __name__ == '__main__':
    main()
