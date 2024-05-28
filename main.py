#main.py

import os
import tkinter as tk
import pygame
import time as timp
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from pygame import *
from tkinter import Button, PhotoImage
from PIL import Image
from resizeimage import resizeimage
from pydub import AudioSegment
from pydub.playback import *
import librosa
import numpy as np
import soundfile as sf
import threading
import alsaaudio

is_playing = False
after_id = None

def animate_gif():
    global frame_index, is_playing
    if is_playing:
        frame_index += 1
        if frame_index >= gif_frames:
            frame_index = 0
    else:
        frame_index = 0 
    
    label.configure(image=frames[frame_index])
    label.after(100, animate_gif)

global browse
browse = False
def AddMusic():
    path = filedialog.askdirectory()
    StopMusic()
    browse = True
    if path:
        Playlist.delete(0, END)
        os.chdir(path)
        songs = sorted(os.listdir(path))  
        for song in songs:
            if song.endswith(".mp3"):
                Playlist.insert(END, song)
    browse = False

def PlayMusic():
    global is_playing, after_id 

    # if after_id:
    #     root.after_cancel(after_id) 

    Music_Name = Playlist.get(ACTIVE)
    mixer.music.load(Music_Name)
    mixer.music.play()
    is_playing = True
    animate_gif() 

    #sound = pygame.mixer.Sound(Music_Name)
    #length_seconds = sound.get_length() * 1000

    #after_id = root.after(int(length_seconds), NextSong) 

def PauseMusic():
    global is_playing, after_id
    # if after_id:
    #     root.after_cancel(after_id)
    #     after_id = None
    mixer.music.pause()
    is_playing = False

def StopMusic():
    global is_playing, after_id
    if after_id:
        root.after_cancel(after_id)
        after_id = None
    mixer.music.stop()
    is_playing = False

def NextSong(event=None):
    global song_cnt, after_id
    if after_id:
        root.after_cancel(after_id)
        after_id = None
    current_index = Playlist.curselection()
    next_index = current_index[0] + 1
    if next_index == Playlist.size():
        next_index = 0
    Playlist.selection_clear(0, END)
    Playlist.selection_set(next_index)
    Playlist.activate(next_index)
    song_cnt = True
    PlayMusic()


def UnpauseMusic():
    global is_playing
    mixer.music.unpause()
    is_playing = True

# def NextSong(event=None):
#     global song_cnt
#     current_index = Playlist.curselection()
#     next_index = current_index[0] + 1
#     if next_index == Playlist.size():
#         next_index = 0
#     Playlist.selection_clear(0, END)
#     Playlist.selection_set(next_index)
#     Playlist.activate(next_index)
#     song_cnt = True
#     PlayMusic()

def PreviousSong():
    global song_cnt
    current_index = Playlist.curselection()
    previous_index = current_index[0] - 1
    if previous_index < 0:
        previous_index = Playlist.size() - 1
    Playlist.selection_clear(0, END)
    Playlist.selection_set(previous_index)
    Playlist.activate(previous_index)
    song_cnt = True
    PlayMusic()

def RemoveVocals():
    start_time = timp.time()
    myAudioFile = Playlist.get(ACTIVE)
    sound_stereo = AudioSegment.from_file(myAudioFile, format="mp3")
    sound_L = sound_stereo.split_to_mono()[0]
    sound_R = sound_stereo.split_to_mono()[1]
    sound_R_inv = sound_R.invert_phase()
    sound_no_vocals = sound_L.overlay(sound_R_inv, position=0)
    output_filename = myAudioFile.replace(".mp3", "_no_vocals.mp3")
    output_filename = "../vocals-removed/" + output_filename
    fh = sound_no_vocals.export(output_filename, format="mp3")
    ShowMessage("The audio file has been processed")
    print(Playlist.get(ACTIVE))
    print("--- %s seconds ---" % (timp.time() - start_time))

def IsolateVocals():
    start_time = timp.time()
    myAudioFile = Playlist.get(ACTIVE)
    y, sr = librosa.load(myAudioFile)
    S_full, phase = librosa.magphase(librosa.stft(y))
    S_filter = librosa.decompose.nn_filter(S_full, aggregate=np.median, metric='cosine', width=int(librosa.time_to_frames(1, sr=sr)))
    S_filter = np.minimum(S_full, S_filter)
    margin_i, margin_v = 0, 2
    power = 2
    mask_i = librosa.util.softmask(S_filter, margin_i * (S_full - S_filter), power=power)
    mask_v = librosa.util.softmask(S_full - S_filter, margin_v * S_filter, power=power)
    S_foreground = mask_v * S_full
    S_background = mask_i * S_full
    y_foreground = librosa.istft(S_foreground * phase)
    output_filename = myAudioFile.replace(".mp3", "_isolated_vocals.mp3")
    output_filename = "/home/gabriel/Desktop/proiect-am/isolated-vocals/" + output_filename
    sf.write(output_filename, y_foreground, sr)
    ShowMessage("The audio file has been processed")
    print(Playlist.get(ACTIVE))
    print("--- %s seconds ---" % (timp.time() - start_time))

