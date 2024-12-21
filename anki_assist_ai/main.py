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

def single_word_profile(vocabulary_file, grammar_file, word, source_language, proficiency_level, generate_image=False, generate_tts=False, add_to_anki=False):
    word_profile = get_translation_and_example(word, source_language, proficiency_level, vocabulary_file, grammar_file, 1, 1)
    print(word_profile)
    if generate_image:
        generate_image_from_profile(word_profile)
    if generate_tts:
        generate_tts_from_profile(word_profile)
    if add_to_anki:
        add_or_update_anki_card(word_profile)

if __name__ == "__main__":
    # Input word
    word = input("Enter a German or source language word: ")

    create_anki_model()

    source_language = 'English'
    proficiency_level = 'B1.1'
    vocabulary_file = 'b1.1/word_exercises.csv'
    grammar_file = 'b1.1/grammer.md'
    generate_image = False
    generate_tts = False
    add_to_anki = True

    single_word_profile(vocabulary_file, grammar_file, word, source_language, proficiency_level, generate_image, generate_tts, add_to_anki)
    
    

    # # Read the CSV file
    # df = pd.read_csv('/Users/ehsanolyaee/Documents/Code/anki_assist_ai/final_table.csv')
    # # Filter the dataframe to include only rows after lecture 7
    # # print(df.columns)

    # df = df[df['Lecture'] > 6]

    # Make a list of all the items in the first column
    # first_column_items = df.iloc[:, 0].tolist()
    # print(first_column_items)

    # Display the first few rows of the dataframe



    # Generate image and TTS audio based on the word profile
    # generate_image_from_profile(word_profile)
    # generate_tts_from_profile(word_profile)

    # # Directory containing the JSON files
    # json_directory = '/Users/ehsanolyaee/Documents/Code/anki_assist_ai/files'

    # # List to store the JSON data
    # json_data_list = []

    # # Iterate through all files in the directory
    # for filename in os.listdir(json_directory):
    #     if filename.endswith('.json'):
    #         file_path = os.path.join(json_directory, filename)
    #         with open(file_path, 'r') as json_file:
    #             json_data = json.load(json_file)
    #             json_data_list.append(json_data)

    # # Sort the list by "Lecture" and then by "Ubung"
    # json_data_list.sort(key=lambda x: (x['lecture'], x['ubung']))

    # # Create the Anki model if not already present

    # # Print the sorted list (optional)
    # for word_profile in json_data_list:
    #     try:
    #         print(f"{json_data_list.index(word_profile)}:", word_profile.get('german_word'), word_profile.get('lecture'), word_profile.get('ubung'))
    #         # generate_image_from_profile(word_profile)
    #         # generate_tts_from_profile(word_profile)
    #         add_or_update_anki_card(word_profile)
    #     except Exception as e:
    #         print(f"Error processing {json_data_list.index(word_profile)}: {word_profile.get('german_word')}: {str(e)}")
    #         continue

    # # Add the word profile to Anki as a new card
    # # add_anki_card(word_profile)
