"""Utilities for creating and managing audio files."""
import os
import subprocess
from pathlib import Path


def create_silent_audio(filename: str, duration_ms: int) -> None:
    """Creates a silent audio file using sox.

    Args:
        filename: The name of the file to save the silent audio.
        duration_ms: The duration of the silent audio in milliseconds.
    """
    duration_s = duration_ms / 1000
    subprocess.run(
        [
            "sox",
            "-n",  # Generate audio
            "-r", "44100",  # Sample rate
            filename,
            "trim", "0.0", str(duration_s),
        ],
        check=True,
        capture_output=True,
    )


def find_audio_files(directory: str) -> list[str]:
    """Finds all MP3 files in the specified directory.

    Args:
        directory: The directory to search for the files.

    Returns:
        A list of file paths that end with .mp3.
    """
    audio_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            file_path = os.path.join(directory, filename)
            audio_files.append(file_path)
            print(f"Found audio file: {filename}")
    return audio_files


def add_silence_to_audio(input_file: str, duration_ms: int = 2000) -> None:
    """Adds silence to the beginning of an audio file using sox.

    Args:
        input_file: Path to the input audio file.
        duration_ms: Duration of silence to add in milliseconds.
    """
    # Create temporary files
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    
    output_file = temp_dir / "output.mp3"
    
    try:
        # Add silence to the beginning using sox pad effect
        subprocess.run(
            [
                "sox",
                input_file,
                str(output_file),
                "pad", f"{duration_ms/1000}", "0",
            ],
            check=True,
            capture_output=True,
        )
        
        # Replace original file with the new one
        os.replace(output_file, input_file)
        
    finally:
        # Clean up temporary files
        if output_file.exists():
            output_file.unlink()
        
        # Try to remove temp directory if empty
        try:
            temp_dir.rmdir()
        except OSError:
            pass  # Directory not empty or already deleted


def add_silence_to_all_audio(directory: str) -> None:
    """Adds silence to the beginning of all MP3 files in the specified directory.

    Args:
        directory: The directory containing the MP3 files to process.
    """
    audio_files = find_audio_files(directory)
    for file_path in audio_files:
        try:
            print(f"Adding silence to: {os.path.basename(file_path)}")
            add_silence_to_audio(file_path)
        except subprocess.CalledProcessError as e:
            print(f"Error processing {file_path}: {e.stderr.decode()}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")


if __name__ == "__main__":
    add_silence_to_all_audio("./files")

