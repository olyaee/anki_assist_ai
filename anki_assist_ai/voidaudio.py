import wave

def create_silent_audio(filename, duration_ms):
    """Creates a silent audio file.

    Args:
        filename (str): The name of the file to save the silent audio.
        duration_ms (int): The duration of the silent audio in milliseconds.
    """
    # Number of frames
    n_frames = int((44100 * duration_ms) / 1000)
    
    # Create a wave file
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 2 bytes per sample
        wf.setframerate(44100)  # 44.1 kHz sample rate
        wf.writeframes(b'\x00\x00' * n_frames)

# Create a 2-second silent audio file
create_silent_audio('silent_audio.wav', 2000)



import os

def find_word_audio_files(directory):
    """Finds all files in the specified directory that end with 'word.mp3'.

    Args:
        directory (str): The directory to search for the files.

    Returns:
        list: A list of file paths that end with 'word.mp3'.
    """
    word_audio_files = []
    for filename in os.listdir(directory):
        if filename.endswith('word.mp3'):
            word_audio_files.append(os.path.join(directory, filename))
            print(filename)
    return word_audio_files

# Example usage
# word_audio_files = find_word_audio_files('/path/to/files')
# print(word_audio_files)

find_word_audio_files("./files")

def replace_with_silent_audio(directory):
    """Replaces all 'word.mp3' files in the specified directory with a 2-second silent audio file.

    Args:
        directory (str): The directory containing the 'word.mp3' files to be replaced.
    """
    word_audio_files = find_word_audio_files(directory)
    for file_path in word_audio_files:
        create_silent_audio(file_path, 2000)

# Example usage
replace_with_silent_audio("./files")


