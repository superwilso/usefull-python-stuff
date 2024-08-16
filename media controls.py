import keyboard
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER, windll
import pystray
from PIL import Image, ImageDraw
import sys

# Define media key codes
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1

class AudioController:
    def __init__(self):
        self.update_volume()
        self.control_action_triggered = False  # Initialize the flag

    def update_volume(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def change_volume(self, delta):
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, min(1.0, current_volume + delta))
        self.volume.SetMasterVolumeLevelScalar(new_volume, None)

    def media_control(self, action):
        if not self.control_action_triggered:  # Check if the action has already been triggered
            if action == "play_pause":
                windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_EXTENDEDKEY, 0)
                windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            elif action == "next":
                windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_EXTENDEDKEY, 0)
                windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            elif action == "previous":
                windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_EXTENDEDKEY, 0)
                windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            self.reset_control_action()  # Ensure the flag is reset after the action

    def reset_control_action(self):
        self.control_action_triggered = False  # Reset the flag

def create_image():
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))
    d = ImageDraw.Draw(image)
    d.text((10, 10), "Audio", fill=(255, 255, 0))
    return image

def setup_hotkeys(controller):
    keyboard.add_hotkey('ctrl+shift+up', lambda: print("Volume increased") or controller.change_volume(0.05))
    keyboard.add_hotkey('ctrl+shift+down', lambda: print("Volume decreased") or controller.change_volume(-0.05))
    keyboard.add_hotkey('ctrl+shift+right', lambda: print("Next track") or controller.media_control("next"), suppress=True)  # Suppress default action
    keyboard.add_hotkey('ctrl+shift+left', lambda: print("Previous track") or controller.media_control("previous"), suppress=True)  # Suppress default action
    keyboard.add_hotkey('ctrl+shift+space', lambda: print("Play/Pause") or controller.media_control("play_pause"), suppress=True)  # Suppress default action

def quit_app(icon):
    icon.stop()
    keyboard.unhook_all()
    sys.exit(0)

def run_app():
    controller = AudioController()
    setup_hotkeys(controller)

    menu = pystray.Menu(
        pystray.MenuItem("Quit", quit_app)
    )

    icon = pystray.Icon("audio_controller", create_image(), "Audio Controller", menu)
    icon.run()

if __name__ == "__main__":
    run_app()
