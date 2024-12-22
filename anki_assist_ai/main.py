from utils.example_generator import get_translation_and_example, generate_image_from_profile, generate_tts_from_profile
from utils.anki_utils import create_anki_model, add_or_update_anki_card
import logging
import yaml
import pandas as pd
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration to get supported languages and proficiency levels
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
supported_languages = config['languages']['supported_source_languages']
supported_proficiency_levels = config['languages']['supported_proficiency_levels']

def single_word_profile(vocabulary_file, grammar_file, word, source_language, proficiency_level, generate_image=False, generate_tts=False, add_to_anki=False, lecture=1, ubung=1):
    word_profile = get_translation_and_example(word, source_language, proficiency_level, vocabulary_file, grammar_file, lecture, ubung)
    print(word_profile)
    if generate_image:
        generate_image_from_profile(word_profile)
    if generate_tts:
        generate_tts_from_profile(word_profile)
    if add_to_anki:
        add_or_update_anki_card(word_profile)
    return word_profile

def word_list_profile(vocabulary_file, grammar_file, word_csv, source_language, proficiency_level, generate_image=False, generate_tts=False, add_to_anki=False):
    # Loop through each row in the CSV
    for index, row in word_csv.iterrows():
        word = row.iloc[0]  # Get word from first column
        lecture = row.iloc[1]  # Get lecture from second column 
        ubung = row.iloc[2]  # Get ubung from third column
        single_word_profile(vocabulary_file, grammar_file, word, source_language, proficiency_level, generate_image, generate_tts, add_to_anki, lecture, ubung)

if __name__ == "__main__":
    create_anki_model()

    source_language = 'English'
    proficiency_level = 'B1.1'
    vocabulary_file = 'b1.1/word_exercises.csv'
    grammar_file = 'b1.1/grammer.md'
    generate_image = False
    generate_tts = False
    add_to_anki = True

    # word = input("Enter a German or source language word: ")
    # words = ["Sein", "viel", "beeilen", "eignen", "böse", "entschließen", "oft", "böse", "good"]
    # for word in words:
    #     single_word_profile(vocabulary_file, grammar_file, word, source_language, proficiency_level, generate_image, generate_tts, add_to_anki)


    # Read the CSV file
    df = pd.read_csv("/Users/ehsanolyaee/Documents/Code/anki_assist_ai/b1.1/word_exercises.csv", delimiter=';')[:1]
    word_list_profile(vocabulary_file, grammar_file, df, source_language, proficiency_level, generate_image, generate_tts, add_to_anki)