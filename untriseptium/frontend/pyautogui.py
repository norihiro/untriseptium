import pyautogui
from PIL import ImageGrab


class FrontendPyautogui:
    def __init__(self):
        self._region = None
        self.click = pyautogui.click
        self.move = pyautogui.moveTo

    def screenshot(self):
        try:
            return ImageGrab.grab()
        except:
            return pyautogui.screenshot(region=self._region)
