import random
import pyautogui
import win32gui, win32ui, win32con, win32com.client
from time import sleep
import subprocess
import pygetwindow as gw
import numpy as np
import pythoncom
import ctypes
import sys
import src.interception as interception
interception.inputs.keyboard = 1
interception.inputs.mouse = 10
import psutil
import pygetwindow as gw

class Window:
    def __init__(self, window_name):
        self.name = window_name
        self.hwnd = win32gui.FindWindow(None, window_name)
        if self.hwnd == 0:
            raise Exception(f'Window "{self.name}" not found!')

        self.gw_object = gw.getWindowsWithTitle(self.name)[0]

        rect = win32gui.GetWindowRect(self.hwnd)
        border = 8
        title_bar = 31
        self.x = rect[0] + border
        self.y = rect[1] + title_bar
        self.width = rect[2] - self.x - border
        self.height = rect[3] - self.y - border

        self.cropped_x = border
        self.cropped_y = title_bar

        pythoncom.CoInitialize()
        win32gui.ShowWindow(self.hwnd, 5)
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.shell.SendKeys('%')
        win32gui.SetForegroundWindow(self.hwnd)

    def set_window_foreground(self):
        self.hwnd = win32gui.FindWindow(None, self.name)
        win32gui.ShowWindow(self.hwnd, 5)
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.shell.SendKeys('%')
        win32gui.SetForegroundWindow(self.hwnd)

    def close_window(self):
        self.hwnd = win32gui.FindWindow(None, self.name)
        #win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        #win32gui.CloseWindow(self.hwnd)
        print("The windows is now closed")

    def find_process_and_kill_window(self):
    # Find the window by title
        window = gw.getWindowsWithTitle(self.name)

        if window:
            window = window[0]
            pid = None

            for proc in psutil.process_iter(attrs=['pid', 'name']):
                try:
                    if "metin2client" in proc.info['name']:
                        pid = proc.info['pid']
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if pid:
                try:
                    process = psutil.Process(pid)  # Get the process by PID
                    process.terminate()  # Terminate the process
                    print(f"Terminated process with PID {pid}")
                except psutil.NoSuchProcess:
                    print(f"Process with PID {pid} not found")
                except psutil.AccessDenied:
                    print(f"Access denied when terminating process with PID {pid}")
            else:
                print(f"No process ID found for window '{self.name}'")
        else:
            print(f"Window with title '{self.name}' not found")

    def get_relative_mouse_pos(self):
        curr_x, curr_y = pyautogui.position()
        return curr_x - self.x, curr_y - self.y

    def print_relative_mouse_pos(self, loop=False):
        repeat = True
        while repeat:
            repeat = loop
            print(self.get_relative_mouse_pos)
            if loop:
                sleep(1)

    def mouse_move(self, x, y):
        #pyautogui.moveTo(self.x + x, self.y + y, duration=0.1)
        interception.move_to(self.x + x, self.y + y)

    def mouse_click(self, x=None, y=None):
        sleep(0.2)
        if x is None and y is None:
            x, y = self.get_relative_mouse_pos()
        interception.click(self.x + x, self.y + y)
        #pyautogui.click(self.x + x, self.y + y, duration=0.1)

    def mouse_right_click(self, x=None, y=None):
        sleep(0.03)
        if x is None and y is None:
            x, y = self.get_relative_mouse_pos()
        interception.right_click(1)

    def move_window(self, x, y):
        win32gui.MoveWindow(self.hwnd, x - 7, y, self.width, self.height, True)
        self.x, self.y = x, y

    def limit_coordinate(self, pos):
        pos = list(pos)
        if pos[0] < 0: pos[0] = 0
        elif pos[0] > self.width: pos[0] = self.width
        if pos[1] < 0: pos[1] = 0
        elif pos[1] > self.height: pos[1] = self.height
        return tuple(pos)

    def capture(self):
        # https://stackoverflow.com/questions/6312627/windows-7-how-to-bring-a-window-to-the-front-no-matter-what-other-window-has-fo\
        try:
            wDC = win32gui.GetWindowDC(self.hwnd)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, self.width, self.height)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0, 0), (self.width, self.height), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)
            # dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')

            # https://stackoverflow.com/questions/41785831/how-to-optimize-conversion-from-pycbitmap-to-opencv-image
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.fromstring(signedIntsArray, dtype='uint8')
            img.shape = (self.height, self.width, 4)

            # Free Resources
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, wDC)
            win32gui.DeleteObject(dataBitMap.GetHandle())

            # Drop the alpha channel
            img = img[..., :3]

            # make image C_CONTIGUOUS
            img = np.ascontiguousarray(img)

            return img
        except:
            print("Failed to capture window, will open a new window")

            file_path = r"C:\Users\Filip\Downloads\MasnoMT2\patcher.exe"
            subprocess.run(["runas", "/user:Administrator", file_path])

