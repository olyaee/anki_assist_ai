"""Utility to check which words have been processed and which are pending."""
import os
import pandas as pd
import yaml
from pathlib import Path

# Load configuration
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

files_dir = config['files']['directory']

def check_word_files(word: str) -> dict:
    """Check which files exist for a given word.

    Args:
        word: The German word to check

    Returns:
        Dictionary with boolean values for each file type
    """
    return {
        'profile': os.path.exists(os.path.join(files_dir, f"{word}_profile.json")),
        'image': os.path.exists(os.path.join(files_dir, f"{word}_image.jpg")),
        'word_audio': os.path.exists(os.path.join(files_dir, f"{word}_word.wav")),
        'example_1': os.path.exists(os.path.join(files_dir, f"{word}_example_1.wav")),
        'example_2': os.path.exists(os.path.join(files_dir, f"{word}_example_2.wav")),
        'example_3': os.path.exists(os.path.join(files_dir, f"{word}_example_3.wav")),
    }

def is_word_complete(word: str) -> bool:
    """Check if all files exist for a word.

    Args:
        word: The German word to check

    Returns:
        True if all files exist, False otherwise
    """
    files = check_word_files(word)
    return all(files.values())

def check_progress(csv_file: str) -> dict:
    """Check progress for all words in the CSV.

    Args:
        csv_file: Path to the CSV file

    Returns:
        Dictionary with progress statistics and lists of complete/incomplete words
    """
    df = pd.read_csv(csv_file, delimiter=";")
    total_words = len(df)

    complete_words = []
    incomplete_words = []

    for idx, row in df.iterrows():
        word = row.iloc[0]  # First column is the word

        if is_word_complete(word):
            complete_words.append(word)
        else:
            incomplete_words.append({
                'word': word,
                'missing': {k: v for k, v in check_word_files(word).items() if not v}
            })

    return {
        'total': total_words,
        'complete': len(complete_words),
        'incomplete': len(incomplete_words),
        'complete_words': complete_words,
        'incomplete_words': incomplete_words,
        'completion_percentage': (len(complete_words) / total_words * 100) if total_words > 0 else 0
    }

if __name__ == "__main__":
    csv_file = "b1.1/word_exercises_combined_with_the_other_two_files.csv"

    print("Checking progress...\n")
    progress = check_progress(csv_file)

    print(f"{'='*60}")
    print(f"PROGRESS SUMMARY")
    print(f"{'='*60}")
    print(f"Total words:       {progress['total']}")
    print(f"Complete:          {progress['complete']} ({progress['completion_percentage']:.1f}%)")
    print(f"Incomplete:        {progress['incomplete']}")
    print(f"{'='*60}\n")

    if progress['incomplete'] > 0:
        print("INCOMPLETE WORDS (first 10):")
        print(f"{'-'*60}")
        for item in progress['incomplete_words'][:10]:
            word = item['word']
            missing = ', '.join(item['missing'].keys())
            print(f"  {word:<20} Missing: {missing}")

        if progress['incomplete'] > 10:
            print(f"\n  ... and {progress['incomplete'] - 10} more")

    if progress['complete'] > 0:
        print(f"\nCOMPLETE WORDS (first 10):")
        print(f"{'-'*60}")
        for word in progress['complete_words'][:10]:
            print(f"  ✓ {word}")

        if progress['complete'] > 10:
            print(f"\n  ... and {progress['complete'] - 10} more")
