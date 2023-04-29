import math


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
            self.location = location
            return
        self.location.x0 = min(self.location.x0, location.x0)
        self.location.y0 = min(self.location.y0, location.y0)
        self.location.x1 = max(self.location.x1, location.x1)
        self.location.y1 = max(self.location.y1, location.y1)

    def center(self):
        return self.location.center()
