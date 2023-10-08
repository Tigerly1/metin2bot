import cv2

# Load the image
image_path = r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\water_map\metin\1696241025.jpg'
image = cv2.imread(image_path)

# Read the YOLO annotation file
annotation_file = r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\water_map\metin\1696241025.txt'

with open(annotation_file, 'r') as f:
    lines = f.readlines()

# Loop through each line in the annotation file
for line in lines:
    line = line.strip().split()  # Split the line into parts
    class_id = int(line[0])      # YOLO class ID
    x_center = float(line[1])    # X-coordinate of the center of the bounding box
    y_center = float(line[2])    # Y-coordinate of the center of the bounding box
    width = float(line[3])       # Width of the bounding box
    height = float(line[4])      # Height of the bounding box

    # Calculate the coordinates of the top-left and bottom-right corners of the bounding box
    x1 = int((x_center - width / 2) * image.shape[1])
    y1 = int((y_center - height / 2) * image.shape[0])
    x2 = int((x_center + width / 2) * image.shape[1])
    y2 = int((y_center + height / 2) * image.shape[0])

    # Draw the bounding box on the image
    color = (0, 255, 0)  # Green color for the bounding box
    thickness = 2       # Thickness of the bounding box
    image = cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # You can also add text to display the class ID if available
    text = f"Class: {class_id}"
    cv2.putText(image, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness=2)

# Display the image with bounding boxes
cv2.imshow('Annotated Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
