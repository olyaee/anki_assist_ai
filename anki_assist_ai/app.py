import streamlit as st
from utils.example_generator import (
    get_translation_and_example,
    generate_image_from_profile,
    generate_tts_from_profile,
)
from utils.anki_utils import create_anki_model, add_anki_card
import os
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration to get supported languages and proficiency levels
with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)
supported_languages = config["languages"]["supported_source_languages"]
supported_proficiency_levels = config["languages"]["supported_proficiency_levels"]

st.title("AI Anki Card Generator")
st.write(
    "Enter a German or source language word to generate an Anki card with detailed information."
)

col1, col2 = st.columns([1, 1.5])

if "generate" not in st.session_state:
    st.session_state["generate"] = False

# Input word and source language in the left column
with col1:
    generate_image = st.checkbox("Generate Image")
    generate_audio = st.checkbox("Generate Audio")
    source_language = st.selectbox("Select the source language:", supported_languages)
    proficiency_level = st.selectbox(
        "Select the proficiency level:", supported_proficiency_levels
    )
    word = st.text_input("Enter a German or source language word:")
    if st.button("Generate"):
        st.session_state["generate"] = True
        st.session_state["word"] = word
        st.session_state["source_language"] = source_language
        st.session_state["proficiency_level"] = proficiency_level
        st.session_state["generate_image"] = generate_image
        st.session_state["generate_audio"] = generate_audio
        # Reset the cached data
        st.session_state.pop("word_profile", None)
        st.session_state.pop("image_generated", None)
        st.session_state.pop("audio_generated", None)
        st.session_state.pop("anki_card_added", None)

if st.session_state.get("generate", False):
    word = st.session_state["word"]
    source_language = st.session_state["source_language"]
    proficiency_level = st.session_state["proficiency_level"]
    generate_image = st.session_state["generate_image"]
    generate_audio = st.session_state["generate_audio"]

    # Generate word profile if not already in session_state
    if "word_profile" not in st.session_state:
        with st.spinner("Generating word profile..."):
            word_profile = get_translation_and_example(
                word, source_language, proficiency_level
            )
            st.session_state["word_profile"] = word_profile
    else:
        word_profile = st.session_state["word_profile"]

    # Display translation and grammatical information in the left column
    with col1:
        st.write("### Word Profile")
        st.write(f"**German Word**: {word_profile['german_word']}")
        st.write(
            f"**{source_language} Translation**: {word_profile['source_language_translation']}"
        )
        st.write(f"**Classification**: {word_profile['classification']}")

        if word_profile["classification"] == "(n)":
            noun_info = word_profile.get("additional_grammatical_info", {}).get(
                "noun", {}
            )
            st.write(f"**Article**: {noun_info.get('article', '')}")
            st.write(f"**Plural**: {noun_info.get('plural_form', '')}")
        elif word_profile["classification"] == "(v)":
            verb_info = word_profile.get("additional_grammatical_info", {}).get(
                "verb", {}
            )
            st.write(f"**Infinitive**: {verb_info.get('infinitive', '')}")
            st.write(
                f"**Präsens**: {', '.join(verb_info.get('praesens', []))}"
            )
            st.write(
                f"**Präteritum**: {', '.join(verb_info.get('praeteritum', []))}"
            )
            st.write(f"**Perfekt**: {', '.join(verb_info.get('perfekt', []))}")

        # Display examples
        st.write("### Example Sentences")
        for i, example in enumerate(word_profile["examples"], start=1):
            st.write(f"**Example {i}**:")
            st.write(f"German: {example['german_example']}")
            st.write(
                f"{source_language} Translation: {example['source_example_translation']}"
            )

    # Generate and display image in the right column if selected
    with col2:
        if generate_image:
            if "image_generated" not in st.session_state:
                with st.spinner("Generating image..."):
                    generate_image_from_profile(word_profile)
                    st.session_state["image_generated"] = True
            image_path = os.path.join(
                "files", f"{word_profile['german_word']}_image.jpg"
            )
            if os.path.exists(image_path):
                st.image(image_path, caption="Generated Image")

        # Generate and display audio files if selected
        if generate_audio:
            if "audio_generated" not in st.session_state:
                with st.spinner("Generating audio..."):
                    generate_tts_from_profile(word_profile)
                    st.session_state["audio_generated"] = True
            audio_files = [
                f"{word_profile['german_word']}_word.mp3"
            ] + [
                f"{word_profile['german_word']}_example_{i}.mp3"
                for i in range(1, len(word_profile["examples"]) + 1)
            ]

            for audio_file in audio_files:
                audio_path = os.path.join("files", audio_file)
                if os.path.exists(audio_path):
                    st.audio(audio_path)

    # Automatically add card to Anki
    if "anki_card_added" not in st.session_state:
        with st.spinner("Adding card to Anki..."):
            create_anki_model()
            add_anki_card(word_profile)
            st.session_state["anki_card_added"] = True
