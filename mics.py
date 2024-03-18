import pyaudio

def mic_search():
    p = pyaudio.PyAudio()

    # Печать информации о доступных аудио устройствах
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        print(f"Индекс устройства {i}: {dev_info['name']}")

    p.terminate()