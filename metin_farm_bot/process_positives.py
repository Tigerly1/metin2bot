import sys
sys.path.append(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main') 
from utils.window import MetinWindow, OskWindow, InterceptionInput
import pyautogui
import time
import cv2 as cv
from utils.samples import Samples
from utils.samples import generate_negative_description_file



def main():
    generate_negative_description_file(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\masno\metin45\neg')
    #generate_negative_description_file(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\negs_from_pos_1691454986')
    # pyautogui.countdown(2)
    # size = (24, 32)
    # samples = Samples('pos.txt', desired_size=size)
    # #samples.display_images(resized=True)
    # samples.generate_negs_from_samples(f'metin_farm_bot/classifier/negs_from_pos_{int(time.time())}')
    # samples.export_samples(f'metin_farm_bot/classifier/sample_export_{int(time.time())}', resized=True)


    print('Done')

if __name__ == '__main__':
    main()

