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
    

class MetinFarmBot_45lvl:

    def __init__(self, metin_window, metin_selection):
        self.metin_window = metin_window
        self.metin = metin_selection

        self.osk_window = InterceptionInput()
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
        self.rotate_threshold = 14

        self.started_hitting_time = None
        self.started_moving_time = None
        self.next_metin = None
        self.last_metin_time = time.time()

        self.stopped = False
        self.state_lock = Lock()
        self.info_lock = Lock()
        self.overlay_lock = Lock()

        self.started = time.time()
        self.last_metin_tiome = time.time()
        #@self.send_telegram_message('Started')
        self.metin_count = 0
        self.last_error = None
        self.dangeons_count = 0

        self.current_click = 0
        self.multiple_detection_result = []

        self.current_channel = 7
        self.current_metin_respawn = 1
        self.metin_teleports_passed = 0



        self.buff_interval = 76
        self.default_killing_mobs_time = 52
        self.killing_mobs_time = 0
        self.last_buff = time.time()

        

        pytesseract.pytesseract.tesseract_cmd = utils.get_tesseract_path()

        self.time_entered_state = None
        self.state = None
        self.switch_state(BotState.INITIALIZING)

    def run(self):
        while not self.stopped:

            if self.state == BotState.INITIALIZING:
                self.metin_window.activate()
                self.check_if_player_is_logged_out()
                #self.respawn_if_dead()
                #self.teleport_back()
                self.calibrate_view()
                #self.osk_window.recall_mount()
               

                #self.started = time.time()
                #self.change_metin_respawn_or_channel()
                #self.turn_on_buffs()
                self.switch_state(BotState.SEARCHING)

            if self.state == BotState.SEARCHING:
                # Check if screenshot is recent
                self.check_if_player_is_logged_out()

                if self.screenshot is not None and self.detection_time is not None and \
                        self.detection_time > self.time_entered_state + 0.16:
                    
                    
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
                try:
                    if self.current_click > 0 and len(self.multiple_detection_result) > 0 and self.current_click < len(self.multiple_detection_result):
                        x = self.multiple_detection_result[self.current_click]
                        self.metin_window.mouse_move(*x)
                        
                        time.sleep(0.13)
                    
                    elif self.current_click == 0 and 'click_positions' in self.detection_result and self.current_click < len(self.detection_result['click_positions'][:4]):
                        self.multiple_detection_result = self.detection_result['click_positions'][:4]
                        x = self.detection_result['click_positions'][self.current_click]
                        self.metin_window.mouse_move(*x)
                        
                        time.sleep(0.13)
                except Exception as e:
                    # detection result is not always there
                    # print(e)
                    # print(self.current_click)
                    # print(self.multiple_detection_result)
                    # print(self.detection_result)
                    pass

                    
                pos = self.metin_window.get_relative_mouse_pos()
                width = 200
                height = 150
                top_left = self.metin_window.limit_coordinate((int(pos[0] - width / 2), pos[1] - height))
                bottom_right = self.metin_window.limit_coordinate((int(pos[0] + width / 2), pos[1]))
                
                self.info_lock.acquire()
                mob_title_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
                self.info_lock.release()
                match_loc = ""
                try:
                    match_loc, match_val = self.vision.template_match_alpha(mob_title_box, utils.get_metin_needle_path())
                except Exception as e:
                    # print(e)
                    pass
                self.metin_window.mouse_right_click()
                time.sleep(0.2)
                print(self.get_clicked_place_info())


                if match_loc is not None:
                    self.metin_window.mouse_click()
                    self.multiple_detection_result = []
                    self.current_click = 0
                    self.put_info_text('Metin found!')
                    self.turn_on_buffs()
                    self.osk_window.ride_through_units()
                    self.switch_state(BotState.MOVING)

                else:
                    # if self.metin_count == 5:
                    #     #self.osk_window
                    #     # if self.rotate_count % 5 == 0:
                    #     #     self.calibrate_view_after_dangeon()
                        
                    #     match_loc, match_val = self.vision.template_match_alpha(mob_title_box, utils.get_dangeon_25lvl_end_needle_path(), max_match_val=100000)
                    #     if match_loc is not None:
                    #         self.put_info_text('end of the dangeon found!')
                    #         self.metin_window.mouse_click()
                    #         time.sleep(0.15)
                    #         print(self.get_after_dangeon_ui_info())
                    #         if "Rozpoc" in self.get_after_dangeon_ui_info():
                    #             self.metin_window.mouse_move(510,663)
                    #             time.sleep(0.05)
                    #             self.metin_window.mouse_click()
                    #             time.sleep(6)
                    #             self.metin_count = 0
                    #             self.dangeons_count += 1
                    #             self.put_info_text(f'{str(self.dangeons_count)} dangeons made')
                    #             print(str(self.dangeons_count) + ' dangeons were made')
                    #             self.calibrate_view
                    #             self.switch_state(BotState.INITIALIZING)
                    try:
                        if self.current_click > 0 and len(self.multiple_detection_result) > 0 and self.current_click < len(self.multiple_detection_result) - 1:
                            self.current_click += 1
                            self.switch_state(BotState.CHECKING_MATCH)
                        elif self.current_click == 0 and 'click_positions' in self.detection_result and self.current_click < len(self.detection_result['click_positions'][:4]) - 1:
                            self.current_click += 1
                            self.switch_state(BotState.CHECKING_MATCH)
                        else:
                            self.multiple_detection_result = []
                            self.current_click = 0
                            self.put_info_text('No metin found -> rotate and search again!')
                            self.rotate_view()
                            self.rotate_count += 1
                            if self.rotate_count > self.rotate_threshold:
                                
                                if self.calibrate_count >= self.calibrate_threshold:
                                    self.rotate_count = 0
                                    self.change_metin_respawn_or_channel()
                                else:
                                    self.put_info_text(f'Rotated {self.rotate_count} times -> Recalibrate!')
                                    self.calibrate_count += 1
                                    self.rotate_count = 0
                                    self.calibrate_view()
                                    self.time_entered_state = time.time()
                            self.switch_state(BotState.SEARCHING)
                    except Exception as e:
                        self.multiple_detection_result = []
                        self.current_click = 0
                        self.put_info_text('No metin found -> rotate and search again!')
                        self.rotate_view()
                        self.rotate_count += 1
                        self.switch_state(BotState.SEARCHING)
                        # detection result is not always there
                        # print(e)
                        # print(self.current_click)
                        # print(self.multiple_detection_result)
                        # print(self.detection_result)
                        # self.multiple_detection_result = []
                        # self.current_click = 0
                        # self.put_info_text('No metin found -> rotate and search again!')
                        # self.switch_state(BotState.SEARCHING)
                        pass


            if self.state == BotState.MOVING:
                if self.started_moving_time is None:
                    self.started_moving_time = time.time()

                result = self.get_mob_info()
                #print(result[0])
                if result is not None and result[1] < 100:
                    self.started_moving_time = None
                    self.move_fail_count = 0
                    self.put_info_text(f'Started hitting {result[0]}')
                    self.switch_state(BotState.HITTING)

                elif time.time() - self.started_moving_time >= 5:
                    self.started_moving_time = None
                    self.osk_window.pick_up()
                    self.metin_count += 1
                    self.switch_state(BotState.RESTART)
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

                result = self.get_mob_info()
                #print(result)
                if result is None or time.time() - self.started_hitting_time >= 7:
                    self.started_hitting_time = None
                    self.put_info_text('Finished -> Collect drop')
                    self.metin_count += 1
                    total = int(time.time() - self.started)
                    if int(self.last_metin_time) + 90 < total:
                        self.calibrate_view()
                    self.last_metin_time = total
                    avg = round(total / self.metin_count, 1)
                    print(f'{self.metin_count} - {datetime.timedelta(seconds=total)} - {avg}s/Metin')

                    #self.send_telegram_message(f'{self.metin_count} - {datetime.timedelta(seconds=total)} - {avg}s/Metin')
                    self.switch_state(BotState.COLLECTING_DROP)

            if self.state == BotState.COLLECTING_DROP:
                self.osk_window.pick_up()
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
                if self.detection_result is not None:
                    self.metin_window.mouse_move(*self.detection_result['click_pos'])
                    time.sleep(0.06)
                    pos = self.metin_window.get_relative_mouse_pos()
                    width = 200
                    height = 150
                    top_left = self.metin_window.limit_coordinate((int(pos[0] - width / 2), pos[1] - height))
                    bottom_right = self.metin_window.limit_coordinate((int(pos[0] + width / 2), pos[1]))

                    self.info_lock.acquire()
                    mob_title_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
                    self.info_lock.release()
                    
                    match_loc, match_val = self.vision.template_match_alpha(mob_title_box, utils.get_metin_needle_path())
                    if match_loc is not None:
                        self.put_info_text('Metin found!')
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
        time.sleep(0.75)
        self.osk_window.stop_rotating_down()
        time.sleep(0.1)
        self.osk_window.start_zooming_out()
        time.sleep(1.3)
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

    def rotate_view(self):
        self.osk_window.start_rotating_horizontally()
        time.sleep(0.3)
        self.osk_window.stop_rotating_horizontally()
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

    def get_mob_info(self):
        top_left = (300, 21)
        bottom_right = (700, 60)

        self.info_lock.acquire()
        mob_info_box = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        mob_info_box = self.vision.apply_hsv_filter(mob_info_box, hsv_filter=self.mob_info_hsv_filter)
        mob_info_text = pytesseract.image_to_string(mob_info_box)

        return self.process_metin_info(mob_info_text)

    def get_clicked_place_info(self):
        top_left = (300, 21)
        bottom_right = (700, 60)

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
        top_left = (440, 396)
        bottom_right = (603, 433)

        self.info_lock.acquire()
        logged_out_info = self.vision.extract_section(self.screenshot, top_left, bottom_right)
        self.info_lock.release()

        logged_out_info = self.vision.apply_hsv_filter(logged_out_info, hsv_filter=self.mob_info_hsv_filter)
        logged_out_info = pytesseract.image_to_string(logged_out_info)
        
        if "LOGOWANIE" in logged_out_info:
            print(logged_out_info)
            self.login_user()
        else:
            return "user is logged in"
        #return logged_out_info

    def login_user(self):
        time.sleep(10)
        self.metin_window.mouse_move(508,403)
        time.sleep(0.07)
        self.metin_window.mouse_click()
        time.sleep(0.1)
        self.metin_window.mouse_move(833,465)
        time.sleep(0.07)
        self.metin_window.mouse_click()
        time.sleep(0.1)
        self.metin_window.mouse_move(529,602)
        time.sleep(0.07)
        self.metin_window.mouse_click()
        time.sleep(10)
        self.metin_window.mouse_move(206,489)
        time.sleep(0.07)
        self.metin_window.mouse_click()
        time.sleep(15)
        self.switch_state(BotState.INITIALIZING)
        self.check_if_player_is_logged_out()

    def turn_on_buffs(self):
        self.metin_window.activate()
        self.last_buff = time.time()
        
        time.sleep(0.3)
        self.osk_window.un_mount()
        time.sleep(0.3)
        self.osk_window.activate_aura()
        #time.sleep(2)
        #self.osk_window.activate_berserk()
        time.sleep(0.3)
        self.osk_window.un_mount()
        self.osk_window.activate_buffs()

    # def send_telegram_message(self, msg):
    #     bot = telegram.Bot(token=bot_token)
    #     bot.sendMessage(chat_id=chat_id, text=msg)

    def teleport_to_next_metin_respawn(self, respawn_number=1):
       
        metin_tp_page = (506,587)
        coords = [(445,216),(445,281), (445,346), (445, 411), (445, 476), (445, 541)]

        self.metin_window.activate()
        self.osk_window.activate_teleports()

        time.sleep(0.1)
        self.metin_window.mouse_move(metin_tp_page[0], metin_tp_page[1])
        time.sleep(0.04)
        self.metin_window.mouse_click()

        time.sleep(0.1)
        self.metin_window.mouse_move(coords[respawn_number-1][0], coords[respawn_number-1][1])
        time.sleep(0.04)
        self.metin_window.mouse_click()
        time.sleep(8)

    def change_channel(self, channel):
        channel_cords = [(896,40), (893,63), (896,84), (900, 102), (910,121), (931,131), (952,136), (973,130)]

        self.metin_window.activate()

        time.sleep(0.1)
        self.metin_window.mouse_move(channel_cords[channel-1][0], channel_cords[channel-1][1])
        time.sleep(0.1)
        self.metin_window.mouse_click()
        time.sleep(8)

    def change_metin_respawn_or_channel(self):
       
        if self.current_metin_respawn == 1 and self.current_channel % 2 == 0 \
                    and self.metin_teleports_passed % 5 == 0 and self.metin_teleports_passed > 0:
            self.current_channel = (self.current_channel % 8) + 1
            self.change_channel(self.current_channel)
        elif self.current_metin_respawn == 6 and self.current_channel % 2 == 1 \
              and self.metin_teleports_passed % 5 == 0:
            self.current_channel = (self.current_channel % 8) + 1
            self.change_channel(self.current_channel)
        else:
            if self.metin_teleports_passed % 10 >= 5:
                self.current_metin_respawn = self.current_metin_respawn - 1
                self.metin_teleports_passed += 1
                self.teleport_to_next_metin_respawn(self.current_metin_respawn)
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
        self.info_lock.acquire()
        screenshot = self.screenshot
        self.info_lock.release()

        match_loc, match_val = self.vision.template_match_alpha(screenshot, utils.get_respawn_needle_path())
        if match_loc is not None:
            #self.send_telegram_message('Respawn cause dead!')
            self.put_info_text('Respawn!')
            self.metin_window.mouse_move(match_loc[0], match_loc[1] + 5)
            time.sleep(0.5)
            self.metin_window.mouse_click()
            time.sleep(3)


    


