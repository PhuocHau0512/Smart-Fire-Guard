import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# 1. Config
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
DATA_DIR = 'dataset' # Cấu trúc folder: dataset/fire và dataset/non_fire

# 2. Data Augmentation (Tăng cường dữ liệu)
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    horizontal_flip=True,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode='binary', subset='training')

val_generator = train_datagen.flow_from_directory(
    DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode='binary', subset='validation')

# 3. Build Model (Transfer Learning)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False # Đóng băng các lớp dưới

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(1, activation='sigmoid')(x) # 1 output: Fire (1) or Non-Fire (0)

model = Model(inputs=base_model.input, outputs=predictions)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 4. Train
print("Đang training...")
model.fit(train_generator, epochs=5, validation_data=val_generator)

# 5. Save
model.save('fire_model.h5')
print("Đã lưu model: fire_model.h5")