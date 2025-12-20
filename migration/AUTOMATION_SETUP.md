# Automated Word Processing Setup

This sets up automatic processing 4 times per day:
- 10:00 AM
- 2:00 PM
- 5:00 PM
- 7:00 PM

## Installation

Run these commands once:

```bash
# Copy the plist to LaunchAgents
cp com.anki.processor.plist ~/Library/LaunchAgents/

# Load the automation (starts scheduling)
launchctl load ~/Library/LaunchAgents/com.anki.processor.plist
```

## What It Does

**Every scheduled run:**
1. Opens Anki if not running
2. Runs all 4 passes (profiles, images, TTS, Anki sync)
3. Stops when quota hits for each component type
4. Logs everything to `~/anki_processor.log`

**Survives restarts:**
- macOS automatically loads launchd agents on login
- Will run at scheduled times even after reboot

## Monitoring

**Check logs:**
```bash
# Main log (detailed processing)
tail -f ~/anki_processor.log

# System logs (errors)
tail -f ~/anki_processor_stderr.log
```

**Check status:**
```bash
# See if it's loaded
launchctl list | grep anki

# See next scheduled run
launchctl print gui/$(id -u)/com.anki.processor
```

## Management

**Stop automation:**
```bash
launchctl unload ~/Library/LaunchAgents/com.anki.processor.plist
```

**Start automation:**
```bash
launchctl load ~/Library/LaunchAgents/com.anki.processor.plist
```

**Run manually (test):**
```bash
./run_daily.sh
```

**Remove completely:**
```bash
launchctl unload ~/Library/LaunchAgents/com.anki.processor.plist
rm ~/Library/LaunchAgents/com.anki.processor.plist
```

## How It Works

**Pass-based processing:**
- Each run does 4 passes: Profiles → Images → TTS → Anki
- Each pass continues until quota hits
- Next run picks up where it left off

**Example progression:**

**Run 1 (10 AM):**
- Profiles: 500 created (quota hit)
- Images: 300 created (quota hit)
- TTS: 50 created (quota hit)
- Anki: 500 synced

**Run 2 (2 PM):**
- Profiles: 200 created (quota hit)
- Images: 150 created (quota hit)
- TTS: 30 created (quota hit)
- Anki: 200 synced

**Continue until all 1042 words are complete!**

## Troubleshooting

**Not running?**
- Check if loaded: `launchctl list | grep anki`
- Check error log: `cat ~/anki_processor_stderr.log`

**Anki not opening?**
- Make sure Anki app is installed in Applications
- Test: `open -a Anki`

**Quota exhausted immediately?**
- Daily quotas reset 24 hours after first use
- Wait for reset, automation will continue next day

## Files

- `run_daily.sh` - Main runner script
- `com.anki.processor.plist` - launchd schedule configuration
- `~/anki_processor.log` - Processing logs
- `~/anki_processor_stdout.log` - Standard output
- `~/anki_processor_stderr.log` - Error logs
