import cv2
import pyaudio
import numpy as np
import tkinter as tk
import time
import json
import os
from tkinter import filedialog, messagebox

config_file = "config.json"

# Default global variables for settings
default_settings = {
    "sound_threshold": 600,
    "sound_duration": 15,
    "frame_pause": 30
}

def load_settings():
    global sound_threshold, sound_duration, frame_pause
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            settings = json.load(file)
            sound_threshold = settings.get("sound_threshold", default_settings["sound_threshold"])
            sound_duration = settings.get("sound_duration", default_settings["sound_duration"])
            frame_pause = settings.get("frame_pause", default_settings["frame_pause"])
    else:
        sound_threshold = default_settings["sound_threshold"]
        sound_duration = default_settings["sound_duration"]
        frame_pause = default_settings["frame_pause"]

def save_settings():
    settings = {
        "sound_threshold": sound_threshold,
        "sound_duration": sound_duration,
        "frame_pause": frame_pause
    }
    with open(config_file, 'w') as file:
        json.dump(settings, file)

# Load settings or use default values
load_settings()

def setup_settings():
    global sound_threshold, sound_duration, frame_pause
    settings_window = tk.Tk()
    settings_window.title("Settings")

    def save_settings_and_close():
        global sound_threshold, sound_duration, frame_pause
        try:
            sound_threshold = int(sound_threshold_entry.get())
            sound_duration = int(sound_duration_entry.get())
            frame_pause = int(frame_pause_entry.get())
            save_settings()
            settings_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter numeric values for settings")

    tk.Label(settings_window, text="Sound Threshold:").pack()
    sound_threshold_entry = tk.Entry(settings_window)
    sound_threshold_entry.insert(0, str(sound_threshold))
    sound_threshold_entry.pack()

    tk.Label(settings_window, text="Sound Duration (0.1 sec):").pack()
    sound_duration_entry = tk.Entry(settings_window)
    sound_duration_entry.insert(0, str(sound_duration))
    sound_duration_entry.pack()

    tk.Label(settings_window, text="Frame Pause (ms):").pack()
    frame_pause_entry = tk.Entry(settings_window)
    frame_pause_entry.insert(0, str(frame_pause))
    frame_pause_entry.pack()

    tk.Button(settings_window, text="Save", command=save_settings_and_close).pack()

    settings_window.mainloop()

# Set up settings first
setup_settings()

root = tk.Tk()
root.withdraw()

gif_path = filedialog.askopenfilename(filetypes=[("GIF Files", "*.gif")])
if not gif_path:
    print("No GIF file selected. Exiting the program.")
    exit()

gif = cv2.VideoCapture(gif_path)
_, first_frame = gif.read()

def display_frame(frame):
    cv2.imshow("Animation", frame)
    cv2.waitKey(frame_pause)

sound_detected = False
reset_animation = False
last_sound_time = time.time()

def detect_sound(in_data, frame_count, time_info, status):
    global sound_detected, reset_animation, last_sound_time
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    if np.max(audio_data) > sound_threshold:
        sound_detected = True
        last_sound_time = time.time()
        reset_animation = False
    elif time.time() - last_sound_time > sound_duration/100:
        sound_detected = False
        if not reset_animation:
            gif.set(cv2.CAP_PROP_POS_FRAMES, 0)
            reset_animation = True
    return None, pyaudio.paContinue

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024,
                stream_callback=detect_sound)
stream.start_stream()

while True:
    if sound_detected:
        _, frame = gif.read()
        if frame is None:
            gif.set(cv2.CAP_PROP_POS_FRAMES, 0)
            _, frame = gif.read()
        display_frame(frame)
    else:
        display_frame(first_frame)

stream.stop_stream()
stream.close()
p.terminate()
cv2.destroyAllWindows()