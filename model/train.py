import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import Xception
import numpy as np
import matplotlib.pyplot as plt

#***********Data Preprocessing****************

# Data augmentation and preprocessing settings for training and validation datasets
train_datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values to range [0, 1]
    rotation_range=20,  # Randomly rotate images by up to 20 degrees
    width_shift_range=0.2,  # Randomly shift images horizontally by 20% of width
    height_shift_range=0.2,  # Randomly shift images vertically by 20% of height
    shear_range=0.2,  # Apply random shearing transformations
    zoom_range=0.2,  
    horizontal_flip=True, 
    fill_mode='nearest',  # Fill in missing pixels with nearest neighbor
    validation_split=0.2  # Reserve 20% of data for validation
)

# Creating a generator for training data
train_generator = train_datagen.flow_from_directory(
    'model/Data/train',  
    target_size=(299, 299), 
    batch_size=32,  # Number of images in each batch
    class_mode='binary',  # Binary classification (e.g., real vs fake)
    subset='training' 
)

# Creating a generator for validation data
validation_generator = train_datagen.flow_from_directory(
    'model/Data/train',  
    target_size=(299, 299), 
    batch_size=32,  # Number of images in each batch
    class_mode='binary',  # Binary classification
    subset='validation'  
)

#************Model Development**************

# Function to build the model
def build_model(dense_units, learning_rate):
    # Load Xception as the base model, without the top layer
    base_model = Xception(
        input_shape=(299, 299, 3),  # Input shape for images
        include_top=False,  # Exclude the fully connected layers
        weights='imagenet'  # Use pre-trained weights from ImageNet
    )
    base_model.trainable = False  # Freeze the base model during training

    # Add custom layers on top of the base model
    model = models.Sequential([
        base_model,  # Pre-trained Xception model
        layers.GlobalAveragePooling2D(),  # Pooling layer to reduce dimensions
        layers.Dense(dense_units, activation='relu'),  # Fully connected layer
        layers.Dense(1, activation='sigmoid')  # Output layer (binary classification)
    ])
    # Compile the model with Adam optimizer and binary cross-entropy loss
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

#***********Hyperparameter Optimization (Random Search)*************

# Function to perform random hyperparameter search
def random_hyperparameter_search(trials, train_gen, val_gen):
    best_val_acc = 0  # Track the best validation accuracy
    best_params = None  # Store the best hyperparameters
    best_model = None  # Store the best model

    for i in range(trials):
        # Randomly sample hyperparameters
        dense_units = np.random.choice([64, 128, 256, 512])  # Number of units in the dense layer
        learning_rate = np.random.choice([0.0001, 0.001, 0.01])  # Learning rate
        print(f"Trial {i + 1}: Dense Units={dense_units}, Learning Rate={learning_rate}")

        # Build and train the model with sampled hyperparameters
        model = build_model(dense_units, learning_rate)
        history = model.fit(
            train_gen,  # Training data
            epochs=3,  # Train for 3 epochs
            validation_data=val_gen,  # Validation data
            verbose=1  # Show training progress
        )

        # Evaluate the model on validation data
        val_loss, val_acc = model.evaluate(val_gen, verbose=0)
        print(f"Validation Accuracy: {val_acc:.4f}")

        # Update the best model if the current one is better
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_params = {'dense_units': dense_units, 'learning_rate': learning_rate}
            best_model = model

    return best_model, best_params, best_val_acc  # Return the best model, parameters, and accuracy

# Perform random search
best_model, best_params, best_val_acc = random_hyperparameter_search(10, train_generator, validation_generator)
print(f"\nBest Parameters: {best_params}")
print(f"Best Validation Accuracy: {best_val_acc:.4f}")

#Train the best model for more epochs
history = best_model.fit(
train_generator,
epochs=20,  # Train for 20 epochs
validation_data=validation_generator
)

# Save the model
best_model.save('deepfake_detection.keras')
print("Model saved as deepfake_detection.keras")


# Visualize Training Results
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Training vs Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Training vs Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()