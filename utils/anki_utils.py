import requests
import os
import base64
import yaml
import logging

# Load configuration from config.yml
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Retrieve configuration values
anki_connect_url = config['anki']['connect_url']
deck_name = config['anki']['deck_name']
model_name = config['anki']['model_name']
card_templates = config['anki']['card_templates']
files_dir = config['files']['directory']

def create_anki_model():
    """Creates a custom Anki model if it doesn't exist.

    Sends a request to the AnkiConnect API to create a model with the specified
    fields and card templates.

    Returns:
        None
    """
    payload = {
        "action": "createModel",
        "version": 6,
        "params": {
            "modelName": model_name,
            "inOrderFields": [
                "Wort_DE", "Wortarten", "Wort_SL", "Artikel", "Plural", "Praesens", "Praeteritum", "Perfekt",
                "Satz1_DE", "Satz1_SL", "Satz2_DE", "Satz2_SL", "Satz3_DE", "Satz3_SL",
                "Audio_Wort", "Audio_S1", "Audio_S2", "Audio_S3", "Picture"
            ],
            "cardTemplates": card_templates,
            "css": """
                .card {
                    font-family: arial;
                    font-size: 20px;
                    text-align: center;
                    color: black;
                    background-color: white;
                }
            """
        }
    }

    response = requests.post(anki_connect_url, json=payload)
    result = response.json()
    if result.get("error") is None:
        logging.info(f"Model '{model_name}' created successfully or already exists.")
    else:
        logging.error(f"Failed to create model '{model_name}': {result['error']}")

def store_media_file(files_dir, word, suffix):
    """Stores a media file in Anki's media collection.

    Args:
        files_dir (str): The directory where the media files are stored.
        word (str): The word associated with the media file.
        suffix (str): The suffix of the media file (e.g., 'word.mp3').

    Returns:
        str: The name of the stored media file, or None if the file does not exist.
    """
    file_path = os.path.join(files_dir, f"{word}_{suffix}")
    try:
        with open(file_path, "rb") as file:
            file_data = base64.b64encode(file.read()).decode("ascii")
    except FileNotFoundError:
        logging.error(f"File '{file_path}' does not exist.")
        return None

    file_name = os.path.basename(file_path)
    payload = {
        "action": "storeMediaFile",
        "version": 6,
        "params": {
            "filename": file_name,
            "data": file_data
        }
    }
    response = requests.post(anki_connect_url, json=payload)
    result = response.json()
    if result.get("error") is None:
        logging.info(f"File '{file_name}' stored successfully.")
        return file_name
    else:
        logging.error(f"Failed to store file '{file_name}': {result['error']}")
        return None

def generate_media_files(files_dir, word_data):
    """Generates and stores all media files (audio, images) for a word profile.

    Handles both word audio and example sentence audio.

    Args:
        files_dir (str): The directory where the media files are stored.
        word_data (dict): The data for the word, including German word, examples, etc.

    Returns:
        dict: A dictionary with the stored media file names.
    """
    # Store word audio
    audio_word = store_media_file(files_dir, word_data['german_word'], "word.mp3")

    # Store audio for example sentences (if present)
    examples = word_data.get("examples", [])
    audio_examples = [
        store_media_file(files_dir, word_data['german_word'], f"example_{i + 1}.mp3")
        for i in range(len(examples))
    ]

    # Store the image
    image_file = store_media_file(files_dir, word_data['german_word'], "image.jpg")

    # Return dictionary with stored files
    return {
        "audio_word": audio_word,
        "audio_examples": audio_examples,
        "image": image_file,
    }

def add_anki_card(word_data):
    """Adds a card to Anki with the custom model template, deleting duplicates if necessary.

    Args:
        word_data (dict): The data for the word, including German word, classification, examples, etc.

    Returns:
        None
    """
    # Find and delete existing cards with the same German word
    existing_cards = find_existing_card(word_data["german_word"])
    if existing_cards:
        for card_id in existing_cards:
            delete_card(card_id)

    # Generate media files for the word profile
    media_files = generate_media_files(files_dir, word_data)

    # Prepare card fields
    examples = word_data.get("examples", [])
    fields = {
        "Wort_DE": word_data["german_word"],
        "Wortarten": word_data["classification"],
        "Wort_SL": word_data["source_language_translation"],
        "Artikel": word_data.get("additional_grammatical_info", {}).get("noun", {}).get("article", "") if word_data["classification"] == "(n)" else "",
        "Plural": word_data.get("additional_grammatical_info", {}).get("noun", {}).get("plural_form", "") if word_data["classification"] == "(n)" else "",
        "Praesens": ", ".join(word_data.get("additional_grammatical_info", {}).get("verb", {}).get("praesens", [])) if word_data["classification"] == "(v)" else "",
        "Praeteritum": ", ".join(word_data.get("additional_grammatical_info", {}).get("verb", {}).get("praeteritum", [])) if word_data["classification"] == "(v)" else "",
        "Perfekt": ", ".join(word_data.get("additional_grammatical_info", {}).get("verb", {}).get("perfekt", [])) if word_data["classification"] == "(v)" else "",
        "Satz1_DE": examples[0]["german_example"] if len(examples) > 0 else "",
        "Satz1_SL": examples[0]["source_example_translation"] if len(examples) > 0 else "",
        "Satz2_DE": examples[1]["german_example"] if len(examples) > 1 else "",
        "Satz2_SL": examples[1]["source_example_translation"] if len(examples) > 1 else "",
        "Satz3_DE": examples[2]["german_example"] if len(examples) > 2 else "",
        "Satz3_SL": examples[2]["source_example_translation"] if len(examples) > 2 else "",
        "Audio_Wort": f"[sound:{media_files['audio_word']}]" if media_files["audio_word"] else "",
        "Audio_S1": f"[sound:{media_files['audio_examples'][0]}]" if len(media_files["audio_examples"]) > 0 else "",
        "Audio_S2": f"[sound:{media_files['audio_examples'][1]}]" if len(media_files["audio_examples"]) > 1 else "",
        "Audio_S3": f"[sound:{media_files['audio_examples'][2]}]" if len(media_files["audio_examples"]) > 2 else "",
        "Picture": f"<img src='{media_files['image']}'>" if media_files["image"] else "",
    }

    # Add the card to Anki
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": fields,
                "tags": ["german-learning", "auto-added"]
            }
        }
    }

    response = requests.post(anki_connect_url, json=payload)
    result = response.json()
    if result.get("error") is None:
        logging.info(f"Card for '{word_data['german_word']}' added successfully!")
    else:
        logging.error(f"Failed to add card: {result['error']}")

def find_existing_card(german_word):
    """Finds existing cards in Anki with the same German word.

    Args:
        german_word (str): The German word to search for.

    Returns:
        list: A list of note IDs for the existing cards, or an empty list if none are found.
    """
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f'"deck:{deck_name}" Wort_DE:{german_word}'
        }
    }
    response = requests.post(anki_connect_url, json=payload)
    result = response.json()
    if result.get("error") is None:
        return result.get("result", [])
    else:
        logging.error(f"Failed to find existing card: {result['error']}")
        return []

def delete_card(card_id):
    """Deletes a card in Anki given its note ID.

    Args:
        card_id (int): The note ID of the card to delete.

    Returns:
        None
    """
    payload = {
        "action": "deleteNotes",
        "version": 6,
        "params": {
            "notes": [card_id]
        }
    }
    response = requests.post(anki_connect_url, json=payload)
    result = response.json()
    if result.get("error") is None:
        logging.info(f"Card with ID {card_id} deleted successfully.")
    else:
        logging.error(f"Failed to delete card: {result['error']}")
