"""Post-processing utilities for word profiles."""
from typing import Optional

import json
import logging
import os
from pathlib import Path

from utils.anki_utils import add_or_update_anki_card
from utils.example_generator import generate_image_from_profile
from utils.example_generator import generate_tts_from_profile
from voidaudio import add_silence_to_all_audio
from voidaudio import find_audio_files
from voidaudio import add_silence_to_audio


def add_silence_to_audios(files_dir: str = "./files") -> None:
    """Add 2 seconds of silence to all MP3 files in the directory.

    Args:
        files_dir: Directory containing the audio files
    """
    print("\nAdding silence to audio files:")
    print("=" * 30)
    
    try:
        # Find all MP3 files
        audio_files = find_audio_files(files_dir)
        print(f"Found {len(audio_files)} audio files")
        
        # Add silence to all audio files
        add_silence_to_all_audio(files_dir)
        
    except Exception as e:
        logging.error(f"Error processing audio files: {str(e)}")


def find_missing_sentences(files_dir: str = "./files") -> list[str]:
    """Go through all JSON files in the files directory and find items that don't have sentences.

    Args:
        files_dir: Directory containing the word profile JSON files

    Returns:
        List of German words that are missing sentences
    """
    missing_sentences = []

    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(files_dir) if f.endswith("_profile.json")]

        for json_file in json_files:
            file_path = os.path.join(files_dir, json_file)
            try:
                with open(file_path) as f:
                    profile = json.load(f)

                # Check if examples exist and are complete
                examples = profile.get("examples", [])
                if not examples or len(examples) < 3:
                    missing_sentences.append(profile["german_word"])
                else:
                    # Check if any example is missing either German or source language translation
                    for example in examples:
                        if not example.get("german_example") or not example.get(
                            "source_example_translation"
                        ):
                            missing_sentences.append(profile["german_word"])
                            break

            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON file: {json_file}")
            except KeyError:
                logging.error(f"Missing required fields in file: {json_file}")
            except Exception as e:
                logging.error(f"Error processing file {json_file}: {str(e)}")

    except Exception as e:
        logging.error(f"Error accessing directory {files_dir}: {str(e)}")

    # Print results for missing sentences
    if missing_sentences:
        print("\nWords missing sentences:")
        print("=" * 30)
        for word in missing_sentences:
            print(f"- {word}")
        print(f"\nTotal words with missing sentences: {len(missing_sentences)}")
    else:
        print("\nNo words with missing sentences found.")

    return missing_sentences


def find_items_with_asterisks(files_dir: str = "./files") -> dict[str, list[str]]:
    """Go through all JSON files in the files directory and find items that contain asterisks.

    Args:
        files_dir: Directory containing the word profile JSON files

    Returns:
        Dictionary mapping German words to lists of fields containing asterisks
    """
    items_with_asterisks = {}

    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(files_dir) if f.endswith("_profile.json")]

        for json_file in json_files:
            file_path = os.path.join(files_dir, json_file)
            try:
                with open(file_path) as f:
                    profile = json.load(f)

                asterisk_fields = []

                # Check german_word
                if "*" in profile.get("german_word", ""):
                    asterisk_fields.append("german_word")

                # Check translations
                for trans in profile.get("source_language_translation", []):
                    if "*" in trans:
                        asterisk_fields.append("source_language_translation")
                        break

                # Check examples
                for i, example in enumerate(profile.get("examples", [])):
                    if "*" in example.get("german_example", ""):
                        asterisk_fields.append(f"german_example_{i+1}")
                    if "*" in example.get("source_example_translation", ""):
                        asterisk_fields.append(f"source_example_translation_{i+1}")

                # If any fields had asterisks, add to results
                if asterisk_fields:
                    items_with_asterisks[profile["german_word"]] = asterisk_fields

            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON file: {json_file}")
            except KeyError:
                logging.error(f"Missing required fields in file: {json_file}")
            except Exception as e:
                logging.error(f"Error processing file {json_file}: {str(e)}")

    except Exception as e:
        logging.error(f"Error accessing directory {files_dir}: {str(e)}")

    # Print results for items with asterisks
    if items_with_asterisks:
        print("\nItems containing asterisks:")
        print("=" * 30)
        for word, fields in items_with_asterisks.items():
            print(f"\n- {word}:")
            for field in fields:
                print(f"  • {field}")
        print(f"\nTotal items with asterisks: {len(items_with_asterisks)}")
    else:
        print("\nNo items containing asterisks found.")

    return items_with_asterisks


