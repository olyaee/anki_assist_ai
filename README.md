# AI Anki Card Generator

Generate Anki flashcards from any source language to German using AnkiConnect and OpenAI. This tool creates custom cards with translations, grammar information, examples, images, and audio. It is easily adaptable to other languages as well.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
   - [Running the Streamlit App](#running-the-streamlit-app)
   - [Using the Command Line](#using-the-command-line)
5. [Project Structure](#project-structure)
6. [Dependencies](#dependencies)
7. [Costs](#costs)
8. [License](#license)

## Features

- **Automatic Translation and Grammatical Analysis**: Translates words between German and various source languages, adding detailed grammatical information.
- **Audio and Image Generation**: Utilizes OpenAI's TTS and image models to generate audio pronunciation files and relevant images.
- **Example Sentences**: Creates three example sentences at the chosen proficiency level (A1 to C2) in both German and the source language for effective vocabulary learning.
- **Multiple Source Languages**: Supports any source language supported by OpenAI, including English, Farsi, Spanish, French, German, Italian, Japanese, Korean, Portuguese, Russian, Chinese, Turkish, Arabic, and Hindi.
- **Customizable Proficiency Levels**: Allows selection of proficiency levels from A1 to C2 to tailor the complexity of generated examples.
- **Custom Anki Model**: Automatically sets up and uses a custom Anki model to format and display generated content.
- **User-Friendly Streamlit Interface**: Provides an interactive web-based interface for easy input and visualization.
- **Command-Line Interface**: Offers a CLI for users who prefer terminal-based interaction.
- **Duplicate Card Handling**: Automatically detects and overwrites duplicate Anki cards.
- **Integrated File Management**: Automatically organizes and saves generated media files (images, audio, profiles).

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/your-username/ai_anki_card_generator.git
   cd ai_anki_card_generator
   ```

2. **Install Poetry** (if you haven’t already):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. **Set the Correct Python Version**: 

   ```bash
   python get_python_version.py | xargs poetry env use
   ```
4. **Install Dependencies**:

   ```bash
   poetry install
   ```

5. **Set Up Environment Variables**:

   - Create a `.env` file in the project root directory.
   - Add your OpenAI API key in the following format:
     ```plaintext
     OPENAI_API_KEY=your_openai_api_key
     ```

5. **Configure AnkiConnect**:

   - Install [AnkiConnect](https://foosoft.net/projects/anki-connect/) by following the instructions provided on the website. Here is a summary:

     1. Open the Install Add-on dialog by selecting **Tools | Add-ons | Get Add-ons**... in Anki.
     2. Input `2055492159` into the text box labeled **Code** and press the **OK** button to proceed.
     3. Restart Anki when prompted to complete the installation of Anki-Connect.

   - Anki must be kept running in the background for other applications to use Anki-Connect. You can verify that Anki-Connect is running at any time by accessing `localhost:8765` in your browser. If the server is running, you will see the message "Anki-Connect" displayed in your browser window.

## Configuration

The configuration file `config.yml` controls the generation and processing parameters for the project. Key sections include:

- **Languages**: Defines supported source languages and proficiency levels.
- **Prompt**: Contains the system message template guiding OpenAI's language model for translations and example generation.
- **Schema**: Specifies the JSON schema for the structured data returned by OpenAI.
- **Files**: Directory to store generated files like images and audio.
- **Anki**: Settings for the Anki deck, model, and card templates.
- **OpenAI Models**: Configuration for OpenAI text, image, and TTS (text-to-speech) models.

Modify the `config.yml` file as needed to fine-tune the project’s output.

## Usage

### Running the Streamlit App

To start the Streamlit app, use the following command:

```bash
poetry run streamlit run ai_anki_card_generator/app.py
```

The app provides a user-friendly interface with a two-column layout:

- **Left Column**:

  - **Generate Image**: Checkbox to generate an image.
  - **Generate Audio**: Checkbox to generate audio files.
  - **Select Source Language**: Choose from supported languages.
  - **Select Proficiency Level**: Choose from A1 to C2.
  - **Input Word**: Enter a German or source language word.
  - **Generate Button**: Starts the generation process.

- **Right Column**:

  - Displays generated images and audio files (if requested).

Once generated, the Anki card is automatically added to your specified deck.

### Using the Command Line

To run the program via the command line, use:

```bash
poetry run python ai_anki_card_generator/main.py
```

- You will be prompted to enter a word, source language, and proficiency level.
- The program will generate the corresponding Anki card, handling duplicate entries by overwriting existing cards with the same German word.

## Project Structure

```plaintext
.
├── ai_anki_card_generator           # Main project directory
│   ├── __init__.py
│   ├── app.py                       # Streamlit app
│   └── main.py                      # Command-line entry point
├── utils                            # Utility functions
│   ├── anki_utils.py                # AnkiConnect functions
│   ├── example_generator.py         # Word profile generation, images, and audio
├── config.yml                       # Configuration file
├── .env                             # Environment variables (API key)
├── README.md                        # Project documentation
├── pyproject.toml                   # Poetry dependencies
├── .gitignore                       # Ignored files
```

## Dependencies

- **Python** 3.10 or later
- **Poetry** for package management
- **OpenAI API** for language, image, and audio generation
- **Pillow** for image processing
- **requests** for HTTP requests (AnkiConnect)
- **PyYAML** for YAML configuration handling
- **python-dotenv** to load environment variables
- **Streamlit** for the web-based interface

## Costs

TODO

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

