import os
import random
import numpy as np
import tensorflow as tf
from tensorflow import keras

# --- Load data ---
# human+activity+recognition+using+smartphones
DATA_PATH = 'UCI HAR Dataset/'

X_train = np.loadtxt(DATA_PATH + 'train/X_train.txt')
y_train = np.loadtxt(DATA_PATH + 'train/y_train.txt', dtype=int) - 1  # 0-indexed

X_test = np.loadtxt(DATA_PATH + 'test/X_test.txt')
y_test = np.loadtxt(DATA_PATH + 'test/y_test.txt', dtype=int) - 1

print(f"X_train shape: {X_train.shape}")
print(f"X_test shape:  {X_test.shape}")
print(f"Classes: {np.unique(y_train)}")

random.seed(0)
np.random.seed(0)
tf.random.set_seed(0)
os.environ['PYTHONHASHSEED'] = '0'

# --- Build model ---
model = keras.Sequential([
    keras.layers.Input(shape=(561,)),
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(6, activation='softmax')
])

model.summary()

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# --- Train ---
history = model.fit(X_train, y_train,
                    epochs=15,
                    batch_size=32,
                    validation_data=(X_test, y_test))

# --- Evaluate ---
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nFinal test accuracy (FP32): {acc:.4f}")

# --- Save ---
model.save('model_fp32.h5')
print("Saved model_fp32.h5")