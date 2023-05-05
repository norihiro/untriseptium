import math
from copy import deepcopy
import PIL.ImageColor


def _linear_distance(a0, a1, b0, b1):
    if a0 <= b0 <= a1:
        return 0
    if a0 <= b1 <= a1:
        return 0
    if b0 <= a0 <= b1:
        return 0
    if b0 <= a1 <= b1:
        return 0
    return min(abs(a0 - b0), abs(a0 - b1), abs(a1 - b1), abs(a1 - b0))


class Location:
    '''
    Holds a coordinate of a rectangle and provides some calculation methods.
    '''
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def center(self):
        '''
        Returns the center coordinate.
        '''
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def diagonal_size(self):
        '''
        Returns the length from top-left to bottom-right.
        '''
        return math.hypot(self.x1 - self.x0, self.y1 - self.y0)

    def distance_at_point(self, another):
        '''
        Returns the shortest distances between two points of self and another
        instance.
        :args:
        - another: An instance of this class.
        '''
        x = _linear_distance(
                self.x0,
                self.x1,
                another.x0,
                another.x1)
        y = _linear_distance(
                self.y0,
                self.y1,
                another.y0,
                another.y1)
        return math.hypot(x, y)

    def __str__(self):
        return f'({self.x0} {self.y0} {self.x1} {self.y1})'

    def str_verbal(self):
        'Returns verbal information of the instance for debugging purpose.'
        c = self.center()
        return f'Location(({self.x0} {self.y0} {self.x1} {self.y1}) ' \
               f'center=({c[0]} {c[1]}) ' \
               f'size={self.x1 - self.x0}x{self.y1 - self.y0} ' \
               f'diagonal={self.diagonal_size():0.1f})'


class Locator:
    '''
    Provides location access on the context
    '''
    def __init__(self):
        self._ctx = None

    def set_context(self, ctx):
        self._ctx = ctx

    def click(self):
        return self._ctx.click(self.center())

    def move(self):
        return self._ctx.move(self.center())


class TextLocator(Locator):
    '''
    Holds a text-search result in the OCR text.
    '''
    def __init__(self):
        self.text = ''
        self.confidence = 0.0
        self.location = None

    def __str__(self):
        return self.text

    def add_location(self, location):
        if not self.location:
            self.location = deepcopy(location)
            return
        self.location.x0 = min(self.location.x0, location.x0)
        self.location.y0 = min(self.location.y0, location.y0)
        self.location.x1 = max(self.location.x1, location.x1)
        self.location.y1 = max(self.location.y1, location.y1)

    def center(self):
        return self.location.center()


def color_difference(c1, c2):
    if len(c1) == len(c2):
        d = 0
        for i in range(0, len(c1)):
            d += abs(c1[i] - c2[i])
        return d / (len(c1) * 255.0)
    raise ValueError('Two colors need to be the same dimention.')


def make_color(c):
    if isinstance(c, str):
        return PIL.ImageColor.getrgb(c)
    return c


def increase_contrast(img, center, gain):
    data = list()
    center = make_color(center)
    for p in img.getdata():
        p = [(c - o) * gain + o for c, o in zip(p, center)]
        p = [0 if c <= 0 else 255 if c >= 255 else c for c in p]
        if len(p) == 3:
            p = (p[0], p[1], p[2])
        data.append(p)
    img = img.copy()
    img.putdata(data)
    return img


def find_background_color(img):
    w = img.width
    h = img.height
    cc_border = dict()
    def add(p):
        if p in cc_border:
            cc_border[p] += 1
        else:
            cc_border[p] = 1
    for y in (0, h - 1):
        for x in range(0, w):
            add(img.getpixel((x, y)))
    for x in (0, w - 1):
        for y in range(0, h):
            add(img.getpixel((x, y)))
    cnt_max = 0
    color_max = None
    for c, v in cc_border.items():
        if v > cnt_max:
            color_max = c
            cnt_max = v
    return color_max


def find_text_color(img):
    bg_color = find_background_color(img)
    cc = dict()
    def add(p, v):
        if p in cc:
            cc[p] += v
        else:
            cc[p] = v
    for p in img.getdata():
        d = color_difference(p, bg_color)
        add(p, d)
    cnt_max = 0
    color_max = None
    for c, v in cc.items():
        if v > cnt_max:
            color_max = c
            cnt_max = v
    return (color_max, bg_color)
