#!/usr/bin/env python3
"""
Find words where audio files are older than the profile JSON.

This means the profile was regenerated (new example sentences) but the old
audio files were kept, so the audio no longer matches what's on the card.
"""
import json
import os
from pathlib import Path

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

    files_dir = Path(config['files']['directory'])

    mismatches = []

    for profile_path in sorted(files_dir.glob('*_profile.json')):
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

        stale_files = []
        for i in range(1, 4):
            wav = files_dir / f"{media_name}_example_{i}.wav"
            if wav.exists():
                wav_mtime = os.path.getmtime(wav)
                if wav_mtime < profile_mtime:
                    stale_files.append(wav.name)

        if stale_files:
            examples = [
                ex.get('german_example', '')
                for ex in profile.get('examples', [])[:3]
            ]
            mismatches.append({
                'word': german_word,
                'profile': profile_path.name,
                'profile_mtime': profile_mtime,
                'stale_files': stale_files,
                'examples': examples,
            })

    if not mismatches:
        print("No stale audio found — all audio files are newer than their profiles.")
        return

    print(f"Found {len(mismatches)} word(s) with stale audio:\n")
    for m in mismatches:
        from datetime import datetime
        p_time = datetime.fromtimestamp(m['profile_mtime']).strftime('%Y-%m-%d %H:%M')
        wav_time = datetime.fromtimestamp(
            os.path.getmtime(files_dir / m['stale_files'][0])
        ).strftime('%Y-%m-%d %H:%M')
        print(f"  {m['word']}")
        print(f"    Profile updated: {p_time}")
        print(f"    Audio from:      {wav_time}")
        print(f"    Stale files:     {', '.join(m['stale_files'])}")
        print(f"    Current examples:")
        for i, ex in enumerate(m['examples'], 1):
            print(f"      {i}. {ex}")
        print()


if __name__ == '__main__':
    main()