def process_existing_profiles(
    generate_image: bool = False,
    generate_tts: bool = False,
    add_silence: bool = False,
    silence_duration_ms: int = 2000,
    add_to_anki: bool = False,
    limit: Optional[int] = None,
) -> None:
    """Process existing JSON profile files to generate TTS and images.

    Args:
        generate_image: Whether to generate images
        generate_tts: Whether to generate TTS
        add_silence: Whether to add silence to the beginning of audio files
        silence_duration_ms: Duration of silence to add in milliseconds
        add_to_anki: Whether to add or update cards in Anki
        limit: Limit processing to first n files. If None, process all files
    """
    files_dir = Path("./files")
    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(files_dir) if f.endswith("_profile.json")]

        if limit:
            json_files = json_files[:limit]
            logging.info(f"Processing first {limit} files")
        else:
            logging.info(f"Processing all {len(json_files)} files")

        for json_file in json_files:
            file_path = files_dir / json_file
            try:
                with file_path.open() as f:
                    word_profile = json.load(f)

                logging.info(f"Processing {word_profile['german_word']}")

                if generate_image:
                    generate_image_from_profile(word_profile)
                if generate_tts:
                    generate_tts_from_profile(word_profile)
                
                if add_silence:
                    # Find and process audio files for this word
                    word = word_profile['german_word']
                    audio_files = [
                        f for f in os.listdir(files_dir) 
                        if f.startswith(word) and f.endswith('.mp3')
                    ]
                    for audio_file in audio_files:
                        file_path = files_dir / audio_file
                        add_silence_to_audio(str(file_path), silence_duration_ms)
                
                if add_to_anki:
                    add_or_update_anki_card(word_profile)

            except Exception as e:
                logging.error(f"Error processing file {json_file}: {str(e)}")
                continue

    except Exception as e:
        logging.error(f"Error accessing directory {files_dir}: {str(e)}")


def find_irregular_words(files_dir: str = "./files") -> dict[str, dict]:
    """Find all words that have irregular verbs or adjectives.

    Args:
        files_dir: Directory containing the word profile JSON files

    Returns:
        Dictionary mapping German words to their irregularity information
    """
    irregular_words = {}

    try:
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(files_dir) if f.endswith("_profile.json")]

        for json_file in json_files:
            file_path = os.path.join(files_dir, json_file)
            try:
                with open(file_path) as f:
                    profile = json.load(f)

                word = profile["german_word"]
                irregular_types = []
                irregular_info = {}

                # Check verb irregularity
                verb_info = profile.get("additional_grammatical_info", {}).get("verb", {})
                if verb_info.get("irregular", False):
                    irregular_types.append("verb")
                    irregular_info["verb"] = verb_info

                # Check adjective irregularity
                adj_info = profile.get("additional_grammatical_info", {}).get("adjective", {})
                if adj_info.get("irregular", False):
                    irregular_types.append("adjective")
                    irregular_info["adjective"] = adj_info

                # If any irregularities found, add to results
                if irregular_types:
                    irregular_words[word] = {
                        "types": irregular_types,
                        "info": irregular_info
                    }

            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON file: {json_file}")
            except KeyError:
                logging.error(f"Missing required fields in file: {json_file}")
            except Exception as e:
                logging.error(f"Error processing file {json_file}: {str(e)}")

    except Exception as e:
        logging.error(f"Error accessing directory {files_dir}: {str(e)}")

    # Print results
    if irregular_words:
        print("\nIrregular words:")
        for word in sorted(irregular_words.keys()):
            print(f"- {word}")
        print(f"\nTotal: {len(irregular_words)}")
    else:
        print("\nNo irregular words found.")

    return irregular_words


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Process existing profiles with silence
    print("\nProcessing existing profiles:")
    print("=" * 30)
    process_existing_profiles(
        generate_image=False,
        generate_tts=True,
        add_silence=True,
        silence_duration_ms=1000,  # 1 second
        add_to_anki=True,
        limit=1,
    )

    # Find words with missing sentences
    words_missing_sentences = find_missing_sentences()

    # Find items with asterisks
    items_with_asterisks = find_items_with_asterisks()

    # Find irregular words
    irregular_words = find_irregular_words()
