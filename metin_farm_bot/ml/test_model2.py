import tensorflow as tf
converter = tf.lite.TFLiteConverter.from_saved_model(r'C:\Users\Filip\Desktop\tob2tm\Metin2-Bot-main\metin_farm_bot\ml\data\resnet-50\output\saved_model')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_quant_model = converter.convert()