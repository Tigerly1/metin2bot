from threading import Thread, Lock
from utils import Vision, SnowManFilter
import time
import numpy as np
import cv2 as cv
from utils import *
import tensorflow as tf
from openvino.runtime import Core

class CaptureAndDetectMobileNet:

    DEBUG = False

    def __init__(self, metin_window, model_path, hsv_filter):
        self.metin_window = metin_window
        self.vision = Vision()
        self.snowman_hsv_filter = hsv_filter
        #self.classifier = cv.CascadeClassifier(model_path)
        self.model = tf.saved_model.load(model_path)

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
            
           

            detection = None
            detection_time = None
            detection_image = screenshot.copy()
            # Convert your image to the appropriate format if necessary
            if self.is_object_detector_enabled:
                detection_time = time.time()
                input_tensor = tf.convert_to_tensor([processed_img], dtype=tf.uint8)
                detections = self.model(input_tensor)

                # Extract bounding boxes and scores
                output_boxes = detections['detection_boxes'].numpy()[0]  # Assuming batch size is 1
                output_scores = detections['detection_scores'].numpy()[0]
                

                height, width, _ = processed_img.shape

                # fix it so draw rectangle would work
                boxes = output_boxes * [height, width, height, width]  # De-normalize
                
                # # # Parse results and generate image
                # detection_time = time.time()
                # detection = None
                # detection_image = screenshot.copy()

                # if x > 0 and y > 0:
                #     detection = {'click_pos': (int(x), int(y))}
            
                if len(output_boxes):
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
                    top_left = (int(best_box[1]), int(best_box[0]))
                    bottom_right = (int(best_box[3]), int(best_box[2]))
                    color = (0, 0, 255)  # BGR color for best bounding box
                    detection_image = cv.rectangle(detection_image, top_left, bottom_right, color, 2)

                    # Put the highest probability on the image for the best box
                    label = f"{best_score:.2f}"
                    detection_image = cv.putText(detection_image, label, (top_left[0], top_left[1] - 10),
                                                cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv.LINE_AA)
                    
                    detection['click_pos'] = int((best_box[1] + best_box[3]) / 2), int((best_box[0] + best_box[2])/2)
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