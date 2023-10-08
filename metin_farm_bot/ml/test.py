# import os
# import tensorflow as tf

# def load_yolo_annotation(image_path, img_size=(224, 224)):
#     # Load image
#     img = tf.io.read_file(image_path)
#     img = tf.image.decode_jpeg(img, channels=3)
#     img = tf.image.resize(img, img_size)
    
#     # Load annotations
#     txt_path = tf.strings.regex_replace(image_path, ".jpg", ".txt")
#     bbox = tf.io.read_file(txt_path)
#     bbox = tf.strings.split(bbox, "\n")
#     bbox = tf.strings.split(bbox, " ").to_number()
    
#     # Convert YOLO format to [ymin, xmin, ymax, xmax]
#     class_id, x_center, y_center, width, height = tf.split(bbox, 5, axis=-1)
#     xmin = x_center - (width / 2)
#     xmax = x_center + (width / 2)
#     ymin = y_center - (height / 2)
#     ymax = y_center + (height / 2)
    
#     return img, (class_id, xmin, ymin, xmax, ymax)

# # Create dataset
# img_size = (224, 224)
# data_dir = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\metin120\images"
# image_paths = [os.path.join(data_dir, fname) for fname in os.listdir(data_dir) if fname.endswith('.jpg')]
# dataset = tf.data.Dataset.from_tensor_slices(image_paths)
# dataset = dataset.map(load_yolo_annotation, num_parallel_calls=tf.data.AUTOTUNE)

import tensorflow as tf
import os
import io
from PIL import Image
from object_detection.utils import dataset_util

def create_tf_example(yolo_label_path, img_path, label_map):
    with tf.io.gfile.GFile(img_path, 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)

    width, height = image.size
    filename = img_path.encode('utf8')
    image_format = b'jpg'

    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    with open(yolo_label_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            data = line.strip().split()
            class_id, x_center, y_center, bbox_width, bbox_height = map(float, data)

            # Convert YOLO bbox (center, width, height) to (xmin, ymin, xmax, ymax)
            xmin = (x_center - bbox_width/2) * width
            xmax = (x_center + bbox_width/2) * width
            ymin = (y_center - bbox_height/2) * height
            ymax = (y_center + bbox_height/2) * height

            class_name = label_map[int(class_id)]
            classes_text.append(class_name.encode('utf8'))
            classes.append(int(class_id) + 1)  # Add 1 because label IDs start at 1

            xmins.append(xmin / width)
            xmaxs.append(xmax / width)
            ymins.append(ymin / height)
            ymaxs.append(ymax / height)

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))

    return tf_example

import matplotlib.pyplot as plt

def parse_tf_example(example_proto):
    feature_description = {
        'image/encoded': tf.io.FixedLenFeature([], tf.string),
        'image/filename': tf.io.FixedLenFeature([], tf.string),
        'image/object/bbox/xmin': tf.io.VarLenFeature(tf.float32),
        'image/object/bbox/xmax': tf.io.VarLenFeature(tf.float32),
        'image/object/bbox/ymin': tf.io.VarLenFeature(tf.float32),
        'image/object/bbox/ymax': tf.io.VarLenFeature(tf.float32),
        'image/object/class/text': tf.io.VarLenFeature(tf.string),
    }
    
    parsed_features = tf.io.parse_single_example(example_proto, feature_description)
    
    image = tf.image.decode_jpeg(parsed_features['image/encoded'])
    filename = parsed_features['image/filename']
    xmins = tf.sparse.to_dense(parsed_features['image/object/bbox/xmin'])
    xmaxs = tf.sparse.to_dense(parsed_features['image/object/bbox/xmax'])
    ymins = tf.sparse.to_dense(parsed_features['image/object/bbox/ymin'])
    ymaxs = tf.sparse.to_dense(parsed_features['image/object/bbox/ymax'])
    class_texts = tf.sparse.to_dense(parsed_features['image/object/class/text'], default_value=b"")
    
    return image, filename, xmins, xmaxs, ymins, ymaxs, class_texts

def visualize_tfrecord(tfrecord_path, num_samples=5):
    raw_dataset = tf.data.TFRecordDataset(tfrecord_path)
    
    for raw_record in raw_dataset.take(num_samples):
        image, filename, xmins, xmaxs, ymins, ymaxs, class_texts = parse_tf_example(raw_record)
        image = image.numpy()
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        height, width, _ = image.shape
        for xmin, xmax, ymin, ymax, class_text in zip(xmins, xmaxs, ymins, ymaxs, class_texts):
            plt.plot([xmin * width, xmin * width, xmax * width, xmax * width, xmin * width],
                     [ymin * height, ymax * height, ymax * height, ymin * height, ymin * height], 'r-')
            plt.text(xmin * width, ymin * height, class_text.numpy().decode('utf-8'), color='red')
        plt.title(filename.numpy().decode('utf-8'))
        print(filename.numpy().decode('utf-8'))
        plt.show()

tfrecord_path = r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\train.tfrecord'  # Replace with your path
visualize_tfrecord(tfrecord_path)


def main():
    # Define paths and label map
    data_dir = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\classifier\ervelia\metin120\images"
    output_train_path = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\train.tfrecord"
    output_test_path = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\test.tfrecord"
    output_val_path = r"C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\val.tfrecord"
    label_map = {
        0: 'metin'
    }

    all_images = [f for f in os.listdir(data_dir) if f.endswith('.jpg')]
    total_images = len(all_images)
    train_images = all_images[:int(0.7 * total_images)]  # 70% for training
    test_images = all_images[int(0.7 * total_images):int(0.85 * total_images)]  # 15% for testing
    val_images = all_images[int(0.85 * total_images):]  # 15% for validation

    for dataset_type, dataset_images, output_path in [("train", train_images, output_train_path), 
                                                      ("test", test_images, output_test_path), 
                                                      ("val", val_images, output_val_path)]:
        writer = tf.io.TFRecordWriter(output_path)
        
        for img_name in dataset_images:
            yolo_label_path = os.path.join(data_dir, img_name.replace(".jpg", ".txt"))
            img_path = os.path.join(data_dir, img_name)
            
            tf_example = create_tf_example(yolo_label_path, img_path, label_map)
            writer.write(tf_example.SerializeToString())

        writer.close()
        print(f"TFRecord for {dataset_type} created.")

if __name__ == "__main__":
    
    #main()
    pass
