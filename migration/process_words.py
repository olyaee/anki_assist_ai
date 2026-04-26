#!/usr/bin/env python3
"""
Clean, pass-based word processor for Anki.

Works in 4 passes:
1. Generate all profiles (until quota hits)
2. Generate all images (until quota hits)
3. Generate all TTS (until quota hits)
4. Sync all to Anki

Run again and it continues where it left off.
"""
import argparse
import base64
import json
import logging
import os
import random
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Load environment
load_dotenv()

# Globals
config = None
client = None
clients = []  # Multiple clients for API key rotation
files_dir = None


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config():
    """Load configuration and initialize Gemini client."""
    global config, client, files_dir

    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)

    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        logging.error("GOOGLE_AI_API_KEY not found in environment")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Build list of TTS clients from all available API keys
    api_keys = [api_key]
    for i in range(2, 10):
        extra = os.getenv(f'GOOGLE_AI_API_KEY_{i}')
        if extra:
            api_keys.append(extra)
    for key in api_keys:
        clients.append(genai.Client(api_key=key))
    files_dir = Path(config['files']['directory'])
    files_dir.mkdir(exist_ok=True)


def normalize_word(word):
    """Extract base word: 'himmel, der, -' -> 'Himmel'"""
    return word.split(',')[0].strip().capitalize()


def sanitize_filename(name):
    """Remove/replace characters invalid in file paths."""
    # Replace / and \ with hyphen, remove other problematic chars
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, '-')
    return name


def update_csv_timestamp(csv_path, word, column):
    """Update timestamp in CSV."""
    try:
        df = pd.read_csv(csv_path, delimiter=';')
        word_base = normalize_word(word)
        mask = df.iloc[:, 0].apply(normalize_word) == word_base

        if mask.any():
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.loc[mask, column] = timestamp
            df.to_csv(csv_path, sep=';', index=False)
    except Exception as e:
        logging.error(f"Failed to update CSV: {e}")


def read_grammar(grammar_file, lecture_number):
    """Read grammar for specific lecture."""
    try:
        with open(grammar_file, 'r') as f:
            content = f.read()

        current = f"### Lektion {lecture_number}"
        next_marker = f"### Lektion {lecture_number + 1}"

        start = content.find(current)
        if start == -1:
            return ""

        end = content.find(next_marker)
        section = content[start:end].strip() if end != -1 else content[start:].strip()
        return section.replace('%%%', '').strip()
    except Exception as e:
        logging.error(f"Error reading grammar: {e}")
        return ""


def generate_profile(word, lecture, ubung, source_language, proficiency_level, grammar_file):
    """Generate word profile JSON."""
    try:
        grammar = read_grammar(grammar_file, lecture)

        system_template = config['prompt']['system_message']
        system_message = f"<Grammar>\n{grammar}\n</Grammar>\n\n{system_template}"
        prompt = system_message.format(
            source_language=source_language,
            proficiency_level=proficiency_level,
            lecture_number=lecture
        ) + f"\n\nWord: {word}"

        function = types.FunctionDeclaration(
            name='generate_word_profile',
            description='Generates word profile with translations and examples',
            parameters_json_schema=config['schema']
        )

        tool = types.Tool(function_declarations=[function])

        response = client.models.generate_content(
            model=config['gemini']['text_model'],
            contents=prompt,
            config=types.GenerateContentConfig(tools=[tool], temperature=0.7)
        )

        if not response.candidates or not response.candidates[0].content:
            return None

        function_call = response.candidates[0].content.parts[0].function_call
        word_profile = dict(function_call.args)
        word_profile['lecture'] = lecture
        word_profile['ubung'] = ubung

        # Save
        normalized = normalize_word(word)
        profile_path = files_dir / f"{normalized}_profile.json"
        with open(profile_path, 'w') as f:
            json.dump(word_profile, f, indent=4)

        return word_profile
    except Exception as e:
        logging.error(f"Profile generation failed: {e}")
        return None


