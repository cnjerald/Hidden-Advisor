from pynput import keyboard
import time
import pyautogui
import pytesseract
from openai import OpenAI
import re
import pyperclip
import pyautogui
import re
from pynput import keyboard
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
import io
from PIL import Image
import cv2
import numpy as np
import base64

SYSTEM_PROMPT = """
You are an AI engine integrated into a competitive programming tool.

Your job is to analyze the provided text and determine its type.

1) If it is a LeetCode-style coding problem:
- Output ONLY valid Python code.
- No explanations.
- No markdown.
- No backticks.
- No comments.
- No extra text.
- The code must be directly executable.

2) If it is a multiple-choice question:
- Output ONLY a single uppercase letter.
- Must be exactly one of: A, B, C, or D.
- No punctuation.
- No explanation.
- No extra text.

3) If unclear:
- Output: UNKNOWN

Follow the output rules strictly.
"""


# Globals
typing_active = False
exit_program = False
last_press_time = 0
DOUBLE_PRESS_DELAY = 0.4

# Clients
rgb_client = OpenRGBClient()
device = rgb_client.devices[0]
print(device)




# API KEY
client = OpenAI(api_key="Key Here")
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Windows Tesseract path
pytesseract.pytesseract.tesseract_cmd = tesseract_path
last_press_time = 0
DOUBLE_PRESS_DELAY = 0.4


def preprocess_for_tesseract(screenshot):
    """
    Convert screenshot to grayscale + thresholding for better OCR accuracy
    """
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def set_color_based_on_answer(answer):
    answer = answer.upper()
    if answer == "A":
        device.set_color(RGBColor(0, 255, 0))
    elif answer == "B":
        device.set_color(RGBColor(0, 0, 255))
    elif answer == "C":
        device.set_color(RGBColor(255, 255, 0))
    elif answer == "D":
        device.set_color(RGBColor(255, 0, 0))
    else:
        device.set_color(RGBColor(0, 0, 0))



def run_ocr_and_send():
    # Capture + preprocess screenshot
    screenshot = pyautogui.screenshot()
    processed_image = preprocess_for_tesseract(screenshot)
    
    # Optional OCR text
    text_hint = pytesseract.image_to_string(processed_image)
    text_hint = " ".join(text_hint.split())
    
    # Convert image to base64 string
    img_byte_arr = io.BytesIO()
    processed_image.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    base64_image = base64.b64encode(img_byte_arr.read()).decode('utf-8')

    device.set_color(RGBColor(0,0,0))

    print(text_hint)
    
    # Send to GPT with vision
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Answer the question in this image. OCR hints: {text_hint}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300
    )
    
    reply = response.choices[0].message.content.strip()
    print("GPT Reply:", reply)
    
    answer = reply.upper()
    if answer in ["A", "B", "C", "D"]:
        set_color_based_on_answer(answer)
    else:
        pyperclip.copy(reply)
        print("Code copied to clipboard.")

def on_press(key):
    global last_press_time, exit_program
    try:
        if key == keyboard.Key.f2:
            current_time = time.time()
            if current_time - last_press_time < DOUBLE_PRESS_DELAY:
                run_ocr_and_send()
            last_press_time = current_time
        elif key == keyboard.Key.esc:
            exit_program = True
            return False
    except AttributeError:
        pass

print("Listening... F4 toggle | Double-H OCR | ESC quit")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
