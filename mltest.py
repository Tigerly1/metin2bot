# from ultralytics import NAS

# # Load a COCO-pretrained YOLO-NAS-s model
# model = NAS('yolo_nas_s.pt')

# # Display model information (optional)
# model.info()

# # Validate the model on the COCO8 example dataset
# results = model.val(data='coco8.yaml')

# # Run inference with the YOLO-NAS-s model on the 'bus.jpg' image
# results = model('path/to/bus.jpg')

import torch
print(torch.__version__)