def generate_image(word_profile):
    """Generate image from profile."""
    try:
        word = word_profile['german_word']
        normalized = sanitize_filename(normalize_word(word))
        image_path = files_dir / f"{normalized}_image.jpg"

        if image_path.exists():
            return True

        # Randomly select an image style for variety
        image_style = random.choice(config['prompt']['image_styles'])
        logging.info(f"  Style: {image_style.split(':')[0]}")

        prompt = config['prompt']['image_prompt'].format(
            german_word=word_profile.get('original_word', word),
            image_style=image_style
        )

        response = client.models.generate_content(
            model=config['gemini']['image_model'],
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )

        image_part = response.candidates[0].content.parts[0]
        if not hasattr(image_part, 'inline_data'):
            return False

        image_data = image_part.inline_data.data

        temp_path = files_dir / "temp_image.jpg"
        with open(temp_path, 'wb') as f:
            f.write(image_data)

        with Image.open(temp_path) as img:
            resized = img.resize((256, 256))
            resized.save(image_path)

        temp_path.unlink()
        return True
    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        return False


def add_silence_to_audio(audio_path, duration_ms=1000):
    """Add silence to beginning of audio using sox."""
    try:
        temp_dir = Path("./temp")
        temp_dir.mkdir(exist_ok=True)
        output = temp_dir / "output.wav"

        subprocess.run(
            ["sox", str(audio_path), str(output), "pad", f"{duration_ms/1000}", "0"],
            check=True,
            capture_output=True
        )

        os.replace(output, audio_path)

        if output.exists():
            output.unlink()
        temp_dir.rmdir()
    except:
        pass  # sox not installed or failed, skip silence


