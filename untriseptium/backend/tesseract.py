import math
import editdistance
from copy import deepcopy
from untriseptium.util import TextLocator, Location


def _weighted_sum(v1, w1, v2, w2):
    return (v1 * w1 + v2 + w2) / (w1 + w2)


class _Text():
    def __init__(self):
        self.level = 0
        self.page_num = 0
        self.block_num = 0
        self.par_num = 0
        self.line_num = 0
        self.word_num = 0
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.confidence = 0
        self.text = ''
        self.location = None

    def __str__(self):
        right = self.left+self.width
        bottom = self.top+self.height
        return f'_Text("{self.text}" ' \
               f'at ({self.left} {self.top} {right} {bottom}) ' \
               f'size {self.width}x{self.height}'

    def _set(self, header, line, offset):
        for i, t in enumerate(line):
            if header[i] == 'level':
                self.level = int(t)
            elif header[i] == 'page_num':
                self.page_num = int(t)
            elif header[i] == 'block_num':
                self.block_num = int(t)
            elif header[i] == 'par_num':
                self.par_num = int(t)
            elif header[i] == 'line_num':
                self.line_num = int(t)
            elif header[i] == 'word_num':
                self.word_num = int(t)
            elif header[i] == 'left':
                self.left = int(t) + offset[0]
            elif header[i] == 'top':
                self.top = int(t) + offset[1]
            elif header[i] == 'width':
                self.width = int(t)
            elif header[i] == 'height':
                self.height = int(t)
            elif header[i] == 'conf':
                self.confidence = float(t) / 100.0
            elif header[i] == 'text':
                self.text = t.strip()
        self.location = Location(self.left, self.top, self.left + self.width,
                                 self.top + self.height)


def _conf_next_word(t, ocr_txt, text_confidence):
    confidence = t.confidence * text_confidence
    if t.location:
        geo_dist = t.location.distance_at_point(ocr_txt.location)
        t_size = t.location.diagonal_size()
        n_size = ocr_txt.location.diagonal_size()
        char_size = (t_size + n_size) / (len(t.text) + len(ocr_txt.text))
        if geo_dist > char_size:
            ex = (geo_dist - char_size) / char_size
            confidence *= math.exp(-ex * ex)
    return confidence


def _new_text_locator(t, ocr_txt, confidence):
    t = deepcopy(t)
    t.text = (t.text + ' ' + ocr_txt.text) if t.text else ocr_txt.text
    t.confidence = confidence
    t.add_location(ocr_txt.location)
    return t


def _conf_old_word(t, current_location):
    # If the found word locates too far from current location, lower the
    # priority.
    if t.location and t.text:
        geo_dist = t.location.distance_at_point(current_location)
        word_size = t.location.diagonal_size()
        if geo_dist > word_size:
            ex = (geo_dist - word_size) / word_size
            return t.confidence * math.exp(-ex * ex)
    return t.confidence


def _ocrdata_has_valid_data(ocrdata):
    for t in ocrdata:
        if t.text:
            return True
    return False


