import sys


sys.path.append(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main') 
from utils.window import MetinWindow, OskWindow, InterceptionInput
import utils.utils as ut
import pyautogui
import time


def command_pause():
    time.sleep(0.2)


def main():
    pyautogui.countdown(3)
    osk = InterceptionInput()
    #osk.move_window(x=-1495, y=810)
    aeldra = MetinWindow('MasnoMT2.eu - SEZON II')

    print('Start hitting')
    osk.start_hitting()
    command_pause()

    for i in range(100000):
        print(f'\nIteration {i}:')

        print('Pulling mobs')
        command_pause()
        osk.pull_mobs()

        

        osk.activate_buffs()
        command_pause()

        print('Kill mobs')
        time.sleep(2)

        
        print('Picking up')
        osk.pick_up()
        command_pause()

        # print('Stop hitting')
        # osk.stop_hitting()
        # command_pause()


    print('Done')


if __name__ == '__main__':
    # utils.countdown()
    main()

z