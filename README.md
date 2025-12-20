# Anki Assist AI

Automated Anki flashcard generator for German learning using Google Gemini. Generates translations, grammar info, example sentences with lecture-specific grammar, images, and audio.

## Features

- **Batch Processing** with auto-resume (skips completed words)
- **Grammar-Aware**: Uses lecture-specific grammar rules for examples
- **AI Generation**: Gemini 2.5 Flash (text), Nano Banana (images), Gemini TTS (audio)
- **Multi-Language**: 14+ source languages
- **Cost**: ~$0.08/word (~$83 for 1,042 words, ~13 hours with free tier)

## Quick Start

```bash
# 1. Install
git clone https://github.com/your-username/anki_assist_ai.git
cd anki_assist_ai
curl -sSL https://install.python-poetry.org | python3 -
poetry install

# 2. Setup
cp .env.template .env
# Add GOOGLE_AI_API_KEY to .env

# 3. Install AnkiConnect
# Anki → Tools → Add-ons → Get Add-ons → Code: 2055492159

# 4. Create Anki deck (e.g., "Netzwerk neu B1.1")

# 5. Create folder for your level
mkdir -p b1.1

# 6. Create grammar file: b1.1/grammer.md
cat > b1.1/grammer.md << 'EOF'
### Lektion 1
- Weil-Sätze (because clauses)
- Perfekt tense
- Modal verbs
EOF

# 7. Create word list: b1.1/word_list.csv
cat > b1.1/word_list.csv << 'EOF'
word;lecture;exercise
faulenzen;1;1a
lernen;1;1b
EOF

# 8. Configure main.py
# Update: proficiency_level, grammar_file, csv_file, deck_name

# 9. Test with 1 word first
# Edit main.py: df = df.head(1)
poetry run python anki_assist_ai/main.py

# 10. Run full batch (prevents sleep)
caffeinate -s poetry run python anki_assist_ai/main.py

# Check progress anytime
poetry run python utils/check_progress.py
```

## Configuration

**config.yml:**
```yaml
gemini:
  text_model: "gemini-2.5-flash"
  image_model: "gemini-2.5-flash-image"  # Nano Banana
  tts_model: "gemini-2.5-flash-preview-tts"

anki:
  deck_name: "Netzwerk neu B1.1"  # Must match your Anki deck
  connect_url: "http://localhost:8765"
```

**main.py:**
```python
source_language = "English"
proficiency_level = "B1.1"
grammar_file = "b1.1/grammer.md"
csv_file = "b1.1/word_list.csv"
generate_image = True
generate_tts = True
add_to_anki = True
```

## How It Works

1. **Input**: CSV with word, lecture, exercise
2. **Grammar**: Extracts lecture-specific grammar from markdown
3. **AI Generation**:
   - Text: Translation + 3 examples using lecture grammar
   - Image: Visual mnemonic (1024x1024 → 256x256)
   - Audio: Word + 3 example WAV files (7-sec delays for rate limiting)
4. **Output**: JSON profiles + media files → Anki cards

**Example:** For word "faulenzen" in Lecture 1:
- Grammar: `Weil-Sätze, Perfekt tense`
- Generated: "Ich habe keine Lust zu faulenzen, **weil** ich etwas erleben möchte."
- Result: Vocabulary reinforces grammar! ✨

## Generated Files

```
files/
├── faulenzen_profile.json       # Word data
├── faulenzen_image.jpg          # Visual mnemonic
├── faulenzen_word.wav           # Word audio
├── faulenzen_example_1.wav      # Example 1 audio
├── faulenzen_example_2.wav      # Example 2 audio
└── faulenzen_example_3.wav      # Example 3 audio
```

## Progress Tracking

```bash
# Check status
poetry run python utils/check_progress.py

# Output shows complete/incomplete words
# Script auto-skips completed words on resume
```

## Rate Limits & Costs (Free Tier)

| Model | Limit | Cost/Word | Bottleneck |
|-------|-------|-----------|------------|
| Text (2.5 Flash) | 15 RPM | $0.0007 | No |
| Image (Nano Banana) | - | $0.039 | No |
| TTS (2.5 Flash) | **10 RPM** | $0.04 | **Yes** |

**Total**: ~$0.08/word, ~45 sec/word (due to TTS rate limiting)

**For 1,042 words**: ~$83, ~13 hours

**Upgrade**: Enable Cloud Billing for faster processing (same cost, higher limits)

## Project Structure

```
.
├── anki_assist_ai/
│   ├── main.py              # Main script
│   └── postprocess.py       # Quality checks
├── utils/
│   ├── anki_utils.py        # AnkiConnect API
│   ├── example_generator.py # Gemini generation
│   ├── cost_calculator.py   # Cost tracking
│   └── check_progress.py    # Progress checker
├── config.yml               # Configuration
├── .env                     # API key
└── files/                   # Generated outputs
```

## Tips

**Prevent laptop sleep:**
```bash
caffeinate -s poetry run python anki_assist_ai/main.py
```

**Run in background:**
```bash
nohup poetry run python anki_assist_ai/main.py > output.log 2>&1 &
tail -f output.log
```

**Resume after crash:**
Just run again - auto-skips completed words!

**Quality checks:**
```bash
poetry run python anki_assist_ai/postprocess.py
```

## Dependencies

- Python 3.10+
- Poetry
- Google AI API key
- Anki + AnkiConnect

## License

MIT License