def ShowMessage(message):
    message_label = tk.Label(root, text=message)
    message_label.place(relx=0.5, rely=0.5, anchor="center")
    root.after(5000, message_label.destroy)

def RemoveVocalsInBackground():
    threading.Thread(target=RemoveVocals).start()

def IsolateVocalsInBackground():
    threading.Thread(target=IsolateVocals).start()

def SetVolume(volume):
    volume = float(volume) / 100
    sys_mixer = alsaaudio.Mixer()
    sys_vol = sys_mixer.getvolume()
    sys_vol = float(sys_vol[0]) / 100 
    combined_volume = sys_vol * volume
    pygame.mixer.music.set_volume(combined_volume)


root = Tk()
root.title("Music Player")
root.geometry("589x1000")
root.resizable(False, False)

try:
    background_image = ImageTk.PhotoImage(Image.open('images/cassette-player.png'))
    background_label = tk.Label(root, image=background_image)
    background_label.place(relwidth=1, relheight=1)
except FileNotFoundError:
    print("Background image file not found!")


Frame_Music = Frame(root, bd=2, relief=RIDGE)
Frame_Music.place(x=19, y=298, width=551, height=100)

mixer.init()

SetVolume(50)

Button(root, text="Browse for music", width=52, height=1, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=AddMusic).place(x=19, y=400)

play_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/play.png")
play_image = play_image.subsample(9, 9) 

Button(root, text="Play", image = play_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=PlayMusic).place(x=70, y=890)

pause_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/pause.png")
pause_image = pause_image.subsample(9, 9) 

Button(root, text="Pause", image = pause_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=PauseMusic).place(x=150, y=890)

unpause_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/unpause.png")
unpause_image = unpause_image.subsample(9, 9)

Button(root, text="Unpause", image = unpause_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=UnpauseMusic).place(x=230, y=890)

stop_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/stop.png")
stop_image = stop_image.subsample(9, 9)

Button(root, text="Stop", image = stop_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=StopMusic).place(x=305, y=890)

previous_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/previous.png")
previous_image = previous_image.subsample(9, 9)

Button(root, text="Previous", image = previous_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=PreviousSong).place(x=385, y=890)

next_image = PhotoImage(file = "/home/gabriel/Desktop/proiect-am/images/next.png")
next_image = next_image.subsample(9, 9)

Button(root, text="Next", image = next_image, font=("calibri", 12, "bold"), fg="Black", bg="#FFFFFF", command=NextSong).place(x=465, y=890)

Button(root, text="Remove Vocals", command=RemoveVocalsInBackground).place(x=37, y = 100)

Button(root, text="Isolate Vocals", command=IsolateVocalsInBackground).place(x=424, y = 100)

Scroll = Scrollbar(Frame_Music)

Playlist = Listbox(Frame_Music, width=100, font=("Times new roman", 10), bg="#333333", fg="grey", selectbackground="lightblue", cursor="hand2", bd=0, yscrollcommand=Scroll.set)


Scroll.config(command=Playlist.yview)
Scroll.pack(side=RIGHT, fill=Y)
Playlist.pack(side=RIGHT, fill=BOTH)

volume_slider = Scale(root, from_=0.0, to=100.0, resolution=1.0, orient=HORIZONTAL, command=SetVolume, width=25)
volume_slider.pack()
volume_slider.place(x=66, y=758)


gif_path = "images/Compact-cassette-playing-in-revox-tight_crop.gif"
gif_image = Image.open(gif_path)


new_width = 400 
new_height = 220 
frames = []
frame_index = 0

try:
    while True:
        gif_image.seek(frame_index)
        resized_frame = gif_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        frame = ImageTk.PhotoImage(resized_frame)
        frames.append(frame)
        frame_index += 1
except EOFError:
    pass


if pygame.mixer.get_busy() == False:
    gif_frames = len(frames)

label = tk.Label(root)
label.place(x=90, y=440)

animate_gif()

root.mainloop()