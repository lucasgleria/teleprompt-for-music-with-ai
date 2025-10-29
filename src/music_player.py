import tkinter as tk
from tkinter import ttk
from pygame import mixer
import src.synchronizer as synchronizer
import threading
import os

class MusicPlayer:
    def __init__(self, master):
        self.master = master
        master.title("Music Player")

        self.songs = self.get_available_songs()
        self.current_song = tk.StringVar(master)
        self.current_song.set(self.songs[0])
        self.current_song.trace("w", self.song_changed)

        self.song_dropdown = ttk.Combobox(master, textvariable=self.current_song, values=self.songs)
        self.song_dropdown.pack()

        self.lyrics_text = tk.Text(master, height=20, width=50)
        self.lyrics_text.pack()

        self.play_button = tk.Button(master, text="Play", command=self.play_music)
        self.play_button.pack()

        self.pause_button = tk.Button(master, text="Pause", command=self.pause_music)
        self.pause_button.pack()

        self.sync_button = tk.Button(master, text="Sync", command=self.sync_lyrics)
        self.sync_button.pack()

        mixer.init()
        self.song_changed()
        self.aligned_lyrics = None
        self.last_highlighted_word_index = -1

    def get_available_songs(self):
        songs = []
        for file in os.listdir("data"):
            if file.endswith(".mp3"):
                songs.append(file.replace(".mp3", ""))
        return songs

    def song_changed(self, *args):
        song_name = self.current_song.get()
        self.lyrics_path = f"data/{song_name}.txt"
        self.music_path = f"data/{song_name}.mp3"
        self.load_lyrics(self.lyrics_path)
        self.load_music(self.music_path)
        self.aligned_lyrics = None
        self.last_highlighted_word_index = -1


    def load_lyrics(self, filename):
        self.lyrics_text.delete("1.0", tk.END)
        with open(filename, "r") as f:
            lyrics = f.read()
        self.lyrics_text.insert(tk.END, lyrics)

    def load_music(self, filename):
        mixer.music.load(filename)

    def play_music(self):
        mixer.music.play()
        if self.aligned_lyrics:
            self.highlight_lyrics()

    def pause_music(self):
        mixer.music.pause()

    def sync_lyrics(self):
        # This can be a long process, so we run it in a separate thread
        def sync():
            vocals_path = synchronizer.separate_vocals(self.music_path)
            vocals_no_silence_path = synchronizer.remove_silence(vocals_path)
            transcription = synchronizer.transcribe_audio(vocals_no_silence_path)
            self.aligned_lyrics = synchronizer.align_lyrics(transcription, self.lyrics_path)
            print("Synchronization complete!")

        threading.Thread(target=sync).start()

    def highlight_lyrics(self):
        current_time = mixer.music.get_pos() / 1000

        self.lyrics_text.tag_remove("highlight", "1.0", tk.END)

        current_word_index = -1
        for i, lyric_data in enumerate(self.aligned_lyrics):
            if lyric_data["start"] <= current_time <= lyric_data["end"]:
                current_word_index = i
                break

        if current_word_index != -1 and current_word_index != self.last_highlighted_word_index:
            lyric_data = self.aligned_lyrics[current_word_index]
            word_to_highlight = lyric_data["text"]

            # Start searching from the position of the last highlighted word
            start_pos = "1.0"
            if self.last_highlighted_word_index != -1 and self.last_highlighted_word_index < current_word_index:
                last_lyric_data = self.aligned_lyrics[self.last_highlighted_word_index]
                last_word_text = last_lyric_data["text"]
                last_pos = self.lyrics_text.search(last_word_text, "1.0", stopindex=tk.END)
                if last_pos:
                    start_pos = f"{last_pos}+{len(last_word_text)}c"

            start_pos = self.lyrics_text.search(word_to_highlight, start_pos, stopindex=tk.END)

            if start_pos:
                end_pos = f"{start_pos}+{len(word_to_highlight)}c"
                self.lyrics_text.tag_add("highlight", start_pos, end_pos)
                self.lyrics_text.tag_config("highlight", background="yellow")
                self.last_highlighted_word_index = current_word_index

        self.master.after(100, self.highlight_lyrics)

if __name__ == "__main__":
    root = tk.Tk()
    player = MusicPlayer(root)
    root.mainloop()
