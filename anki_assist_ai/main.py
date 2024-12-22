"""Main module for Anki card generation."""
import logging
from pathlib import Path

import pandas as pd
import yaml

from utils.anki_utils import add_or_update_anki_card
from utils.anki_utils import create_anki_model
from utils.example_generator import generate_image_from_profile
from utils.example_generator import generate_tts_from_profile
from utils.example_generator import get_translation_and_example


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load configuration to get supported languages and proficiency levels
with Path("config.yml").open() as config_file:
    config = yaml.safe_load(config_file)

SUPPORTED_LANGUAGES = config["languages"]["supported_source_languages"]
SUPPORTED_PROFICIENCY_LEVELS = config["languages"]["supported_proficiency_levels"]


def single_word_profile(
    grammar_file: str,
    word: str,
    source_language: str,
    proficiency_level: str,
    generate_image: bool = False,
    generate_tts: bool = False,
    add_to_anki: bool = False,
    lecture: int = 1,
    ubung: int = 1,
) -> dict:
    """Generate profile for a single word.

    Args:
        grammar_file: Path to grammar file
        word: German word to process
        source_language: Source language for translations
        proficiency_level: Language proficiency level
        generate_image: Whether to generate images
        generate_tts: Whether to generate TTS
        add_to_anki: Whether to add to Anki
        lecture: Lecture number
        ubung: Exercise number

    Returns:
        Dictionary containing word profile
    """
    word_profile = get_translation_and_example(
        word, source_language, proficiency_level, grammar_file, lecture, ubung
    )
    print(word_profile)

    if generate_image:
        generate_image_from_profile(word_profile)
    if generate_tts:
        generate_tts_from_profile(word_profile)
    if add_to_anki:
        add_or_update_anki_card(word_profile)

    return word_profile


def word_list_profile(
    grammar_file: str,
    word_csv: pd.DataFrame,
    source_language: str,
    proficiency_level: str,
    generate_image: bool = False,
    generate_tts: bool = False,
    add_to_anki: bool = False,
    start_row: int = 0,
) -> None:
    """Generate profiles for a list of words from CSV.

    Args:
        grammar_file: Path to grammar file
        word_csv: DataFrame containing words and their details
        source_language: Source language for translations
        proficiency_level: Language proficiency level
        generate_image: Whether to generate images
        generate_tts: Whether to generate TTS
        add_to_anki: Whether to add to Anki
        start_row: Row index to start processing from (0-based)
    """
    # Skip rows before start_row
    for idx, row in enumerate(word_csv.iterrows()):
        if idx < start_row:
            continue
            
        _, row_data = row
        word = row_data.iloc[0]  # Get word from first column
        lecture = row_data.iloc[1]  # Get lecture from second column
        ubung = row_data.iloc[2]  # Get ubung from third column
        print(f"\nProcessing row {idx + 1} of {len(word_csv)}: {word}")
        single_word_profile(
            grammar_file,
            word,
            source_language,
            proficiency_level,
            generate_image,
            generate_tts,
            add_to_anki,
            lecture,
            ubung,
        )


if __name__ == "__main__":
    create_anki_model()

    source_language = "English"
    proficiency_level = "B1.1"
    grammar_file = "b1.1/grammer.md"
    csv_file = "b1.1/word_exercises_combined_with_the_other_two_files.csv"
    generate_image = False
    generate_tts = False
    add_to_anki = True
    start_row = 250  # Start from the beginning, change this to skip rows

    # Read the CSV file
    df = pd.read_csv(csv_file, delimiter=";")
    print(f"Total rows in CSV: {len(df)}")
    word_list_profile(
        grammar_file,
        df,
        source_language,
        proficiency_level,
        generate_image,
        generate_tts,
        add_to_anki,
        start_row,
    )
