import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import os
import matplotlib.pyplot as plt

# Constants
IMG_SIZE = 299  # Image resize dimension
MODEL_PATH = "deepfake_detection_model.keras" 

# Load the trained model
try:
    model = tf.keras.models.load_model(MODEL_PATH)  # Attempt to load the model
    print(f"Model loaded from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")  # If loading fails
    model = None    

# Image preprocessing
def preprocess_image(image_path):
    img = load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))         # Load and resize image
    img_array = img_to_array(img) / 255.0               # Convert to array and normalize pixel values
    return np.expand_dims(img_array, axis=0), img        # Add batch dimension and return both

# Prediction function
def predict_image(image_path):
    if not model:
        print("Model not loaded.")  # If model isn't loaded, exit
        return
    
    img_array, img = preprocess_image(image_path)  # Preprocess the image
    pred = model.predict(img_array)[0][0]  # Predict the result
    pred_class = "Real" if pred < 0.5 else "Fake"  # Set class based on prediction

    # Display the image with prediction result
    plt.imshow(img)
    plt.axis('off')
    plt.title(f"Predicted Class:{pred_class}") 
    plt.show()

# Test images in a directory
def test_images_in_directory(test_dir):
    if not os.path.exists(test_dir):
        print(f"Directory not found: {test_dir}")  # If directory doesn't exist
        return
    
    for image_name in os.listdir(test_dir):  # Loop through files in the directory
        image_path = os.path.join(test_dir, image_name)  # Get the full path
        if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):  # Filter out non-image files
            print(f"Predicting: {image_name}")
            predict_image(image_path) 

test_directory = "Test"  # Directory to test images 
test_images_in_directory(test_directory)  # Call the function to test images in the directory