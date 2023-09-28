from threading import Thread, Lock

import torch
from utils import Vision, SnowManFilter
import time
import numpy as np
import cv2 as cv
from utils import *
import tensorflow as tf
from openvino.runtime import Core

class CaptureAndDetectYolo:

    DEBUG = False

    def __init__(self, metin_window, model_path, hsv_filter):
        self.metin_window = metin_window
        self.vision = Vision()
        self.snowman_hsv_filter = hsv_filter
        #self.classifier = cv.CascadeClassifier(model_path)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(device)
        self.model = torch.hub.load(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\yolov5', 'custom', path=r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\yolo\best.pt', source='local',force_reload=True )
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.model = self.model.to(self.device)

        #self.model = self.model.cuda()
        # self.model = self.model.eval()

        self.screenshot = None
        self.screenshot_time = None

        self.processed_image = None

        self.detection = None
        self.detection_time = None
        self.detection_image = None

        self.detection_tries = 5 

        self.stopped = False
        self.lock = Lock()

        self.is_object_detector_enabled = False
        # self.vision.init_control_gui() # Uncomment do debug HSV filter

    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()

    def run(self):
        while not self.stopped:
            # Take screenshot
            screenshot = self.metin_window.capture()

            start_x = (1024 - 70) // 2
            end_x = start_x + 70
            start_y = (768 - 70) // 2
            end_y = start_y + 70

            # Make the middle region black (set pixel values to [0, 0, 0])
            screenshot[start_y:end_y, start_x:end_x, :] = [0, 0, 0]

            screenshot_time = time.time()
            
            self.lock.acquire()
            self.screenshot = screenshot
            self.screenshot_time = screenshot_time
            self.lock.release()
            # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # self.model.to(device)
            # Preprocess image for object detection
            #processed_img = self.vision.apply_hsv_filter(screenshot, hsv_filter=self.snowman_hsv_filter)
            # processed_img = screenshot
            # processed_img = cv.resize(processed_img, (640,640))
            # results = self.model(processed_img)
            # print(results)
            # results.print()
            # results.show()  # or .show()

            # print(results.xyxy[0])
            #print(results.pandas().xyxy[0])
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
            
           

            detection = None
            detection_time = None
            detection_image = screenshot.copy()
            # Convert your image to the appropriate format if necessary
            if self.is_object_detector_enabled:
                detection_time = time.time()
                # screenshot_gpu = torch.from_numpy(screenshot).to(self.device) #to gpu
                results = self.model(screenshot)
                #results.print()
                results_pandas_df = results.pandas().xyxy[0]
                boxes = results_pandas_df[['xmin', 'ymin', 'xmax', 'ymax']].values
                output_scores = results_pandas_df['confidence'].values

                if len(boxes):
                    detection = {
                        'rectangles': boxes,
                        'scores': output_scores
                    }
                    sorted_indices = np.argsort(detection['scores'])[::-1]
                    sorted_rectangles = detection['rectangles'][sorted_indices]
                    detection['rectangles'] = sorted_rectangles
                    sorted_scores = detection['scores'][sorted_indices]
                    detection['scores'] = sorted_scores
                    # Use to display the best box (the one with the highest score)
                    best_box = detection['rectangles'][0]
                    best_score = detection['scores'][0]

                    for box, score in zip(detection['rectangles'][:6], detection['scores'][:6]):
                        if score > 0.02:
                            self.vision.draw_rectangle_xmin_ymin_xmax_ymax(detection_image,box, (255,0,0))
                            top_left = (int(box[1]), int(box[0]))
                            bottom_right = (int(box[3]), int(box[2]))
                            # Put the probability on the image
                            label = f"{score:.2f}"
                            detection_image = cv.putText(detection_image, label, (top_left[0], top_left[1] - 10),
                                                        cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
                    
                    # Highlighting the best box in a different color (optional)
                    top_left = (int(best_box[0]), int(best_box[1]))
                    bottom_right = (int(best_box[2]), int(best_box[3]))
                    color = (0, 0, 255)  # BGR color for best bounding box
                    detection_image = cv.rectangle(detection_image, top_left, bottom_right, color, 2)

                    # Put the highest probability on the image for the best box
                    label = f"{best_score:.2f}"
                    detection_image = cv.putText(detection_image, label, (top_left[0], top_left[1] - 10),
                                                cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv.LINE_AA)
                    
                    detection['click_pos'] = int((best_box[0] + best_box[2]) / 2), int((best_box[1] + best_box[3])/2)
                    self.vision.draw_marker(detection_image, detection['click_pos'])
                

            # Acquire lock and set new images
            self.lock.acquire()
            self.detection = detection
            self.detection_time = detection_time
            self.detection_image = detection_image
            self.lock.release()
            #time_to_go_to_sleep = 0.04 if not detection else  0.20 * len(detection['scores']) + 0.2
            #time.sleep(time_to_go_to_sleep)

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

    def set_object_detector_state(self,state):
        self.lock.acquire()
        self.is_object_detector_enabled = state
        self.lock.release()

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