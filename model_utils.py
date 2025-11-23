# model_utils.py
import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def create_generators(dataset_dir, img_size=(224,224), batch_size=32):
    train_dir = os.path.join(dataset_dir, 'train')
    val_dir = os.path.join(dataset_dir, 'val')

    train_datagen = ImageDataGenerator(rescale=1./255,
                                       rotation_range=20,
                                       width_shift_range=0.1,
                                       height_shift_range=0.1,
                                       shear_range=0.1,
                                       zoom_range=0.2,
                                       horizontal_flip=True,
                                       fill_mode='nearest')
    val_datagen = ImageDataGenerator(rescale=1./255)

    train_gen = train_datagen.flow_from_directory(train_dir,
                                                  target_size=img_size,
                                                  batch_size=batch_size,
                                                  class_mode='binary')

    val_gen = val_datagen.flow_from_directory(val_dir,
                                              target_size=img_size,
                                              batch_size=batch_size,
                                              class_mode='binary',
                                              shuffle=False)
    return train_gen, val_gen