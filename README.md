# Untriseptium

A GUI automation library in python with OCR.

## Example usage

Below is an example to run OCR on a screen, find a text, and click it.

```python
import untriseptium
u = untriseptium.Untriseptium()
u.capture()
u.find_text('Sign in').click()
```

## Acknowledgments

- [pyautogui](https://github.com/asweigart/pyautogui) - A frontend to access the desktop
- [Tesseract](https://github.com/tesseract-ocr/tesseract) - An open source OCR engine
- [pytesseract](https://pypi.org/project/pytesseract/) - An interface for python to access Tesseract
