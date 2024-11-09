from PIL import Image
import requests
from openai import OpenAI
import openai
import json
import random
import os
import yaml
from dotenv import load_dotenv
import logging
import sys

# Load environment variables
load_dotenv()
# Retrieve the API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    logging.error("OpenAI API key not found. Please set it in the .env file.")
    sys.exit(1)

# Load configuration from config.yml
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Retrieve configuration values
api_key = os.getenv('OPENAI_API_KEY')
files_dir = config['files']['directory']
deck_name = config['anki']['deck_name']
text_model = config['openai']['text_model']
image_model = config['openai']['image_model']
image_size = config['openai']['image_size']
tts_model = config['openai']['tts_model']
system_message_template = config['prompt']['system_message']
json_schema = config['schema']

# Initialize OpenAI API key
client = OpenAI(api_key=api_key)
openai.api_key = api_key

def get_translation_and_example(word, source_language, proficiency_level):
    """Generate translation and example sentences for a given word.
    Args:
        word (str): The word to generate translation and examples for.
        source_language (str): The source language of the word.
        proficiency_level (str): The proficiency level of the user.
    Returns:
        dict: A dictionary containing the word profile with translation and example sentences.
    Raises:
        Exception: If there is an error in generating the word profile.
    """
    """Generate translation and example sentences for a given word."""
    system_message = system_message_template.format(source_language=source_language, proficiency_level=proficiency_level)
    response = client.chat.completions.create(
        model=text_model,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": word
            }
        ],
        functions=[
            {
                "name": "generate_word_profile",
                "description": "Generates a word profile with translations and examples.",
                "parameters": json_schema
            }
        ],
        function_call={"name": "generate_word_profile"}
    )

    # Parse the structured output
    word_profile_arguments = response.choices[0].message.function_call.arguments
    word_profile = json.loads(word_profile_arguments)
    logging.info(word_profile)

    # Save the word_profile as JSON
    file_path = os.path.join(files_dir, f"{word_profile['german_word']}_profile.json")
    with open(file_path, 'w') as json_file:
        json.dump(word_profile, json_file, indent=4)
    logging.info(f"Word profile saved as {file_path}")

    # Extract and log token usage information
    logging.info(f"Prompt tokens: {response.usage.prompt_tokens}")
    logging.info(f"Completion tokens: {response.usage.completion_tokens}")
    logging.info(f"Total tokens: {response.usage.total_tokens}")

    return word_profile

def generate_image_from_profile(word_profile):
    """
    Generate an image based on the word profile.
    This function creates an image based on the provided word profile by generating an image prompt,
    retrieving the generated image, resizing it, and saving it to a specified directory.
    Args:
        word_profile (dict): A dictionary containing the word profile information. It should include
                             a key 'german_word' which will be used to name the saved image file.
    Returns:
        None
    """
    """Generate an image based on the word profile."""
    image_prompt = f"Create an image for the word {word_profile}."

    image_response = client.images.generate(
        model=image_model,
        prompt=image_prompt,
        n=1,
        size=image_size,
    )
    # Retrieve and download the image
    image_url = image_response.data[0].url
    image_data = requests.get(image_url).content

    temp_image_path = os.path.join(files_dir, "temp_image.jpg")
    with open(temp_image_path, 'wb') as temp_image_file:
        temp_image_file.write(image_data)

    # Open, resize, and save the image
    with Image.open(temp_image_path) as img:
        resized_img = img.resize((256, 256))
        resized_image_filename = os.path.join(files_dir, f"{word_profile['german_word']}_image.jpg")
        resized_img.save(resized_image_filename)
    logging.info(f"Resized image saved as {resized_image_filename}")
    # Remove the temporary file
    os.remove(temp_image_path)

def generate_tts_from_profile(word_profile):
    """Generate TTS audio files for the word and example sentences.

    Args:
        word_profile (dict): A dictionary containing the word profile information. It should include
                             a key 'german_word' and a list of 'examples' with 'german_example' sentences.

    Returns:
        None
    """
    voice = random.choice(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

    # Generate TTS for the main German word
    main_word = word_profile['german_word']

    def save_tts_audio(input_text, file_path, voice):
        """Helper to generate and save TTS audio.

        Args:
            input_text (str): The text to convert to speech.
            file_path (str): The path to save the audio file.
            voice (str): The voice to use for TTS.

        Returns:
            None
        """
        tts_response = openai.audio.speech.create(
            model=tts_model,
            input=input_text,
            voice=voice
        )
        tts_response.stream_to_file(file_path)
        logging.info(f"Audio saved as {file_path}")
    # Use in generate_tts_from_profile
    save_tts_audio(main_word, os.path.join(files_dir, f"{main_word}_word.mp3"), voice)

    # Generate TTS for each example sentence
    for index, example in enumerate(word_profile['examples']):
        save_tts_audio(
            example['german_example'],
            os.path.join(files_dir, f"{main_word}_example_{index + 1}.mp3"),
            voice
        )
