import math
from utils.window import MetinWindow, OskWindow, InterceptionInput
import pyautogui
import time
import cv2 as cv
from utils.vision import Vision, SnowManFilter, MobInfoFilter
import numpy as np
import enum
from threading import Thread, Lock
import datetime
from utils import * #get_metin_needle_path, get_tesseract_path
import pytesseract
import re
import datetime

#from credentials import bot_token, chat_id
#import telegram


class BotState(enum.Enum):
    INITIALIZING = 0
    SEARCHING = 1
    CHECKING_MATCH = 2
    MOVING = 3
    HITTING = 4
    COLLECTING_DROP = 5
    RESTART = 6
    KILLING_MOBS = 7
    WAITING = 10
    ERROR = 100
    DEBUG = 101
    

class MetinFarmBot:

    def __init__(self, metin_window, metin_selection):
        self.metin_window = metin_window
        self.metin = metin_selection

        self.osk_window = InterceptionInput("Ervelia")
        #self.osk_window.move_window(x=-1495, y=810)

        self.vision = Vision()
        self.mob_info_hsv_filter = MobInfoFilter()

        self.screenshot = None
        self.screenshot_time = None
        self.detection_result = None
        self.detection_time = None

        self.overlay_image = None
        self.info_text = ''
        self.delay = None
        self.detected_zero_percent = 0
        self.move_fail_count = 0

        self.calibrate_count = 0
        self.calibrate_threshold = 0
        self.rotate_count = 0
        self.rotate_threshold = 10

        self.started_hitting_time = None
        self.started_moving_time = None
        self.next_metin = None
        self.last_metin_time = time.time()

        self.stopped = False
        self.state_lock = Lock()
        self.info_lock = Lock()
        self.overlay_lock = Lock()

        self.started = time.time()
        #@self.send_telegram_message('Started')
        self.metin_count_120 = 0
        self.metin_count_water = 0
        self.last_error = None
        self.dangeons_count = 0



        self.current_click = 0
        self.multiple_detection_result = []

        self.current_channel = 5
        self.current_metin_respawn = 1
        self.metin_teleports_passed = 0
        self.current_metin_name = "water"
        self.current_channel_skips = 0

        self.buff_interval = 76
        self.default_killing_mobs_time = 52
        self.killing_mobs_time = 0
        self.last_buff = time.time()

        self.is_object_detector_enabled = False

        pytesseract.pytesseract.tesseract_cmd = utils.get_tesseract_path()

        self.time_entered_state = None
        self.state = None
        self.switch_state(BotState.INITIALIZING)

    def run(self):
        while not self.stopped:

            if self.state == BotState.INITIALIZING:
                self.metin_window.activate()
                self.check_if_player_is_logged_out()
                self.osk_window.turn_poly_off()
                self.osk_window.turn_poly_on()
                #self.respawn_if_dead()
                #self.teleport_back()
                self.calibrate_view()
                #self.osk_window.recall_mount()
               
                #self.metin_window.find_process_and_kill_window()
                #self.started = time.time()
                #self.change_metin_respawn_or_channel()
                #self.turn_on_buffs()
                self.switch_state(BotState.SEARCHING)

            if self.state == BotState.SEARCHING:
                # Check if screenshot is recent
                self.check_if_player_is_logged_out()
                self.close_window_if_not_working()
                self.set_object_detector_state(True)
                self.respawn_if_dead()

                current_time = datetime.datetime.now()
                current_minute = current_time.minute

                if (current_minute < 12 or current_minute > 58) and self.current_metin_name=="120":
                    self.current_metin_name="water"
                    self.current_channel_skips = 0
                    self.change_metin_respawn_or_channel()

                if self.rotate_count == 0 and not self.does_metin_exist_on_current_channel():
                    if self.current_channel_skips > 11:
                        self.current_channel_skips = 0
                        self.current_metin_name="120"
                        self.change_metin_respawn_or_channel()
                    else:
                        self.current_channel = (self.current_channel % 8) + 1
                        self.change_channel(self.current_channel)
                        if  self.current_metin_name=="water":
                            self.current_channel_skips += 1
                    


                elif self.screenshot is not None and self.detection_time is not None and \
                        self.detection_time > self.time_entered_state + 0.03:
                    
                    
                    #If no matches were found
                    if self.detection_result is None:
                        self.put_info_text('No metin found, will rotate!')
                        if self.rotate_count > self.rotate_threshold:
                            
                            
                            self.put_info_text(f'Rotated {self.rotate_count} times -> Recalibrate!')
                            if self.calibrate_count >= self.calibrate_threshold:
                                self.rotate_count = 0
                                self.change_metin_respawn_or_channel()
                                # self.put_info_text(f'Recalibrated {self.calibrate_count} times -> Error!')
                                # #self.send_telegram_message('Entering error mode because no metin could be found!')
                                # self.switch_state(BotState.ERROR)
                            else:
                                self.calibrate_count += 1
                                self.rotate_count = 0
                                self.calibrate_view()
                                self.time_entered_state = time.time()
                        else:
                            self.rotate_count += 1
                            self.rotate_view()
                            self.time_entered_state = time.time()
                        
                        
                    else:
                        # self.put_info_text(f'Best match width: {self.detection_result["best_rectangle"][2]}')
                        
                        self.metin_window.mouse_move(*self.detection_result['click_pos'])
                        time.sleep(0.03)
                        self.switch_state(BotState.CHECKING_MATCH)
                        
                        

            if self.state == BotState.CHECKING_MATCH:
                time.sleep(0.07)
                pos = self.metin_window.get_relative_mouse_pos()
                width = 200
                height = 150
                top_left = self.metin_window.limit_coordinate((int(pos[0] - width / 2), pos[1] - height))
                bottom_right = self.metin_window.limit_coordinate((int(pos[0] + width / 2), pos[1]))
                
                self.info_lock.acquire()
                time.sleep(0.02)
                new_screen_after_hovering = []
                new_screen_after_hovering = self.metin_window.capture()
                time.sleep(0.02)

                if len(new_screen_after_hovering) > 0:
                    mob_title_box = self.vision.extract_section(new_screen_after_hovering, top_left, bottom_right)
                    
                    match_loc = ""
                    
                    try:
                        match_loc, match_val = self.vision.template_match_alpha(mob_title_box, utils.get_ervelia_metin_needle(), 999999)
                    except Exception as e:
                        
                        print(e)
                        pass
                self.info_lock.release()

                if match_loc is not None:
                    self.metin_window.mouse_click()
                    time.sleep(0.02)
                    self.osk_window.activate_dodge(self.current_metin_name=="water")
                    #self.osk_window.activate_flag()
                    time.sleep(0.02)
                    self.set_object_detector_state(False)
                    self.put_info_text('Metin found!')
                    self.turn_on_buffs()
                    self.osk_window.ride_through_units()
                    self.switch_state(BotState.MOVING)

                else:
                  
                    try:
                        self.multiple_detection_result = []
                        self.current_click = 0
                        self.put_info_text('No metin found -> rotate and search again!')
                        if self.rotate_count > self.rotate_threshold:
                            self.rotate_count = 0
                            self.change_metin_respawn_or_channel()
                            self.switch_state(BotState.SEARCHING)

                        else:
                            self.rotate_view()
                            self.rotate_count += 1
                            self.switch_state(BotState.SEARCHING)

                    except Exception as e:

                        self.multiple_detection_result = []
                        self.current_click = 0
                        self.put_info_text('No metin found -> rotate and search again!')
                        self.rotate_view()
                        self.rotate_count += 1
                        self.switch_state(BotState.SEARCHING)
                        pass


            if self.state == BotState.MOVING:
                if self.started_moving_time is None:
                    self.started_moving_time = time.time()

                result = self.get_mob_info()
                # print(result)
                #print(result[0])

                if self.started_moving_time > 4 and self.started_moving_time < 4.1:
                    self.osk_window.activate_dodge(self.current_metin_name=="water")
                    time.sleep(0.05)
                    self.osk_window.heal_yourself()

                if result is not None and result[1] < 1000:
                    self.started_moving_time = None
                    self.move_fail_count = 0
                    self.put_info_text(f'Started hitting {result[0]}')
                    self.switch_state(BotState.HITTING)

                elif time.time() - self.started_moving_time >= 8:
                    self.started_moving_time = None
                    #self.osk_window.pick_up()
                    #self.metin_count += 1
                    #self.switch_state(BotState.RESTART)
                    self.switch_state(BotState.SEARCHING)
                    # self.move_fail_count += 1
                    # if self.move_fail_count >= 4:
                    #     self.move_fail_count = 0
                    #     self.put_info_text(f'Failed to move to metin {self.move_fail_count} times -> Error!')
                    #     #self.send_telegram_message('Entering error mode because couldn\'t move to metin!')
                    #     self.switch_state(BotState.ERROR)
                    # else:
                    #     self.put_info_text(f'Failed to move to metin ({self.move_fail_count} time) -> search again')
                    #     self.rotate_view()
                    #     self.switch_state(BotState.SEARCHING)

            if self.state == BotState.HITTING:
                self.rotate_count = 0
                self.calibrate_count = 0
                self.move_fail_count = 0

                if self.started_hitting_time is None:
                    self.started_hitting_time = time.time()

                self.respawn_if_dead()
                result = self.get_mob_info()

                #print(result)
                if result is None or time.time() - self.started_hitting_time >= 100:
                    self.respawn_if_dead()
                    self.started_hitting_time = None
                    self.put_info_text('Finished -> Collect drop')
                    if self.current_metin_name=="water":
                        self.metin_count_water += 1
                    else:
                        self.metin_count_120 += 1
                    total = int(time.time() - self.started)
                    if int(self.last_metin_time) + 90 < total:
                        self.calibrate_view()
                    self.last_metin_time = total
                    avg= round(total / (self.metin_count_120+self.metin_count_water), 1)
                    print(f'{self.metin_count_water} - water metins and {self.metin_count_120} - usual metins || {datetime.timedelta(seconds=total)} - {avg}s/Metin')

                    #self.send_telegram_message(f'{self.metin_count} - {datetime.timedelta(seconds=total)} - {avg}s/Metin')
                    self.switch_state(BotState.COLLECTING_DROP)

            if self.state == BotState.COLLECTING_DROP:
                #self.osk_window.pick_up()
                self.switch_state(BotState.RESTART)

            if self.state == BotState.RESTART:
                self.rotate_count = 0
                self.calibrate_count = 0
                self.move_fail_count = 0
                # if (time.time() - self.last_buff) > self.buff_interval:
                #     self.put_info_text('Turning on buffs...')
                #     self.turn_on_buffs()
                #     self.last_buff = time.time()


                #setup for easiest dangeon
                # if self.metin_count == 4:
                #     self.killing_mobs_time = 0
                #     self.default_killing_mobs_time = 55
                #     self.switch_state(BotState.KILLING_MOBS)
                # elif self.metin_count == 5:
                #     self.killing_mobs_time = 0
                #     self.default_killing_mobs_time = 14
                #     self.switch_state(BotState.KILLING_MOBS)
                # else:
                #     self.switch_state(BotState.SEARCHING)
                
                self.change_metin_respawn_or_channel()
                

                self.switch_state(BotState.SEARCHING)


            if self.state == BotState.KILLING_MOBS:
                
                self.osk_window.start_hitting()
                time.sleep(0.1)

                self.osk_window.pull_mobs()
                time.sleep(0.1)

                self.osk_window.pick_up()
                time.sleep(0.5)

                time.sleep(2)

                self.osk_window.pick_up()
                time.sleep(0.5)

                self.osk_window.stop_hitting()
                time.sleep(0.1)
                
                self.killing_mobs_time += 5

                if (time.time() - self.last_buff) > self.buff_interval:
                    self.put_info_text('Turning on buffs...')
                    self.turn_on_buffs()
                    self.last_buff = time.time()

                if self.killing_mobs_time > self.default_killing_mobs_time:
                    self.killing_mobs_time = self.default_killing_mobs_time
                    self.switch_state(BotState.SEARCHING)

            if self.state == BotState.WAITING:
                pass


            if self.state == BotState.ERROR:
                self.rotate_count = 0
                self.calibrate_count = 0
                self.move_fail_count = 0
                self.put_info_text('Went into error mode!')
                #self.send_telegram_message('Went into error mode')
                if True or self.last_error is None or time.time() - self.last_error > 300:
                    self.last_error = time.time()
                    self.put_info_text('Error not persistent! Will restart!')
                    #self.send_telegram_message('Restart')
                    # self.respawn_if_dead()
                    # self.teleport_back()
                    self.osk_window.recall_mount()
                    self.turn_on_buffs()
                    self.calibrate_view()
                    self.switch_state(BotState.SEARCHING)
                else:
                    self.put_info_text('Error persistent!')
                    #self.send_telegram_message('Shutdown')
                    while True:
                        time.sleep(1)
                    self.stop()

            if self.state == BotState.DEBUG:
                #self.set_object_detector_state(True)
                #self.osk_window.rotate_with_mouse()
                time.sleep(0.5)
                self.respawn_if_dead()
                # if self.detection_result is not None:
                #     self.metin_window.mouse_move(*self.detection_result['click_pos'])
                #     time.sleep(0.06)
                #     pos = self.metin_window.get_relative_mouse_pos()
                #     width = 200
                #     height = 150
                #     top_left = self.metin_window.limit_coordinate((int(pos[0] - width / 2), pos[1] - height))
                #     bottom_right = self.metin_window.limit_coordinate((int(pos[0] + width / 2), pos[1]))

                #     self.info_lock.acquire()
                #     mob_title_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
                #     self.info_lock.release()
                    
                #     match_loc, match_val = self.vision.template_match_alpha(mob_title_box, utils.get_metin_needle_path())
                #     if match_loc is not None:
                #         self.put_info_text('Metin found!')
                        # self.turn_on_buffs()
                        # self.metin_window.mouse_click()
                        # self.osk_window.ride_through_units()
                        # self.switch_state(BotState.MOVING)
                
                pass
                #self.metin_window.activate()
                # time.sleep(3)
                # for x in range(1, 9):
                #     self.change_channel(x)
                # # self.rotate_view()
                # time.sleep(3)
                # self.calibrate_view()
                # # while True:
                # #     self.put_info_text(str(self.metin_window.get_relative_mouse_pos()))
                # #     time.sleep(1)
                # self.stop()

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def rotate_or_calibrate(self):
        self.info_lock.acquire()
       
        self.state_lock.release()
    def stop(self):
        self.stopped = True

    def set_object_detector_state(self,state):
        
        self.is_object_detector_enabled = state
        


    def get_object_detector_state(self):
   
        state = self.is_object_detector_enabled
        
        return state

    def detection_info_update(self, screenshot, screenshot_time, result, result_time):
        self.info_lock.acquire()
        self.screenshot = screenshot
        self.screenshot_time = screenshot_time
        self.detection_result = result
        self.detection_time = result_time
        self.info_lock.release()

    def switch_state(self, state):
        self.state_lock.acquire()
        self.state = state
        self.time_entered_state = time.time()
        self.state_lock.release()
        self.put_info_text()

    def get_state(self):
        self.state_lock.acquire()
        state = self.state
        self.state_lock.release()
        return state

    def put_info_text(self, string=''):
        if len(string) > 0:
            self.info_text += datetime.datetime.now().strftime("%H:%M:%S") + ': ' + string + '\n'
        font, scale, thickness = cv.FONT_HERSHEY_SIMPLEX, 0.35, 1
        lines = self.info_text.split('\n')
        text_size, _ = cv.getTextSize(lines[0], font, scale, thickness)
        y0 = 720 - len(lines) * (text_size[1] + 6)

        self.overlay_lock.acquire()
        self.overlay_image = np.zeros((self.metin_window.height, self.metin_window.width, 3), np.uint8)
        self.put_text_multiline(self.overlay_image, self.state.name, 10, 715, scale=0.5, color=(0, 255, 0))
        self.put_text_multiline(self.overlay_image, self.info_text, 10, y0, scale=scale)
        self.overlay_lock.release()

    def get_overlay_image(self):
        self.overlay_lock.acquire()
        overlay_image = self.overlay_image.copy()
        self.overlay_lock.release()
        return overlay_image

    def put_text_multiline(self, image, text, x, y, scale=0.3, color=(0, 200, 0), thickness=1):
        font = font = cv.FONT_HERSHEY_SIMPLEX
        y0 = y
        for i, line in enumerate(text.split('\n')):
            text_size, _ = cv.getTextSize(line, font, scale, thickness)
            line_height = text_size[1] + 6
            y = y0 + i * line_height
            if y > 300:
                cv.putText(image, line, (x, y), font, scale, color, thickness)

    def zoom_out(self, zooming_time=1.0):
        self.osk_window.start_zooming_out()
        time.sleep(zooming_time)
        self.osk_window.stop_zooming_out()

    def calibrate_view(self):
        self.metin_window.activate()
        # Camera option: Near, Perspective all the way to the right
        self.osk_window.start_rotating_up()
        time.sleep(0.8)
        self.osk_window.stop_rotating_up()
        self.osk_window.start_rotating_down()
        time.sleep(0.65)
        self.osk_window.stop_rotating_down()
        time.sleep(0.1)
        self.osk_window.start_zooming_out()
        time.sleep(0.8)
        self.osk_window.stop_zooming_out()
        #self.osk_window.start_zooming_in()
        time.sleep(0.03)
        #self.osk_window.stop_zooming_in()

    def calibrate_view_after_dangeon(self):
        self.metin_window.activate()
        # Camera option: Near, Perspective all the way to the right
        # self.osk_window.start_rotating_up()
        # time.sleep(0.8)
        # self.osk_window.stop_rotating_up()
        # self.osk_window.start_rotating_down()
        # time.sleep(0.75)
        # self.osk_window.stop_rotating_down()
        # self.osk_window.start_zooming_out()
        # time.sleep(0.8)
        # self.osk_window.stop_zooming_out()
        self.osk_window.start_zooming_in()
        time.sleep(0.08)
        self.osk_window.stop_zooming_in()

    def close_window_if_not_working(self):
        total = int(time.time() - self.started)
        if total - int(self.last_metin_time) > 600:
            self.metin_window.find_process_and_kill_window()
            self.last_metin_time = total

    def rotate_view(self):
        # self.osk_window.start_rotating_horizontally()
        # time.sleep(0.5)
        # self.osk_window.stop_rotating_horizontally()

        self.osk_window.rotate_with_mouse()

        #self.osk_window.move_with_camera_rotation()

    def process_metin_info(self, text):
        # Remove certain substrings
        remove = ['\f', '.', '°', '%', '‘', ',']
        for char in remove:
            text = text.replace(char, '')

        # Replace certain substrings
        replace = [('\n', ' '), ('Lw', 'Lv'), ('Lv', 'Lv.')]
        for before, after in replace:
            text = text.replace(before, after)

        # '%' falsely detected as '96'
        p = re.compile('(?<=\d)96')
        m = p.search(text)
        if m:
            span = m.span()
            text = text[:span[0]]

        # Parse the string
        parts = text.split()
        parts = [part for part in parts if len(part) > 0]
        if len(parts) == 0:
            return None
        else:
            health_text = re.sub('[^0-9]', '', parts[-1])
            health = 9999
            if len(health_text) > 0:
                health = int(health_text)
            name = ' '.join(parts[:-1])
            return name, health

    def does_metin_exist_on_current_channel(self):
        self.osk_window.find_metin()
        time.sleep(0.1)
        chat_text = self.get_clicked_place_info((215,683),(812,732))
        possible_chat_texts = ["Na tej mapie nie ma Kamieni Metin do znalezienia.",
                               "Na te} mapie nie ma Kamiani Metin do znalezieria,",
                               "Na tej mapie nie ma Kamieni Metin do znalezienia,",
                               "Na tej mapie nie ma Kamieni Metin"]
        if chat_text is not None:
            metin_exists = True
            for text in possible_chat_texts:
                if text in chat_text:
                    metin_exists = False
            return metin_exists
        return True
        


    def get_mob_info(self):
        top_left = (300, 21)
        bottom_right = (700, 60)

        self.info_lock.acquire()
        mob_info_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        mob_info_box = self.vision.apply_hsv_filter(mob_info_box, hsv_filter=self.mob_info_hsv_filter)
        mob_info_text = pytesseract.image_to_string(mob_info_box)

        return self.process_metin_info(mob_info_text)

    def get_clicked_place_info(self, top_left, bottom_right):
        # top_left = (300, 21)
        # bottom_right = (705, 60)

        self.info_lock.acquire()
        mob_info_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        mob_info_box = self.vision.apply_hsv_filter(mob_info_box, hsv_filter=self.mob_info_hsv_filter)
        mob_info_text = pytesseract.image_to_string(mob_info_box)

        return mob_info_text

    def get_after_dangeon_ui_info(self):
        # top_left = (420, 637)
        # bottom_right = (600, 657)

        top_left = (420, 650)
        bottom_right = (600, 670)

        self.info_lock.acquire()
        mob_info_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        mob_info_box = self.vision.apply_hsv_filter(mob_info_box, hsv_filter=self.mob_info_hsv_filter)
        mob_info_text = pytesseract.image_to_string(mob_info_box)
        return mob_info_text
    
    def check_if_player_is_logged_out(self):
        top_left = (450, 509)
        bottom_right = (560, 549)

        self.info_lock.acquire()
        logged_out_info = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        logged_out_info = self.vision.apply_hsv_filter(logged_out_info, hsv_filter=self.mob_info_hsv_filter)
        logged_out_info = pytesseract.image_to_string(logged_out_info)
        if "ZALOG" in logged_out_info:
            self.set_object_detector_state(False)
            print(logged_out_info)
            self.login_user()
        else:
            return "user is logged in"
        #return logged_out_info

    def login_user(self):
        time.sleep(11)
        self.metin_window.mouse_move(511,405)
        time.sleep(0.3)
        self.metin_window.mouse_click()
        time.sleep(0.5)
        self.metin_window.mouse_move(865,365)
        time.sleep(0.2)
        self.metin_window.mouse_click()
        time.sleep(10)
        self.metin_window.mouse_move(239,616)
        time.sleep(0.07)
        self.metin_window.mouse_click()
        time.sleep(15)
        self.switch_state(BotState.INITIALIZING)
        self.check_if_player_is_logged_out()

    def turn_on_buffs(self):
        # self.metin_window.activate()
        self.last_buff = time.time()
        
        # time.sleep(0.3)
        # self.osk_window.un_mount()
        # time.sleep(0.3)
        # self.osk_window.activate_aura()
        # #time.sleep(2)
        # #self.osk_window.activate_berserk()
        # time.sleep(0.3)
        # self.osk_window.un_mount()
        self.osk_window.heal_yourself()
        self.osk_window.activate_buffs()

    # def send_telegram_message(self, msg):
    #     bot = telegram.Bot(token=bot_token)
    #     bot.sendMessage(chat_id=chat_id, text=msg)

    def teleport_to_next_metin_respawn(self, respawn_number=1):
       
        metin_tp_page = [(338,519),(455,518)]
        if self.current_metin_name == "water":
            metin_tp_page = [(340,551),(446,550)]
            
        coords = [(718,272),(718,302), (718,331), (718, 363), (718, 392), (718, 421), (718,453)]

        self.metin_window.activate()
        self.osk_window.activate_teleports()

        time.sleep(0.1)
        self.metin_window.mouse_move(metin_tp_page[math.floor((self.metin_teleports_passed)/6) % 2][0], metin_tp_page[math.floor((self.metin_teleports_passed)/6) % 2][1])
        time.sleep(0.04)
        self.metin_window.mouse_click()

        time.sleep(0.1)
        self.metin_window.mouse_move(coords[respawn_number-1][0], coords[respawn_number-1][1])
        time.sleep(0.04)
        self.metin_window.mouse_click()
        time.sleep(4)

    def change_channel(self, channel):
        
        self.metin_teleports_passed = 0

        channel_cords = [(896,40), (893,63), (896,84), (900, 102), (910,121), (931,131), (952,136), (973,130)]

        self.metin_window.activate()

        time.sleep(0.1)
        self.metin_window.mouse_move(channel_cords[channel-1][0], channel_cords[channel-1][1])
        time.sleep(0.1)
        self.metin_window.mouse_click()
        time.sleep(9)
        self.osk_window.heal_yourself()

    def change_metin_respawn_or_channel(self):
        
        
        if (self.metin_teleports_passed) % 12 == 11:
            self.current_metin_respawn = 0
            self.current_channel = (self.current_channel % 8) + 1
            self.osk_window.heal_yourself()
            self.change_channel(self.current_channel)
            self.osk_window.heal_yourself()
            self.osk_window.turn_poly_off()
            self.osk_window.turn_poly_on()
            self.current_metin_respawn = (self.current_metin_respawn % 6) + 1
            self.metin_teleports_passed += 1
            
            self.teleport_to_next_metin_respawn(self.current_metin_respawn, )
            self.calibrate_view()
        else:
            self.current_metin_respawn = (self.current_metin_respawn % 6) + 1
            self.metin_teleports_passed += 1
            self.teleport_to_next_metin_respawn(self.current_metin_respawn)

    def teleport_back(self):
        self.metin_window.activate()
        self.osk_window.activate_tp_ring()

        coords = {'lv_40': [(512, 401), (508, 402)],
                  'lv_60': [(509, 463), (515, 497)],
                  'lv_70': [(654, 410), (509, 305), (518, 434)],
                  'lv_90': [(654, 410), (508, 369), (513, 495)]}

        for coord in coords[self.metin]:
            time.sleep(1)
            self.metin_window.mouse_move(coord[0], coord[1])
            time.sleep(0.3)
            self.metin_window.mouse_click()
        time.sleep(2)
        while self.detection_result is None:
            time.sleep(1)
        time.sleep(2)

    def respawn_if_dead(self):
        respawn_text = self.get_clicked_place_info((65,70),(238,88))
        possible_texts = ["Rozpocenij tutaj", "tutaj", "Rozpocenij", "Rozpocznij"]

        if respawn_text is not None:
            respawn = False
            for text in possible_texts:
                if text in respawn_text:
                    respawn = True
            
            if respawn == True:
                time.sleep(10)
                time.sleep(0.2)
                self.metin_window.mouse_move(156,80)
                time.sleep(0.04)
                self.metin_window.mouse_click()
                time.sleep(0.5)
                self.osk_window.heal_yourself()
                time.sleep(0.1)
                self.osk_window.heal_yourself()
                time.sleep(0.2)
                self.osk_window.un_mount()
                time.sleep(0.4)
        # match_loc, match_val = self.vision.template_match_alpha(screenshot, utils.get_respawn_needle_path())
        # if match_loc is not None:
        #     #self.send_telegram_message('Respawn cause dead!')
        #     self.put_info_text('Respawn!')
        #     self.metin_window.mouse_move(match_loc[0], match_loc[1] + 5)
        #     time.sleep(0.5)
        #     self.metin_window.mouse_click()
        #     time.sleep(3)

    


