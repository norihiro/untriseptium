import pyautogui


class FrontendPyautogui:
    def __init__(self):
        self._region = None
        self.click = pyautogui.click
        self.move = pyautogui.moveTo

    def screenshot(self):
        return pyautogui.screenshot(region=self._region)
