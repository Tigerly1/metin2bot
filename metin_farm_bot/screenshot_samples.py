#from utils.window import MetinWindow, OskWindow
import sys
sys.path.append(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main') 
from utils.window import MetinWindow, OskWindow, InterceptionInput
import pyautogui
import time
import cv2 as cv
from utils.vision import Vision, SnowManFilter



def command_pause():
    time.sleep(0.2)


def main():
    pyautogui.countdown(3)
    aeldra = MetinWindow('Ervelia')
    vision = Vision()
    vision.init_control_gui()
    sm_filter = SnowManFilter()

    count = {'p': 0, 'n': 0}

    while True:
        loop_time = time.time()
        screenshot = aeldra.capture()

        #processed_screenshot = vision.apply_hsv_filter(screenshot, hsv_filter=sm_filter)
        processed_screenshot = vision.apply_hsv_filter(screenshot)

        cv.imshow('Video Feed', processed_screenshot)
        # print(f'{round(1 / (time.time() - loop_time),2)} FPS')

        # press 'q' with the output window focused to exit.
        # waits 1 ms every loop to process key presses
        key = cv.waitKey(1)
        if key == ord('q'):
            cv.destroyAllWindows()
            break
        elif key == ord('p'):
            cv.imwrite(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\water_map\metin\new\{}.jpg'.format(int(loop_time)), processed_screenshot)
            count['p'] += 1
            print(f'Saved positive sample. {count["p"]} total.')
        elif key == ord('n'):
            cv.imwrite(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\masno\metin45\neg\{}.jpg'.format(int(loop_time)), processed_screenshot)
            count['n'] += 1
            print(f'Saved negative sample. {count["n"]} total.')


if __name__ == '__main__':
    main()

