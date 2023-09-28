import sys
import os

# Get the directory of the current script (main.py)
current_directory = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Append the parent directory to sys.path
sys.path.append(parent_directory)

# sys.path.append(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main') 
print(sys.path)
# from bots.masnomt2.botmt45lvl import MetinFarmBot_45lvl
# from bots.masnomt2.botboss50lvl import BossFarmBot_50lvl
from bots.ervelia.metinbot import MetinFarmBot
import cv2 as cv
import utils
from captureAndDetect import CaptureAndDetect
from captureAndDetectMobileNet import CaptureAndDetectMobileNet
from captureAndDetectYolo import CaptureAndDetectYolo
from utils.window import MetinWindow
import tkinter as tk
from utils import SnowManFilter, SnowManFilterRedForest, Dang25metin, Metin_45
from functools import partial

def main():

    # Choose which metin
    metin_selection = {'metin': None}
    #metin_select(metin_selection)
    #metin_selection = metin_selection['metin']
    metin_selection = 'lv_90'
    #hsv_filter = SnowManFilter() if metin_selection != 'lv_90' else SnowManFilterRedForest() 
    hsv_filter = Metin_45()
    # Countdown
    utils.countdown()

    # Get window and start window capture
    metin_window = MetinWindow('Ervelia')

    #capt_detect = CaptureAndDetect(metin_window, r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\masno\metin45\cascade\cascade.xml', hsv_filter)
    
    capt_detect = CaptureAndDetectYolo(metin_window, r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\yolo\best.pt', hsv_filter)
    # Initialize the bot
    bot = MetinFarmBot(metin_window, metin_selection)
    capt_detect.start()
    bot.start()
    
    is_object_detector_enabled = False

    pause = False

    while True:

        key = cv.waitKey(1)
        if not pause:

            state_of_detection = bot.get_object_detector_state()

            capt_detect.set_object_detector_state(state_of_detection)
            # Get new detections
            screenshot, screenshot_time, detection, detection_time, detection_image = capt_detect.get_info()

            # Update bot with new image
            bot.detection_info_update(screenshot, screenshot_time, detection, detection_time)

            if detection_image is None:
                continue

            # Draw bot state on image
            overlay_image = bot.get_overlay_image() 
            detection_image = cv.addWeighted(detection_image, 1, overlay_image, 1, 0)

            # Display image
            cv.imshow('Matches', detection_image)

            # press 'q' with the output window focused to exit.
            # waits 1 ms every loop to process key presses
            if key == ord('w') and not pause: ## w as wait
                capt_detect.stop()
                bot.stop()
                pause = True

        if pause:
            key = cv.waitKey(5)
            if key == ord('w'):
                capt_detect.start()
                bot.start()
                pause = False

        if key == ord('q'):
            capt_detect.stop()
            bot.stop()
            cv.destroyAllWindows()
            break

    print('Done.')

def metin_select(metin_selection):
    metins = {'Lvl. 40: Tal von Seungryong': 'lv_40',
              'Lvl. 60: Hwang-Tempel': 'lv_60',
              'Lvl. 70: Feuerland': 'lv_70',
              'Lvl. 90: Roter Wald': 'lv_90'}

    def set_metin_cb(window, metin, metin_selection): 
        metin_selection['metin'] = metin
        window.destroy()

    window = tk.Tk()
    window.title("Metin2 Bot")
    tk.Label(window, text='Select Metin:').pack(pady=5)

    for button_text, label in metins.items():
        tk.Button(window, text=button_text, width=30, command=partial(set_metin_cb, window, label, metin_selection))\
            .pack(padx=3, pady=3)

    window.mainloop()

if __name__ == '__main__':
    main()
