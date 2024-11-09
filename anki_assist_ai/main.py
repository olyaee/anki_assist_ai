from utils.example_generator import get_translation_and_example, generate_image_from_profile, generate_tts_from_profile
from utils.anki_utils import create_anki_model, add_anki_card
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration to get supported languages
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
supported_languages = config['languages']['supported_source_languages']

if __name__ == "__main__":

    word = input("Enter a German or source language word: ")
    print("Supported source languages:")
    for idx, lang in enumerate(supported_languages, 1):
        print(f"{idx}. {lang}")
    source_language_index = int(input("Enter the number corresponding to the source language: "))
    source_language = supported_languages[source_language_index - 1]

    # Generate word profile
    word_profile = get_translation_and_example(word, source_language, proficiency_level)
    generate_image_from_profile(word_profile)
    generate_tts_from_profile(word_profile)

    # Create the Anki model if not present
    create_anki_model()

    # Add word data to Anki
    add_anki_card(word_profile)
