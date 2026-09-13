import pygame
import os

def init_music(file_name="background_music.mp3", volume=0.2):
    """Ініціалізує мікшер та запускає фонову музику по колу."""
    if os.path.exists(file_name):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_name)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)  # -1 означає нескінченний повтор
            print(f"Музику '{file_name}' успішно запущено!")
        except Exception as e:
            print(f"Не вдалося запустити музику: {e}")
    else:
        print(f"Увага: Файл '{file_name}' не знайдено в папці з грою. Гра працює без звуку.")