class BackendTesseract:
    def __init__(self):
        # FIXME: Workaround to avoid system to be shutdown
        # https://github.com/tesseract-ocr/tesseract/issues/2064
        # This workaround should be removed or limited to the certain system
        # only.
        import os
        os.environ['OMP_THREAD_LIMIT'] = '1'

        self.lang = None
        # FIXME: I don't know these magic numbers are ok.
        # When ocr_unconfidence_ratio >= confidence_threshold, all
        # ambiguous words will match.
        # FIXME: Consider to define some presets for these numbers.
        self.ocr_unconfidence_ratio = 0.4
        self.confidence_threshold = 0.2

    def preset(self, preset_name):
        if preset_name == 'ja':
            self.lang = 'jpn'
            self.find_texts = self._find_texts_para_partial

    def _ocr_subregion(self, image, subregion):
        if subregion:
            image = image.crop(subregion)
            offset = subregion
        offset = (0, 0)
        from pytesseract import pytesseract
        tsv = pytesseract.image_to_data(image, lang=self.lang)

        data = list()
        header = None
        for line in tsv.split('\n'):
            line = line.split('\t')
            if not header:
                header = line
                continue
            if len(line) < len(header):
                continue
            d = _Text()
            try:
                d._set(header, line, offset)
            except BaseException as e:
                raise (Exception('Failed to parse line: "%s"' % line, e))
            data.append(d)

        return data

    def ocr(self, image):
        data = self._ocr_subregion(image, None)

        # Tesseract sometimes returns nothing when the image is big.
        # This is a workaround to have smaller image.
        if not _ocrdata_has_valid_data(data):
            h = int(image.height / 8)
            for y in range(0, image.height, int(h / 2)):
                data1 = self._ocr_subregion(image, (0, y, image.width, y + h))
                for t in data1:
                    data.append(t)

        return data

    def _conf_ocr_text(self, ocr_txt, ideal_txt):
        distance = editdistance.eval(ocr_txt.text, ideal_txt)
        max_length = max(len(ocr_txt.text), len(ideal_txt))
        ocr_invconf = (1.0 - ocr_txt.confidence) * self.ocr_unconfidence_ratio
        return ((max_length - distance) * ocr_txt.confidence +
                distance * ocr_invconf) / max_length

    def find_texts(self, data, text):
        return self._find_texts_para_partial(data, text)

    def _find_texts_word(self, data, text):
        text = text.split(' ')

        def init_dp():
            t0 = TextLocator()
            t1 = TextLocator()
            t1.confidence = 1.0
            return [t1 if i == 0 else t0 for i in range(len(text) + 1)]

        dp0 = init_dp()
        cand = list()

        for ocr_txt in data:
            if ocr_txt.confidence < 0:
                continue
            dp1 = init_dp()

            for i, t in enumerate(text):
                confidence = self._conf_ocr_text(ocr_txt, t)
                if confidence < self.confidence_threshold:
                    continue

                dp_confidence = _conf_next_word(dp0[i], ocr_txt, confidence)
                if dp_confidence > dp1[i + 1].confidence:
                    d = _new_text_locator(dp0[i], ocr_txt, dp_confidence)
                    dp1[i + 1] = d
                    if i == len(text) - 1:
                        cand.append(d)

            for i, d in enumerate(dp1):
                c = _conf_old_word(dp0[i], ocr_txt.location)

                if d.confidence > c:
                    dp0[i] = d

        return sorted(cand, key=lambda d: -d.confidence)

    def _find_texts_char(self, data, text):
        def init_dp():
            t0 = TextLocator()
            t1 = TextLocator()
            t1.confidence = 1.0
            return [t1 if i == 0 else t0 for i in range(len(text) + 1)]

        dp0 = init_dp()
        cand = list()

        for ocr_txt in data:
            if ocr_txt.confidence < 0:
                continue
            dp1 = init_dp()

            for i_start in range(len(text)):
                for i_end in range(i_start + 1, len(text) + 1):
                    t = text[i_start:i_end].strip()

                    conf = self._conf_ocr_text(ocr_txt, t)
                    if conf < self.confidence_threshold:
                        continue

                    dp_conf = _conf_next_word(dp0[i_start], ocr_txt, conf)
                    if dp_conf > dp1[i_end].confidence:
                        d = _new_text_locator(dp0[i_start], ocr_txt, dp_conf)
                        dp1[i_end] = d
                        if i_end == len(text):
                            cand.append(d)

            for i, d in enumerate(dp1):
                c = _conf_old_word(dp0[i], ocr_txt.location)

                if d.confidence > c:
                    dp0[i] = d

        return sorted(cand, key=lambda d: -d.confidence)

    def _find_texts_para(self, data, text):
        cand = list()

        def _process(t):
            confidence = self._conf_ocr_text(t, text)
            if confidence < self.confidence_threshold:
                return
            d = deepcopy(t)
            d.confidence = confidence
            cand.append(d)

        t = None
        for ocr_txt in data:
            if ocr_txt.confidence < 0:
                if t and t.text:
                    _process(t)
                t = TextLocator()
                t.confidence = 1.0
                continue

            t.confidence = _weighted_sum(
                    t.confidence, len(t.text),
                    ocr_txt.confidence, len(ocr_txt.text))
            t.text = (t.text + ' ' + ocr_txt.text) if t.text else ocr_txt.text
            t.add_location(ocr_txt.location)

        _process(t)

        return sorted(cand, key=lambda d: -d.confidence)

    def _find_texts_para_partial(self, data, text):
        cand = list()

        for i_end in range(len(data)):
            if data[i_end].confidence < 0:
                i_para_start = i_end + 1
                continue

            for i_start in range(i_para_start, i_end + 1):
                t = TextLocator()
                conf_tot = 0.0
                textlen_total = 0
                for i in range(i_start, i_end + 1):
                    ocr_txt = data[i]
                    conf_tot += ocr_txt.confidence * len(ocr_txt.text)
                    textlen_total += len(ocr_txt.text)
                    if t.text:
                        t.text = t.text + ' ' + ocr_txt.text
                    else:
                        t.text = ocr_txt.text
                    t.add_location(ocr_txt.location)
                t.confidence = conf_tot / textlen_total if textlen_total else 0

                confidence = self._conf_ocr_text(t, text)
                if confidence < self.confidence_threshold:
                    continue

                d = deepcopy(t)
                d.confidence = confidence
                cand.append(d)

        return sorted(cand, key=lambda d: -d.confidence)