def generate_tts(word_profile, tts_client=None, tts_model=None):
    """Generate TTS audio for 3 examples. Returns 'ok', 'quota', or 'error'."""
    try:
        word = word_profile['german_word']
        normalized = sanitize_filename(normalize_word(word))

        use_client = tts_client or client
        use_model = tts_model or config['gemini']['tts_models'][0]
        voice = random.choice(config['gemini']['tts_voices'])
        examples = word_profile.get('examples', [])

        # Check if all expected files already exist
        all_exist = all(
            (files_dir / f"{normalized}_example_{i+1}.wav").exists()
            for i, ex in enumerate(examples[:3])
            if ex.get('german_example', '')
        )
        if all_exist:
            return 'ok'

        for idx, example in enumerate(examples[:3]):
            text = example.get('german_example', '')
            if not text:
                continue

            audio_path = files_dir / f"{normalized}_example_{idx+1}.wav"
            if audio_path.exists():
                continue

            response = use_client.models.generate_content(
                model=use_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    )
                )
            )

            if not response.candidates or not response.candidates[0].content:
                continue

            audio_part = response.candidates[0].content.parts[0]
            if not hasattr(audio_part, 'inline_data'):
                continue

            audio_base64 = audio_part.inline_data.data
            pcm_data = base64.b64decode(audio_base64) if isinstance(audio_base64, str) else audio_base64

            with wave.open(str(audio_path), 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(pcm_data)

            add_silence_to_audio(audio_path, 1000)

            if idx < 2:
                time.sleep(7)

        # Only return 'ok' if all expected files now exist
        all_created = all(
            (files_dir / f"{normalized}_example_{i+1}.wav").exists()
            for i, ex in enumerate(examples[:3])
            if ex.get('german_example', '')
        )
        if all_created:
            return 'ok'
        logging.warning(f"TTS incomplete for {word} - some files missing")
        return 'error'
    except Exception as e:
        err_str = str(e)
        if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
            logging.warning(f"TTS quota hit on {use_model}: {e}")
            return 'quota'
        logging.error(f"TTS generation failed: {e}")
        return 'error'


def create_anki_model():
    """Create Anki model if needed."""
    try:
        url = config['anki']['connect_url']
        model_name = config['anki']['model_name']

        payload = {
            "action": "createModel",
            "version": 6,
            "params": {
                "modelName": model_name,
                "inOrderFields": [
                    "Wort_DE", "Wort_SL", "Wortarten", "Artikel", "Plural",
                    "Praesens", "Praeteritum", "Perfekt", "Reflexiv", "Praeposition", "Unregelmaeßig_Verb",
                    "Komparativ", "Superlativ", "Unregelmaeßig_Adjective",
                    "Satz1_DE", "Satz1_SL", "Satz2_DE", "Satz2_SL", "Satz3_DE", "Satz3_SL",
                    "Audio_Wort", "Audio_S1", "Audio_S2", "Audio_S3", "Bild",
                    "Benutzerkommentare"
                ],
                "cardTemplates": config['anki']['card_templates'],
                "css": ".card { font-family: arial; font-size: 20px; text-align: center; }"
            }
        }

        requests.post(url, json=payload)
    except:
        pass


def store_media_file(word, suffix):
    """Store media file in Anki."""
    try:
        url = config['anki']['connect_url']
        file_path = files_dir / f"{word}_{suffix}"

        if not file_path.exists():
            return None

        with open(file_path, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('ascii')

        payload = {
            "action": "storeMediaFile",
            "version": 6,
            "params": {"filename": file_path.name, "data": file_data}
        }

        response = requests.post(url, json=payload)
        if response.json().get("error"):
            return None

        return file_path.name
    except:
        return None


def sync_to_anki(word_profile):
    """Add or update Anki card."""
    try:
        url = config['anki']['connect_url']
        deck_name = config['anki']['deck_name']
        model_name = config['anki']['model_name']
        word = word_profile['german_word']
        normalized = sanitize_filename(normalize_word(word))

        # Store media
        audio_examples = [
            store_media_file(normalized, f"example_{i+1}.wav") for i in range(3)
        ]
        image_file = store_media_file(normalized, "image.jpg")

        # Build fields
        examples = word_profile.get('examples', [])
        classification = word_profile.get('classification', '')
        info = word_profile.get('additional_grammatical_info', {})

        fields = {
            "Wort_DE": word,
            "Wortarten": classification,
            "Wort_SL": ", ".join(word_profile.get("source_language_translation", [])),
            "Artikel": info.get("noun", {}).get("article", "") if classification == "(n)" else "",
            "Plural": info.get("noun", {}).get("plural_form", "") if classification == "(n)" else "",
            "Praesens": info.get("verb", {}).get("praesens", "") if classification == "(v)" else "",
            "Praeteritum": info.get("verb", {}).get("praeteritum", "") if classification == "(v)" else "",
            "Perfekt": info.get("verb", {}).get("perfekt", "") if classification == "(v)" else "",
            "Reflexiv": "(sich)" if info.get("verb", {}).get("reflexive", False) else "",
            "Praeposition": (
                info.get("verb", {}).get("praeposition", "") if classification == "(v)" else
                info.get("adjective", {}).get("praeposition", "") if classification == "(adj)" else ""
            ),
            "Unregelmaeßig_Verb": "Unregelmäßig" if classification == "(v)" and info.get("verb", {}).get("irregular", False) else "",
            "Unregelmaeßig_Adjective": "Unregelmäßig" if classification == "(adj)" and info.get("adjective", {}).get("irregular", False) else "",
            "Komparativ": info.get("adjective", {}).get("comparative", "") if classification == "(adj)" and info.get("adjective", {}).get("irregular", False) else "",
            "Superlativ": info.get("adjective", {}).get("superlative", "") if classification == "(adj)" and info.get("adjective", {}).get("irregular", False) else "",
            "Satz1_DE": examples[0]["german_example"] if len(examples) > 0 else "",
            "Satz1_SL": examples[0]["source_example_translation"] if len(examples) > 0 else "",
            "Satz2_DE": examples[1]["german_example"] if len(examples) > 1 else "",
            "Satz2_SL": examples[1]["source_example_translation"] if len(examples) > 1 else "",
            "Satz3_DE": examples[2]["german_example"] if len(examples) > 2 else "",
            "Satz3_SL": examples[2]["source_example_translation"] if len(examples) > 2 else "",
            "Audio_Wort": "",
            "Audio_S1": f"[sound:{audio_examples[0]}]" if audio_examples[0] else "",
            "Audio_S2": f"[sound:{audio_examples[1]}]" if audio_examples[1] else "",
            "Audio_S3": f"[sound:{audio_examples[2]}]" if audio_examples[2] else "",
            "Bild": f"<img src='{image_file}'>" if image_file else "",
            "Benutzerkommentare": ""
        }

        # Check existing
        search = {
            "action": "findNotes",
            "version": 6,
            "params": {"query": f'"deck:{deck_name}" Wort_DE:{word}'}
        }

        existing = requests.post(url, json=search).json().get("result", [])

        if existing:
            # Update
            for card_id in existing:
                update = {
                    "action": "updateNoteFields",
                    "version": 6,
                    "params": {"note": {"id": card_id, "fields": fields}}
                }
                requests.post(url, json=update)
        else:
            # Add new
            add = {
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
            requests.post(url, json=add)

        return True
    except Exception as e:
        logging.error(f"Anki sync failed: {e}")
        return False


def main():
    """Main entry point - 4 passes."""
    parser = argparse.ArgumentParser(description='Process words in passes')
    parser.add_argument('--csv', required=True, help='CSV file path')
    parser.add_argument('--grammar', required=True, help='Grammar file path')
    parser.add_argument('--language', default='English', help='Source language')
    parser.add_argument('--level', default='B1.1', help='Proficiency level')
    parser.add_argument('--skip-anki', action='store_true', help='Skip Anki sync')

    args = parser.parse_args()

    setup_logging()
    load_config()

    # Load CSV
    df = pd.read_csv(args.csv, delimiter=';')
    logging.info(f"Loaded {len(df)} words from CSV\n")

    # Ensure tracking columns exist
    for col in ['profile_timestamp', 'image_timestamp', 'tts_1_timestamp', 'tts_2_timestamp', 'tts_3_timestamp']:
        if col not in df.columns:
            df[col] = ''
    df.to_csv(args.csv, sep=';', index=False)

    # Create Anki model
    if not args.skip_anki:
        create_anki_model()

    # PASS 1: PROFILES
    logging.info("="*60)
    logging.info("PASS 1: GENERATING PROFILES")
    logging.info("="*60)

    profile_count = 0
    for idx, row in df.iterrows():
        if pd.notna(row.get('profile_timestamp')):
            continue

        word = row.iloc[0]
        lecture = int(row.iloc[1])
        ubung = row.iloc[2]

        logging.info(f"Profile: {word}")

        result = generate_profile(word, lecture, ubung, args.language, args.level, args.grammar)
        if result:
            update_csv_timestamp(args.csv, word, 'profile_timestamp')
            profile_count += 1
        else:
            logging.warning("Quota hit - stopping profile pass")
            break

    logging.info(f"✓ Profiles created: {profile_count}\n")

    # PASS 2: IMAGES
    logging.info("="*60)
    logging.info("PASS 2: GENERATING IMAGES")
    logging.info("="*60)

    # Reload CSV to get updated timestamps
    df = pd.read_csv(args.csv, delimiter=';')

    image_count = 0
    for idx, row in df.iterrows():
        if pd.isna(row.get('profile_timestamp')):
            continue
        if pd.notna(row.get('image_timestamp')):
            continue

        word = row.iloc[0]
        normalized = normalize_word(word)
        profile_path = files_dir / f"{normalized}_profile.json"

        if not profile_path.exists():
            continue

        with open(profile_path, 'r') as f:
            word_profile = json.load(f)

        logging.info(f"Image: {word}")

        if generate_image(word_profile):
            update_csv_timestamp(args.csv, word, 'image_timestamp')
            image_count += 1
        else:
            logging.warning("Quota hit - stopping image pass")
            break

    logging.info(f"✓ Images created: {image_count}\n")

    # PASS 3: TTS
    logging.info("="*60)
    logging.info("PASS 3: GENERATING TTS")
    logging.info("="*60)

    df = pd.read_csv(args.csv, delimiter=';')

    tts_count = 0
    tts_models = config['gemini']['tts_models']

    # Build all (client, model) combos to rotate through
    tts_combos = []
    for c in clients:
        for m in tts_models:
            tts_combos.append((c, m))
    logging.info(f"TTS rotation: {len(clients)} API key(s) x {len(tts_models)} model(s) = {len(tts_combos)} combos")

    exhausted_combos = set()
    combo_idx = 0

    for idx, row in df.iterrows():
        if pd.isna(row.get('profile_timestamp')):
            continue
        if pd.notna(row.get('tts_1_timestamp')):
            continue

        word = row.iloc[0]
        normalized = normalize_word(word)
        profile_path = files_dir / f"{normalized}_profile.json"

        if not profile_path.exists():
            continue

        with open(profile_path, 'r') as f:
            word_profile = json.load(f)

        logging.info(f"TTS: {word}")

        # Try combos until one works or all exhausted
        result = 'quota'
        attempts = 0
        while attempts < len(tts_combos):
            if combo_idx in exhausted_combos:
                combo_idx = (combo_idx + 1) % len(tts_combos)
                attempts += 1
                continue

            tts_client, tts_model = tts_combos[combo_idx]
            result = generate_tts(word_profile, tts_client=tts_client, tts_model=tts_model)

            if result == 'ok':
                logging.info(f"  ✓ using {tts_model} (combo {combo_idx})")
                # Rotate to next combo for next word
                combo_idx = (combo_idx + 1) % len(tts_combos)
                break
            elif result == 'quota':
                logging.warning(f"  ✗ quota exhausted on {tts_model} (combo {combo_idx})")
                exhausted_combos.add(combo_idx)
                combo_idx = (combo_idx + 1) % len(tts_combos)
                attempts += 1
            else:
                # Other error, try next combo
                combo_idx = (combo_idx + 1) % len(tts_combos)
                attempts += 1

        if result == 'ok':
            update_csv_timestamp(args.csv, word, 'tts_1_timestamp')
            update_csv_timestamp(args.csv, word, 'tts_2_timestamp')
            update_csv_timestamp(args.csv, word, 'tts_3_timestamp')
            tts_count += 1
        else:
            if len(exhausted_combos) >= len(tts_combos):
                logging.warning("All TTS model/key combos exhausted - stopping TTS pass")
            else:
                logging.warning("TTS failed - stopping TTS pass")
            break

    logging.info(f"✓ TTS created: {tts_count}\n")

    # PASS 4: ANKI SYNC
    if not args.skip_anki:
        logging.info("="*60)
        logging.info("PASS 4: SYNCING TO ANKI")
        logging.info("="*60)

        df = pd.read_csv(args.csv, delimiter=';')

        anki_count = 0
        for idx, row in df.iterrows():
            if pd.isna(row.get('profile_timestamp')):
                continue

            word = row.iloc[0]
            normalized = normalize_word(word)
            profile_path = files_dir / f"{normalized}_profile.json"

            if not profile_path.exists():
                continue

            with open(profile_path, 'r') as f:
                word_profile = json.load(f)

            logging.info(f"Anki: {word}")

            if sync_to_anki(word_profile):
                anki_count += 1

        logging.info(f"✓ Anki cards synced: {anki_count}\n")

    # SUMMARY
    logging.info("="*60)
    logging.info("ALL PASSES COMPLETE")
    logging.info("="*60)
    logging.info(f"Profiles: {profile_count}")
    logging.info(f"Images:   {image_count}")
    logging.info(f"TTS:      {tts_count}")
    if not args.skip_anki:
        logging.info(f"Anki:     {anki_count}")
    logging.info("="*60)


if __name__ == '__main__':
    main()
