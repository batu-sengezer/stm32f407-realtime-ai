import numpy as np
import tensorflow as tf

# --- Load original model ---
model = tf.keras.models.load_model('model_fp32.h5')

# --- Load training data for representative dataset ---
X_train = np.loadtxt('UCI HAR Dataset/train/X_train.txt')

# --- Representative dataset (calibrates INT8 ranges) ---
def representative_dataset():
    for i in range(100):
        sample = X_train[i:i+1].astype(np.float32)
        yield [sample]

# --- Convert to INT8 ---
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.int8
converter.inference_output_type = tf.int8

tflite_model = converter.convert()

# --- Save ---
with open('model_int8.tflite', 'wb') as f:
    f.write(tflite_model)

# --- Compare sizes ---
import os
fp32_size = os.path.getsize('model_fp32.h5')
int8_size  = os.path.getsize('model_int8.tflite')
print(f"FP32 model size: {fp32_size / 1024:.1f} KB")
print(f"INT8 model size: {int8_size  / 1024:.1f} KB")
print(f"Size reduction:  {fp32_size / int8_size:.1f}x smaller")

# --- Evaluate INT8 accuracy ---
X_test = np.loadtxt('UCI HAR Dataset/test/X_test.txt')
y_test = np.loadtxt('UCI HAR Dataset/test/y_test.txt', dtype=int) - 1

interpreter = tf.lite.Interpreter(model_content=tflite_model)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Get quantization scale/zero_point for input
input_scale, input_zero_point = input_details[0]['quantization']

correct = 0
for i in range(len(X_test)):
    sample = X_test[i:i+1].astype(np.float32)
    # Quantize input to INT8
    sample_int8 = (sample / input_scale + input_zero_point).astype(np.int8)
    interpreter.set_tensor(input_details[0]['index'], sample_int8)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    if np.argmax(output) == y_test[i]:
        correct += 1

int8_acc = correct / len(X_test)
# Evaluate FP32 model on test set
fp32_loss, fp32_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"FP32 accuracy: {fp32_acc:.4f}")
print(f"INT8 accuracy: {int8_acc:.4f}")
print(f"Accuracy drop: {(fp32_acc - int8_acc):.4f}")
print("\nSaved model_int8.tflite")