from PIL import Image
import requests
from google import genai
from google.genai import types
import json
import random
import os
import yaml
from dotenv import load_dotenv
import logging
import sys
import base64
import wave
import time
from .cost_calculator import calculate_cost

# Load environment variables
load_dotenv()
# Retrieve API key from environment variables
google_api_key = os.getenv('GOOGLE_AI_API_KEY')

if not google_api_key:
    logging.error("Google AI API key not found. Please set GOOGLE_AI_API_KEY in the .env file.")
    sys.exit(1)

# Initialize Gemini client
client = genai.Client(api_key=google_api_key)

# Load configuration from config.yml
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Retrieve configuration values
files_dir = config['files']['directory']

# Create files directory if it doesn't exist
os.makedirs(files_dir, exist_ok=True)

deck_name = config['anki']['deck_name']
text_model = config['gemini']['text_model']
image_model = config['gemini']['image_model']
image_aspect_ratio = config['gemini']['image_aspect_ratio']
image_size = config['gemini']['image_size']
tts_model = config['gemini']['tts_model']
tts_voices = config['gemini']['tts_voices']
system_message_template = config['prompt']['system_message']
image_prompt_template = config['prompt']['image_prompt']
json_schema = config['schema']

def read_grammar(grammar_file, lecture_number):
    """Read the grammar content for a specific lecture from grammar.md.
    
    Args:
        grammar_file (str): Path to the grammar file
        lecture_number (int): The lecture number to extract grammar for
        
    Returns:
        str: The grammar content for the specified lecture
    """
    try:
        with open(grammar_file, 'r') as file:
            content = file.read()
            
            # Find the start marker for the requested lecture
            current_lecture_marker = f"### Lektion {lecture_number}"
            next_lecture_marker = f"### Lektion {lecture_number + 1}"
            
            # Find the start position of the current lecture
            start_pos = content.find(current_lecture_marker)
            if start_pos == -1:
                return ""  # Lecture not found
                
            # Find the start position of the next lecture
            end_pos = content.find(next_lecture_marker)
            if end_pos == -1:
                # If there's no next lecture, take until the end
                section_content = content[start_pos:].strip()
            else:
                # Take content between current and next lecture
                section_content = content[start_pos:end_pos].strip()
            
            # Clean up the content by removing %%% markers
            return section_content.replace('%%%', '').strip()
                
    except Exception as e:
        logging.error(f"Error reading grammar for lecture {lecture_number}: {e}")
        return ""

def get_translation_and_example(word, source_language, proficiency_level, grammar_file, lecture_number, ubung):
    """Generate translation and example sentences for a given word."""
    # Read grammar for specific lecture
    grammar = read_grammar(grammar_file, lecture_number)

    # Construct the complete prompt with system message
    complete_prompt = f"<Grammar>\n{grammar}\n</Grammar>\n\n{system_message_template}"
    system_message = complete_prompt.format(source_language=source_language, proficiency_level=proficiency_level, lecture_number=lecture_number)
    prompt = f"{system_message}\n\nWord: {word}"

    # Define function declaration
    function = types.FunctionDeclaration(
        name='generate_word_profile',
        description='Generates a word profile with translations and examples.',
        parameters_json_schema=json_schema
    )

    # Create tool with function declaration
    tool = types.Tool(function_declarations=[function])

    # Generate content with function calling
    response = client.models.generate_content(
        model=text_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[tool],
            temperature=0.7
        )
    )

    # Extract function call response
    function_call = response.candidates[0].content.parts[0].function_call
    word_profile = dict(function_call.args)

    logging.info(word_profile)

    # Add lecture and ubung to the word profile
    word_profile['lecture'] = lecture_number
    word_profile['ubung'] = ubung

    # Save the word_profile as JSON
    file_path = os.path.join(files_dir, f"{word_profile['german_word']}_profile.json")
    with open(file_path, 'w') as json_file:
        json.dump(word_profile, json_file, indent=4)
    logging.info(f"Word profile saved as {file_path}")

    # Extract and log token usage information
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        logging.info(f"Prompt tokens: {usage.prompt_token_count}")
        logging.info(f"Completion tokens: {usage.candidates_token_count}")
        logging.info(f"Total tokens: {usage.total_token_count}")

    # Calculate and log cost information
    input_text = prompt
    output_text = json.dumps(word_profile)
    cost_info = calculate_cost(input_text, output_text, text_model)
    logging.info(f"API Call Cost Information: {json.dumps(cost_info, indent=2)}")

    return word_profile

