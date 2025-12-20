# Anki Word Processor

Clean, focused implementation for processing German vocabulary words and syncing to Anki.

## What It Does

1. Reads a CSV file with German words
2. For each word, generates:
   - **Profile JSON**: Word details, translations, grammar, examples
   - **Image**: Visual mnemonic (256x256 JPG)
   - **TTS Audio**: 3 example sentences (WAV with silence padding)
3. Updates Anki deck with card for each word
4. Tracks progress in CSV timestamps

## Key Features

- **Error Resilient**: If one type fails (e.g., TTS quota limit), continues with others
- **Skip Completed**: Only processes words with missing content
- **Resume Anytime**: Run multiple times, picks up where it left off

## Setup

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env and add your GOOGLE_AI_API_KEY
```

### 3. Prepare CSV

Your CSV should have this structure:

```
word;lecture;exercise;profile_timestamp;image_timestamp;tts_1_timestamp;tts_2_timestamp;tts_3_timestamp
faulenzen;1;1a;;;;;
giftig;1;1a;;;;;
himmel, der, -;1;1a;;;;;
```

**Tracking columns** (automatically updated):
- `profile_timestamp`: When profile JSON was created
- `image_timestamp`: When image was generated
- `tts_1_timestamp`, `tts_2_timestamp`, `tts_3_timestamp`: When each TTS file was created

Empty = not created yet.

### 4. Start Anki

Make sure Anki is running with the AnkiConnect addon installed.

## Usage

```bash
poetry run python process_words.py \
  --csv path/to/words.csv \
  --grammar grammer.md \
  --language English \
  --level B1.1
```

**Optional flags:**
- `--skip-profile`: Don't generate profiles
- `--skip-image`: Don't generate images
- `--skip-tts`: Don't generate TTS
- `--skip-anki`: Don't sync to Anki
- `--limit N`: Process only first N incomplete words

**Examples:**

```bash
# Process everything
poetry run python process_words.py --csv words.csv --grammar grammer.md

# Just generate missing images
poetry run python process_words.py --csv words.csv --skip-profile --skip-tts --skip-anki

# Test with 5 words
poetry run python process_words.py --csv words.csv --grammar grammer.md --limit 5
```

## Files Generated

For each word (e.g., "Himmel"):

```
files/
├── Himmel_profile.json    # Word profile (translations, grammar, examples)
├── Himmel_image.jpg       # Visual mnemonic (256x256)
├── Himmel_example_1.wav   # TTS for example 1 (with silence padding)
├── Himmel_example_2.wav   # TTS for example 2
└── Himmel_example_3.wav   # TTS for example 3
```

## Configuration

Edit `config.yml` to customize:
- **Prompts**: System message, image prompt
- **Models**: Gemini text/image/TTS models
- **Anki**: Deck name, card template
- **TTS Voices**: Available voice options

## Error Handling

The processor is resilient:
- **Quota limits**: Skips that type, continues with others
- **API errors**: Logs error, moves to next word
- **Anki down**: Generates files, skips Anki sync
- **Interrupted**: Resume anytime, continues from incomplete words

Check logs for details on what succeeded/failed.

## Dependencies

- **google-genai**: Gemini API (text, image, TTS generation)
- **pandas**: CSV reading and manipulation
- **pillow**: Image resizing
- **requests**: AnkiConnect API
- **pyyaml**: Config file parsing
- **python-dotenv**: Environment variable loading
- **sox**: Audio silence padding (system dependency)

## Troubleshooting

**No words processed**: Check CSV has empty timestamp columns for incomplete words

**Quota exceeded**: Gemini API has daily limits. Wait 24h or use `--skip-tts` to generate other content

**Anki errors**: Make sure Anki is running and AnkiConnect addon is installed

**Audio silence fails**: Install sox: `brew install sox` (macOS)
