from utils.example_generator import get_translation_and_example, generate_image_from_profile, generate_tts_from_profile
from utils.anki_utils import create_anki_model, add_anki_card
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration to get supported languages and proficiency levels
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
supported_languages = config['languages']['supported_source_languages']
supported_proficiency_levels = config['languages']['supported_proficiency_levels']

if __name__ == "__main__":
    # Input word
    word = input("Enter a German or source language word: ")

    # Display supported source languages and get user's choice
    print("\nSupported source languages:")
    for idx, lang in enumerate(supported_languages, 1):
        print(f"{idx}. {lang}")
    source_language_index = int(input("Enter the number corresponding to the source language: "))
    source_language = supported_languages[source_language_index - 1]

    # Display supported proficiency levels and get user's choice
    print("\nSupported proficiency levels:")
    for idx, level in enumerate(supported_proficiency_levels, 1):
        print(f"{idx}. {level}")
    proficiency_level_index = int(input("Enter the number corresponding to the proficiency level: "))
    proficiency_level = supported_proficiency_levels[proficiency_level_index - 1]

    # Generate word profile
    word_profile = get_translation_and_example(word, source_language, proficiency_level)

    # Generate image and TTS audio based on the word profile
    generate_image_from_profile(word_profile)
    generate_tts_from_profile(word_profile)

    # Create the Anki model if not already present
    create_anki_model()

    # Add the word profile to Anki as a new card
    add_anki_card(word_profile)