def generate_image_from_profile(word_profile):
    """
    Generate an image based on the word profile using Gemini native image generation.
    Args:
        word_profile (dict): A dictionary containing the word profile information.
    Returns:
        None
    """
    # Format the image prompt with the word profile data
    image_prompt = image_prompt_template.format(german_word=word_profile['original_word'])

    # Generate image with specified config
    response = client.models.generate_content(
        model=image_model,
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    # Extract image data from response
    image_part = response.candidates[0].content.parts[0]

    if hasattr(image_part, 'inline_data'):
        # Get image data
        image_data = image_part.inline_data.data

        # Save as temporary file
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
    else:
        logging.error("No image data found in response")

def generate_tts_from_profile(word_profile):
    """Generate TTS audio files for the word and example sentences using Gemini TTS.

    Args:
        word_profile (dict): A dictionary containing the word profile information.

    Returns:
        None
    """
    # Randomly select a voice from configured voices
    voice = random.choice(tts_voices)

    # Generate TTS for the main German word
    main_word = word_profile['german_word']

    def save_tts_audio(input_text, file_path, voice_name):
        """Helper to generate and save TTS audio using Gemini.

        Args:
            input_text (str): The text to convert to speech.
            file_path (str): The path to save the audio file.
            voice_name (str): The Gemini voice to use for TTS.

        Returns:
            None
        """
        # Generate audio with voice config
        response = client.models.generate_content(
            model=tts_model,
            contents=input_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
        )

        # Extract audio data from response
        if not response.candidates or not response.candidates[0].content:
            logging.error(f"No valid response received for TTS: {input_text}")
            return

        audio_part = response.candidates[0].content.parts[0]

        if hasattr(audio_part, 'inline_data'):
            # Gemini TTS returns base64-encoded PCM audio (24kHz, 16-bit, mono)
            audio_base64 = audio_part.inline_data.data

            # Decode base64 to raw PCM bytes
            if isinstance(audio_base64, str):
                pcm_data = base64.b64decode(audio_base64)
            else:
                # Already bytes
                pcm_data = audio_base64

            # Convert PCM to WAV format
            # Gemini TTS format: 24kHz sample rate, 16-bit, 1 channel (mono)
            wav_path = file_path.replace('.mp3', '.wav')
            with wave.open(wav_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(24000)  # 24kHz
                wav_file.writeframes(pcm_data)

            logging.info(f"Audio saved as {wav_path}")
        else:
            logging.error(f"No audio data found in response for {input_text}")

    # Generate TTS for the word itself (optional - skip on error)
    logging.info("Generating word audio...")
    try:
        # Add context to single words to help TTS API (some models struggle with single words)
        word_text = main_word if len(main_word.split()) > 1 else f"Das Wort ist {main_word}."
        save_tts_audio(
            word_text,
            os.path.join(files_dir, f"{main_word}_word.mp3"),
            voice
        )
        # Rate limiting: 10 requests/minute = 1 request per 6 seconds
        # Adding 7 seconds to be safe
        time.sleep(7)
    except Exception as e:
        logging.warning(f"Skipping word audio due to error: {e}")

    # Generate TTS for each example sentence
    for index, example in enumerate(word_profile['examples']):
        save_tts_audio(
            example['german_example'],
            os.path.join(files_dir, f"{main_word}_example_{index + 1}.mp3"),
            voice
        )
        # Rate limiting delay between each TTS request
        if index < len(word_profile['examples']) - 1:  # Don't sleep after last one
            time.sleep(7)
