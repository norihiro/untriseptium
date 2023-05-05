'''
The module untriseptium provides a framework to automate GUI interaction using
screenshot, OCR, and mouse/keyboard control.
'''

from . import util
import math

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

    def find_texts(self, text, location_hint=None, color_hint=None, create_image=False):
        if not self.ocrdata:
            self.ocr()

        texts = self.ocrengine.find_texts(self.ocrdata, text)

        if location_hint:
            xyh = (
                    location_hint[0] * self.screenshot.width,
                    location_hint[1] * self.screenshot.height
                    )
            if len(location_hint) > 2:
                ambiguity = location_hint[2] * math.hypot(self.screenshot.width, self.screenshot.height)
            else:
                ambiguity = hypot(self.screenshot.width, self.screenshot.height)
            for t in texts:
                xyt = t.location.center()
                dist = math.hypot(xyh[0] - xyt[0], xyh[1] - xyt[1])
                t.location_confidence = math.cos(dist * math.pi / ambiguity) * 0.5 + 0.5 if dist < ambiguity else 0

        for t in texts:
            t.set_context(self)
            if create_image or color_hint:
                loc = t.location
                t.image = self.screenshot.crop((loc.x0, loc.y0, loc.x1, loc.y1))

        if color_hint:
            if len(color_hint) == 2:
                fg_hint = util.make_color(color_hint[0])
                bg_hint = util.make_color(color_hint[1])
            else:
                fg_hint = util.make_color(color_hint)
                bg_hint = None
            for t in texts:
                try:
                    fg, bg = util.find_text_color(t.image)
                    diff = util.color_difference(fg, fg_hint)
                    if bg_hint:
                        diff = (diff + util.color_difference(bg, bg_hint)) * 0.5
                    t.color_confidence = 1.0 - diff
                except:
                    t.color_confidence = 0.0

        if location_hint or color_hint:
            def sort_key(t):
                conf = t.confidence
                if location_hint:
                    conf = conf * t.location_confidence
                if color_hint:
                    conf = conf * t.color_confidence
                return -conf
            return sorted(texts, key=sort_key)

        return texts

    def find_text(self, *args, **kwargs):
        texts = self.find_texts(*args, **kwargs)
        return texts[0]

    def click(self, locator):
        locator = _filter_locator(locator)
        self._clear_screenshot()
        return self.frontend.click(locator[0], locator[1])

    def move(self, locator):
        locator = _filter_locator(locator)
        return self.frontend.move(locator[0], locator[1])
