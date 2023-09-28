from threading import Thread, Lock
from utils import Vision, SnowManFilter
import time
import numpy as np
import cv2 as cv
from utils import *


class CaptureAndDetect:

    DEBUG = False

    def __init__(self, metin_window, model_path, hsv_filter):
        self.metin_window = metin_window
        self.vision = Vision()
        self.snowman_hsv_filter = hsv_filter
        self.classifier = cv.CascadeClassifier(model_path)

        self.screenshot = None
        self.screenshot_time = None

        self.processed_image = None

        self.detection = None
        self.detection_time = None
        self.detection_image = None

        self.detection_tries = 5 

        self.is_object_detector_enabled = False
        
        self.stopped = False
        self.lock = Lock()
        # self.vision.init_control_gui() # Uncomment do debug HSV filter

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def run(self):
        while not self.stopped:
            # Take screenshot
            screenshot = self.metin_window.capture()
            screenshot_time = time.time()

            self.lock.acquire()
            self.screenshot = screenshot
            self.screenshot_time = screenshot_time
            self.lock.release()

            # Preprocess image for object detection
            #processed_img = self.vision.apply_hsv_filter(screenshot, hsv_filter=self.snowman_hsv_filter)
            processed_img = screenshot
            #self.vision.black_out_area(processed_img, (390, 270), (600, 460))
            # Detect objects
            # image_paths = self.get_image_paths(utils.get_metin_45_path())
            # x = 0
            # y = 0
            # for i in image_paths:
            #     loc = self.vision.template_match(self.screenshot, i)
            #     if len(loc[0]) > 30:
            #          avg_x = sum(loc[1]) / len(loc[1])
            #          avg_y = sum(loc[0]) / len(loc[0])
            #          x, y = avg_x, avg_y
            #          break
            # print(loc)
            # print(x,y)
            

            output = self.classifier.detectMultiScale2(processed_img)

            # # Parse results and generate image
            detection_time = time.time()
            detection = None
            detection_image = screenshot.copy()

            # if x > 0 and y > 0:
            #     detection = {'click_pos': (int(x), int(y))}
            if len(output[0]):
                detection = {'rectangles': output[0], 'scores': output[1]}
                #best = self.find_best_match(detection['rectangles'])
                # Used to determine best match via scores
                # sort recatngles by their scores
                sorted_indices = np.argsort(detection['scores'])[::-1]
                # Sort the rectangles and scores arrays based on the sorted indices
                sorted_rectangles = detection['rectangles'][sorted_indices]
                detection['sorted_rectangles'] = sorted_rectangles
                sorted_scores = detection['scores'][sorted_indices]

                sorted_data = {'rectangles': sorted_rectangles, 'scores': sorted_scores}
                best = detection['rectangles'][np.argmax(detection['scores'])]
                
                detection_tries = 0
                
                detection['click_positions'] = []
                if self.detection_tries > 1 and detection_tries<len(sorted_rectangles):
                    best = sorted_data['rectangles'][detection_tries]
                    
                    for x in sorted_data['rectangles']:
                        detection['click_positions'].append((int(x[0] + x[2] / 2), int(x[1] + 0.66 * x[3])))
                detection['best_rectangle'] = best
                detection['click_pos'] = int(best[0] + best[2] / 2), int(best[1] + 0.66 * best[3])
                self.vision.draw_rectangles(detection_image, detection['rectangles'])
                self.vision.draw_rectangles(detection_image, [detection['best_rectangle']],
                                            bgr_color=(0, 0, 255))
                self.vision.draw_marker(detection_image, detection['click_pos'])
                

            # Acquire lock and set new images
            self.lock.acquire()
            self.detection = detection
            self.detection_time = detection_time
            self.detection_image = detection_image
            self.lock.release()
            time_to_go_to_sleep = 0.04 if not detection else  0.20 * len(detection['click_positions']) + 0.2
            time.sleep(time_to_go_to_sleep)

            if self.DEBUG:
                time.sleep(1)
    def try_x_matches_before_screenshot(self):
        self.lock.acquire()
        screenshot = None if self.screenshot is None else self.screenshot.copy()
        screenshot_time = self.screenshot_time
        detection = None if self.detection is None else self.detection.copy()
        detection_time = self.detection_time
        detection_image = None if self.detection_image is None \
            else self.detection_image.copy()
        self.lock.release()
        return screenshot, screenshot_time, detection, detection_time, detection_image


    def stop(self):
        self.stopped = True

    def get_info(self):
        self.lock.acquire()
        screenshot = None if self.screenshot is None else self.screenshot.copy()
        screenshot_time = self.screenshot_time
        detection = None if self.detection is None else self.detection.copy()
        detection_time = self.detection_time
        detection_image = None if self.detection_image is None \
            else self.detection_image.copy()
        self.lock.release()
        return screenshot, screenshot_time, detection, detection_time, detection_image

    def find_best_match(self, rectangles):
        ideal_width = 80
        diff = []
        for rectangle in rectangles:
            diff.append(abs(rectangle[2] - ideal_width))
        return rectangles[np.argmin(diff)]
        # best = rectangles[np.argmax(rectangles['scores'])]
        # return best

    def get_image_paths(self, directory):
        # List of common image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp']

        # Collect the paths of all image files in the directory
        image_paths = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    full_path = os.path.join(root, file)
                    image_paths.append(full_path)

        return image_paths