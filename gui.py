import cv2
import pyaudio
import numpy as np
import tkinter as tk
import time
import json
import os
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading

# Установка имени файла конфигурации
config_file = "config.json"

# Глобальные переменные для настроек по умолчанию
default_settings = {
    "sound_threshold": 600,
    "sound_duration": 15,
    "frame_pause": 30,
    "selected_device_index": 0
}

# Загрузка настроек из файла конфигурации или использование значений по умолчанию
def load_settings():
    global sound_threshold, sound_duration, frame_pause, selected_device_index, new_selected_device_index
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            settings = json.load(file)
            sound_threshold = settings.get("sound_threshold", default_settings["sound_threshold"])
            sound_duration = settings.get("sound_duration", default_settings["sound_duration"])
            frame_pause = settings.get("frame_pause", default_settings["frame_pause"])
            selected_device_index = settings.get("selected_device_index", default_settings["selected_device_index"])
            new_selected_device_index = selected_device_index
    else:
        sound_threshold = default_settings["sound_threshold"]
        sound_duration = default_settings["sound_duration"]
        frame_pause = default_settings["frame_pause"]
        selected_device_index = default_settings["selected_device_index"]
        new_selected_device_index = selected_device_index

# Сохранение текущих настроек в файле конфигурации
def save_settings():
    global sound_threshold, sound_duration, frame_pause, selected_device_index, new_selected_device_index
    settings = {
        "sound_threshold": sound_threshold,
        "sound_duration": sound_duration,
        "frame_pause": frame_pause,
        "selected_device_index": new_selected_device_index
    }
    with open(config_file, 'w') as file:
        json.dump(settings, file)
    selected_device_index = new_selected_device_index  # Обновление selected_device_index

def select_audio_device_menu():
    p = pyaudio.PyAudio()
    audio_devices = []
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        audio_devices.append((i, dev_info['name']))
    p.terminate()
    return audio_devices

def setup_settings(selected_device_index):
    global sound_threshold, sound_duration, frame_pause
    settings_window = tk.Tk()
    settings_window.title("Settings")
    settings_window.geometry("250x200")  # Задаем размер окна (ширина x высота)
    settings_window.resizable(False, False)  # Запрещаем изменение размеров окна пользователем

    def save_settings_and_close():
        global sound_threshold, sound_duration, frame_pause, selected_device_index, new_selected_device_index, stream, p
        try:
            sound_threshold = int(sound_threshold_entry.get())
            sound_duration = int(sound_duration_entry.get())
            frame_pause = int(frame_pause_entry.get())
            new_selected_device_index = audio_device_combobox.current()

            save_settings()

            stream.stop_stream()
            stream.close()
            p.terminate()

            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=44100,
                            input=True,
                            frames_per_buffer=1024,
                            stream_callback=detect_sound,
                            input_device_index=new_selected_device_index)
            stream.start_stream()

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

    audio_devices = select_audio_device_menu()
    audio_device_names = [f"{device[1]}" for device in audio_devices]

    tk.Label(settings_window, text="Select Audio Device:").pack()
    audio_device_combobox = ttk.Combobox(settings_window, values=audio_device_names)
    selected_device_name = [device[1] for device in audio_devices if device[0] == selected_device_index][0]
    audio_device_combobox.set(selected_device_name)
    audio_device_combobox.pack()

    tk.Button(settings_window, text="Save", command=save_settings_and_close).pack()

    settings_window.mainloop()

# Функция для отображения кадра
def display_frame(frame):
    cv2.imshow("Animation", frame)
    cv2.waitKey(frame_pause)

# Загрузка настроек и установка параметров
load_settings()
# Создание корневого окна Tkinter для диалога выбора GIF файла
root = tk.Tk()
root.withdraw()

def menu_thread(selected_device_index):
    setup_settings(selected_device_index)

# Передача значения переменной selected_device_index в функцию menu_thread
menu_t = threading.Thread(target=menu_thread, args=(selected_device_index,))
menu_t.start()
# Запрос выбора GIF файла у пользователя
gif_path = filedialog.askopenfilename(filetypes=[("GIF Files", "*.gif")])
if not gif_path:
    print("No GIF file selected. Exiting the program.")
    exit()

# Открытие GIF файла с помощью OpenCV и чтение первого кадра
gif = cv2.VideoCapture(gif_path)
_, first_frame = gif.read()

# Функция для обнаружения звука во входных данных аудио
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

# Инициализация переменных для обнаружения звука
sound_detected = False
reset_animation = False
last_sound_time = time.time()

# Настройка записи аудио с использованием PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024,
                stream_callback=detect_sound,
                input_device_index=new_selected_device_index)  # Используйте new_selected_device_index здесь
stream.start_stream()

# Основной цикл отображения анимации
while True:
    if sound_detected:
        _, frame = gif.read()
        if frame is None:
            gif.set(cv2.CAP_PROP_POS_FRAMES, 0)
            _, frame = gif.read()
        display_frame(frame)
    else:
        display_frame(first_frame)

# Остановка записи аудио и закрытие всех окон
stream.stop_stream()
stream.close()
p.terminate()
cv2.destroyAllWindows()