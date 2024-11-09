import lyricsgenius
import re
import os
import subprocess
import json
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

# Initialize the Genius API client
genius = lyricsgenius.Genius("I1Skzzd5zK9eEuzOojzk-t_z_cFb9FhkAykiHQKFTRhpwpj-gcOYRgX23Dz2pWOT7jF9H9Nd-p3gKAnMEMUSOg")

# Set artist and song details
artist_name = "Rick Astley"  # Correct artist's name
song_title = "Never Gonna Give You Up"

# Define file paths
mp3_file = f"{song_title}.mp3"
wav_file = f"{song_title}.wav"
lyrics_file = "lyricpre.txt"
output_file = "lyricpre.json"
lang = "eng"

# Search for the song
song = genius.search_song(song_title, artist_name)

# Function to clean up lyrics
def clean_lyrics(lyrics):
    lyrics = re.sub(r'\[.*?\]', '', lyrics)  # Remove bracketed text
    lyrics = re.sub(r'\s*\(.*?\)', '', lyrics)  # Remove parentheses text
    lyrics = re.sub(r'\n+', '\n', lyrics).strip()  # Remove extra newlines
    lyrics = re.sub(r'You might also like.*', '', lyrics)  # Remove unwanted fragments
    return lyrics

# Check if song was found and save cleaned lyrics
if song:
    cleaned_lyrics = clean_lyrics(song.lyrics)
    with open(lyrics_file, 'w', encoding='utf-8') as file:
        file.write(cleaned_lyrics)
    print(f"Lyrics saved to {lyrics_file}")
else:
    print("Song not found.")
    exit()

# Convert MP3 to WAV
def convert_mp3_to_wav(mp3_file, wav_file):
    try:
        subprocess.run(['ffmpeg', '-y', '-i', mp3_file, '-ar', '44100', '-ac', '2', wav_file], check=True)
        print(f"Converted '{mp3_file}' to '{wav_file}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return False
    return True

# Generate timestamped lyrics
def generate_timestamped_lyrics(mp3_file, lyrics_file, output_file):
    with open(lyrics_file, 'r', encoding='utf-8') as f:
        if not (content := f.read().strip()):
            print("Error: Lyrics file is empty or unreadable.")
            return

    task = Task(f"task_language={lang}|is_text_type=plain|os_task_file_format=json|aligner=forced|phonetic_distance=0.2")
    task.audio_file_path_absolute = mp3_file
    task.text_file_path_absolute = lyrics_file
    task.sync_map_file_path_absolute = output_file

    try:
        ExecuteTask(task).execute()
        task.output_sync_map_file()
        print(f"Timestamped lyrics saved to {output_file}")
    except Exception as e:
        print("Error during synchronization:", e)

# Adjust timestamps
def adjust_timestamps(data, offset=0.2):
    for fragment in data['fragments']:
        fragment['begin'] = float(fragment['begin']) + offset
        fragment['end'] = float(fragment['end']) + offset
    return data

# Format lyrics with timestamps
def format_lyrics_with_timestamps(data, song_title):
    output = [f"Song: {song_title}"]
    for fragment in data['fragments']:
        minutes, seconds = divmod(int(float(fragment['begin'])), 60)
        formatted_time = f"{minutes}:{seconds:02d}"
        for line in fragment['lines']:
            line = re.sub(r'\s*\(.*?\)', '', line).strip()
            if line:
                output.append(f"{formatted_time}\n{line}")
    return "\n".join(output)

# Main execution
if convert_mp3_to_wav(mp3_file, wav_file):
    generate_timestamped_lyrics(wav_file, lyrics_file, output_file)

    # Load and adjust timestamps
    with open(output_file, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    adjusted_data = adjust_timestamps(data, offset=0.2)

    # Write formatted lyrics to file
    formatted_lyrics = format_lyrics_with_timestamps(adjusted_data, song.title)
    with open("lyric.txt", 'w', encoding='utf-8') as text_file:
        text_file.write(formatted_lyrics)
    print("Lyrics have been successfully written to lyric.txt")
else:
    print("Failed to convert MP3 to WAV.")
