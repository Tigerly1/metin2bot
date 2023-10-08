import os

def normalize_coordinates(image_width, image_height, x, y, width, height):
    # Normalize coordinates to values between 0 and 1
    normalized_x = (float(x) + width / 2) / image_width
    normalized_y = (float(y) + height / 2) / image_height
    normalized_width = width / image_width
    normalized_height = height / image_height
    return normalized_x, normalized_y, normalized_width, normalized_height

def convert_to_yolo(input_file, output_dir, class_id):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 6:
            continue

        image_path, _, x, y, width, height = parts
        x, y, width, height = map(float, [x, y, width, height])

        # Open the image to get its dimensions
        image = cv2.imread(image_path)
        image_height, image_width, _ = image.shape
        # Normalize coordinates
        normalized_x, normalized_y, normalized_width, normalized_height = normalize_coordinates(
            image_width, image_height, x, y, width, height)

        # Write YOLO format annotation to a text file
        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(image_path))[0] + ".txt")
        with open(output_file, 'w') as out_f:
            out_f.write(f"{class_id} {normalized_x:.6f} {normalized_y:.6f} {normalized_width:.6f} {normalized_height:.6f}")

if __name__ == "__main__":
    import cv2

    input_file = "pos.txt"  # Replace with the path to your annotations file
    output_dir = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\water_map\metin"  # Replace with the directory where you want to save YOLO annotations
    class_id = 1  # Replace with the appropriate class ID

    os.makedirs(output_dir, exist_ok=True)

    convert_to_yolo(input_file, output_dir, class_id)