class MetinWindow(Window):
    def __init__(self, window_name):
        self.name = window_name
        self.hwnd = win32gui.FindWindow(None, window_name)
        if self.hwnd == 0:
            self.open_new_window()
            #raise Exception(f'Window "{self.name}" not found!')
        
        super().__init__(window_name)
        self.set_window_foreground()

    def activate(self):
        self.mouse_move(40, -15)
        sleep(0.1)
        self.mouse_click()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
        
    def check_if_window_is_opened(self):
        window = win32gui.FindWindow(None, self.name)
        if window == 0:
            return False
        else:
            return True
    def open_new_window(self):
        
        #game_path = r"C:\Users\Filip\Desktop\Ervelia_official_011\Ervelia.pl\metin2client.exe"
        game_path = r"C:\Users\Filip\Desktop\Ervelia_official_011\Ervelia.pl\Ervelia Patcher.exe"
        game_dir = r"C:\Users\Filip\Desktop\Ervelia_official_011\Ervelia.pl"
        # Request UAC elevation
        ctypes.windll.shell32.ShellExecuteW(None, "runas", game_path, None, game_dir, 1)
        sleep(60)
        
        interception.move_to(1100,650)
        patcher = win32gui.FindWindow(None, "Ervelia Patcher")
        win32gui.ShowWindow(patcher, 5)
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(patcher)
        sleep(0.5)
        interception.left_click(1)
        sleep(20)
        max_wait_time = 200
        time_passed = 0
        while not self.check_if_window_is_opened():
            sleep(1)
            time_passed += 1
            if time_passed > max_wait_time:
                break
        if not self.check_if_window_is_opened():
            self.open_new_window()
        
        
    def capture(self):
        # https://stackoverflow.com/questions/6312627/windows-7-how-to-bring-a-window-to-the-front-no-matter-what-other-window-has-fo\
        try:
            wDC = win32gui.GetWindowDC(self.hwnd)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, self.width, self.height)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0, 0), (self.width, self.height), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)
            # dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')

            # https://stackoverflow.com/questions/41785831/how-to-optimize-conversion-from-pycbitmap-to-opencv-image
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.fromstring(signedIntsArray, dtype='uint8')
            img.shape = (self.height, self.width, 4)

            # Free Resources
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, wDC)
            win32gui.DeleteObject(dataBitMap.GetHandle())

            # Drop the alpha channel
            img = img[..., :3]

            # make image C_CONTIGUOUS
            img = np.ascontiguousarray(img)

            return img
        except:
            try:
                print("Failed to capture window, will try to open a new window")

                self.hwnd = win32gui.FindWindow(None, self.name)
                if self.hwnd != 0:
                    #self.open_new_window()
                    self.set_window_foreground()
                    return self.capture()
                if self.hwnd == 0:
                    self.open_new_window()
                    self.set_window_foreground()
                    return self.capture()
                return self.capture()
            except:
                return self.capture()

class InterceptionInput(Window):
    def __init__(self, window_name):
        super().__init__(window_name)
        pass

    def start_hitting(self):
        sleep(0.03)
        interception.key_down("space")

    def start_spinning(self):
        sleep(0.03)
        interception.key_down("e")
        sleep(0.03)
        interception.key_down("w")
        sleep(0.03)

    def press_enter(self):
        interception.press('enter', 2)
        sleep(0.3)
    
    def stop_spinning(self):
        interception.key_up("e")
        sleep(0.03)
        interception.key_up("w")
        sleep(0.03)

    def stop_hitting(self):
        interception.key_up("space")

    def pull_mobs(self):
        interception.press("3", 3, 0.01)

    def pick_up(self):
        interception.key_down("z")
        sleep(0.8)
        interception.key_up("z")
        
    def move_with_camera_rotation(self):
        interception.key_down("w")
        sleep(0.05)
        interception.key_down("e")
        sleep(0.3)
        interception.key_up("w")
        sleep(0.05)
        interception.key_up("e")

    def activate_flag(self):
        interception.press("3")

    def activate_horse_dodge(self):
        interception.press("4")

    def activate_dodge(self, flag=False):
        if flag: self.activate_flag()
        else: self.activate_horse_dodge()


    def send_mount_away(self):
        # self.press_key(button='Ctrl', mode='click')
        # sleep(0.2)
        # self.press_key(button='b', mode='click')
        pass

    def call_mount(self):
        interception.press("1")
        # self.press_key(button='Fn', mode='click')
        # sleep(0.2)
        # self.press_key(button='1', mode='click')
        

    def recall_mount(self):
        self.call_mount()
        # self.send_mount_away()
        self.un_mount()
        # self.send_mount_away()
        # self.call_mount()
        # self.un_mount()
        pass

    def find_metin(self):
        interception.press("f1")
        sleep(0.1)


    def activate_buffs(self):
        interception.press("f5")

    def start_rotating_up(self):
        interception.key_down("g")

    def stop_rotating_up(self):
        interception.key_up("g")

    def rotate_with_mouse(self):
        
        self.mouse_move(random.randint(300, 400), random.randint(300, 400))
        sleep(0.03)
        # with interception.hold_mouse("right"):
        #     sleep(0.10)
        #     x, y = self.get_relative_mouse_pos()
        #     interception.move_relative(30, 0)
        #     #self.mouse_move(x+random.randint(30, 50), y)

        #sleep(0.1)
        interception.mouse_down('right')
        sleep(0.02)
        interception.move_relative(random.randint(15, 35), 0)
        sleep(0.02)
        interception.mouse_up('right')
        sleep(0.03)
    def start_rotating_down(self):
        interception.key_down("t")

    def stop_rotating_down(self):
        interception.key_up("t")

    def start_rotating_horizontally(self):
        interception.key_down("e")

    def stop_rotating_horizontally(self):
       interception.key_up("e")

    def ride_through_units(self):
        #self.press_key(button='4', mode='click', count=1)
        pass
    def un_mount(self):
        interception.key_down("ctrl")
        sleep(0.05)
        interception.key_down("g")
        sleep(0.05)
        interception.key_up("ctrl")
        sleep(0.05)
        interception.key_up("g")

        # self.press_key(button='Ctrl', mode='click')
        # sleep(0.4)
        # self.press_key(button='h', mode='click')
        
    def activate_aura(self):
        interception.press("2")

    def activate_teleports(self):
        interception.key_down("ctrl")
        sleep(0.04)
        interception.key_down("x")
        sleep(0.04)
        interception.key_up("ctrl")
        sleep(0.04)
        interception.key_up("x")

    def turn_poly_off(self):
        sleep(0.04)
        interception.press("p")
        sleep(0.3)

    def turn_poly_on(self):
        sleep(0.1)
        interception.press("f4")
        sleep(0.2)

    def activate_berserk(self):
        interception.press("2")

    def heal_yourself(self):
        interception.press("1")

    def start_zooming_out(self):
        interception.key_down("f")

    def stop_zooming_out(self):
        interception.key_up("f")

    def start_zooming_in(self):
        interception.key_down("r")

    def stop_zooming_in(self):
        interception.key_up("r")



