'''
The module untriseptium provides a framework to automate GUI interaction using
screenshot, OCR, and mouse/keyboard control.
'''

from . import util

# pylint: disable=import-outside-toplevel


def _default_frontend():
    from .frontend import pyautogui
    return pyautogui.FrontendPyautogui()


def _default_backend():
    from .backend import tesseract
    return tesseract.BackendTesseract()


def _filter_locator(locator):
    try:
        locator = locator.center()
    except AttributeError:
        pass
    return locator


class Untriseptium:
    def __init__(self, frontend=None, ocrengine=None):
        # engine instances
        self.frontend = frontend if frontend else _default_frontend()
        self.ocrengine = ocrengine if ocrengine else _default_backend()

        self._clear_screenshot()

    def _clear_screenshot(self):
        self.screenshot = None
        self.ocrdata = None

    def capture(self):
        self.screenshot = self.frontend.screenshot()
        self.ocrdata = None

    def ocr(self):
        if not self.screenshot:
            self.capture()
        self.ocrdata = self.ocrengine.ocr(self.screenshot)

    def find_text(self, text, location_hint=None):
        if not self.ocrdata:
            self.ocr()

        texts = self.ocrengine.find_texts(self.ocrdata, text)

        if location_hint:
            xyh = (
                    location_hint[0] * self.screenshot.width,
                    location_hint[1] * self.screenshot.height
                    )
            cand = None
            for t in texts:
                xyt = t.location.center()
                x, y = (xyh[0] - xyt[0], xyh[1] - xyt[1])
                dist = x * x + y * y
                if not cand or dist < cand_dist:
                    cand = t
                    cand_dist = dist
            cand.set_context(self)
            return cand

        texts[0].set_context(self)
        return texts[0]

    def click(self, locator):
        locator = _filter_locator(locator)
        self._clear_screenshot()
        return self.frontend.click(locator[0], locator[1])

    def move(self, locator):
        locator = _filter_locator(locator)
        return self.frontend.move(locator[0], locator[1])