class OskWindow(Window):
    def __init__(self, window_name):
        if win32gui.FindWindow(None, window_name) == 0:
            returned_value = subprocess.Popen('osk', shell=True)
            sleep(1)
        super().__init__(window_name)

        self.width, self.height = 576, 173
        self.gw_object.resizeTo(self.width, self.height)

        self.key_pos = {'space': (148, 155), 'Fn': (11, 150), '1': (55, 61), '2': (79, 67),
                        '3': (100, 65), '4': (122, 59), 'z': (67, 132), 'e': (87, 87),
                        'q': (40, 85), 'g': (134, 107), 't': (129, 86), 'Ctrl': (35, 150),
                        'h': (159, 109), 'r': (107, 88), 'f': (114, 109), 'b': (156, 134)
                        }

    def start_hitting(self):
        self.press_key(button='space', mode='down')

    def stop_hitting(self):
        self.press_key(button='space', mode='up')

    def pull_mobs(self):
        self.press_key(button='2', mode='click', count=3)

    def pick_up(self):
        self.press_key(button='z', mode='click', count=1)

    def activate_tp_ring(self):
        self.press_key(button='3', mode='click', count=1)

    def send_mount_away(self):
        self.press_key(button='Ctrl', mode='click')
        sleep(0.2)
        self.press_key(button='b', mode='click')

    def call_mount(self):
        self.press_key(button='Fn', mode='click')
        sleep(0.2)
        self.press_key(button='1', mode='click')

    def recall_mount(self):
        self.send_mount_away()
        self.un_mount()
        self.send_mount_away()
        self.call_mount()
        self.un_mount()

    def start_rotating_up(self):
        self.press_key(button='g', mode='down')

    def stop_rotating_up(self):
        self.press_key(button='g', mode='up')

    def start_rotating_down(self):
        self.press_key(button='t', mode='down')

    def stop_rotating_down(self):
        self.press_key(button='t', mode='up')

    def start_rotating_horizontally(self):
        self.press_key(button='e', mode='down')

    def stop_rotating_horizontally(self):
        self.press_key(button='e', mode='up')

    def ride_through_units(self):
        self.press_key(button='4', mode='click', count=1)

    def un_mount(self):
        self.press_key(button='Ctrl', mode='click')
        sleep(0.4)
        self.press_key(button='h', mode='click')

    def activate_aura(self):
        self.press_key(button='1', mode='click')

    def activate_berserk(self):
        self.press_key(button='2', mode='click')

    def start_zooming_out(self):
        self.press_key(button='f', mode='down')

    def stop_zooming_out(self):
        self.press_key(button='f', mode='up')

    def start_zooming_in(self):
        self.press_key(button='r', mode='down')

    def stop_zooming_in(self):
        self.press_key(button='r', mode='up')

    def press_key(self, button, mode='click', count=1):
        x, y = self.x, self.y
        if button not in self.key_pos.keys():
            raise Exception('Unknown key!')
        else:
            x += self.key_pos[button][0]
            y += self.key_pos[button][1]
            pyautogui.moveTo(x=x, y=y)
        if mode == 'click':
            for i in range(count):
                pyautogui.mouseDown()
                sleep(0.1)
                pyautogui.mouseUp()
        elif mode == 'down':
            pyautogui.mouseDown()
        elif mode == 'up':
            pyautogui.mouseUp()
