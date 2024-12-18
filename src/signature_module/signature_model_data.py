import os
import random
import shutil
import uuid

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from sklearn.model_selection import train_test_split

# Paths
base_path = "/Users/siyengar/Desktop/dev/Chemical/dataset_original"  # Original dataset
new_dataset_path = (
    "/Users/siyengar/Desktop/dev/Chemical/dataset"  # New dataset with augmented images
)
output_csv = "/Users/siyengar/Desktop/dev/Chemical/notebooks/signature_dataset.csv"
dataset_prefix = "signatures/dataset"

# Ensure the new dataset directory exists
if os.path.exists(new_dataset_path):
    shutil.rmtree(new_dataset_path)
os.makedirs(new_dataset_path, exist_ok=True)


def augment_image(image, save_path):
    """
    Perform random augmentations on an image and save it.

    Args:
        image (np.ndarray): Input image array.
        save_path (str): Path to save the augmented image.

    Returns:
        str: The path where the augmented image was saved.
    """
    pil_img = Image.fromarray(image)
    pil_img = ImageOps.expand(pil_img, border=50, fill="white")

    # Random Brightness and Contrast
    if random.random() < 0.2:
        pil_img = ImageEnhance.Brightness(pil_img).enhance(random.uniform(0.9, 1.1))
    if random.random() < 0.2:
        pil_img = ImageEnhance.Contrast(pil_img).enhance(random.uniform(0.9, 1.1))

    # Random Rotation
    if random.random() < 0.2:
        angle = random.uniform(-10, 10)
        pil_img = pil_img.rotate(angle, fillcolor=255)

    # Random Scaling (Zoom In/Out)
    if random.random() < 0.2:
        scale = random.uniform(0.9, 1.1)
        width, height = pil_img.size
        new_size = (int(width * scale), int(height * scale))
        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
        pil_img = pil_img.resize((width, height))

    # Random Horizontal/Vertical Shift
    if random.random() < 0.2:
        max_shift = 5
        shift_x = random.randint(-max_shift, max_shift)
        shift_y = random.randint(-max_shift, max_shift)
        shifted_img = Image.new("L", pil_img.size, 255)
        shifted_img.paste(pil_img, (shift_x, shift_y))
        pil_img = shifted_img

    # Random Shear
    if random.random() < 0.2:
        shear = random.uniform(-0.1, 0.1)
        shear_matrix = (1, shear, 0, shear, 1, 0)
        pil_img = pil_img.transform(
            pil_img.size, Image.AFFINE, shear_matrix, fillcolor=255
        )

    # Random Blur
    if random.random() < 0.2:
        np_img = np.array(pil_img)
        blurred_img = cv2.GaussianBlur(np_img, (3, 3), 0)
        pil_img = Image.fromarray(blurred_img)

    pil_img.save(save_path)
    return save_path


def copy_dataset(base_path, new_dataset_path):
    """
    Copy the original dataset to the new dataset path.

    Args:
        base_path (str): Path to the original dataset.
        new_dataset_path (str): Path to the new dataset.
    """
    all_folders = [
        os.path.join(base_path, folder)
        for folder in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, folder))
    ]
    for folder in all_folders:
        folder_name = os.path.basename(folder)
        new_folder_path = os.path.join(new_dataset_path, folder_name)
        os.makedirs(new_folder_path, exist_ok=True)
        for file in os.listdir(folder):
            shutil.copy(os.path.join(folder, file), os.path.join(new_folder_path, file))


def generate_pairs(base_path, target_count_per_class):
    """
    Generate positive and negative pairs of images for the dataset.

    Args:
        base_path (str): Path to the dataset.
        target_count_per_class (int): Target number of pairs per class.

    Returns:
        list: List of tuples containing image pairs and their labels.
    """
    pairs = []
    all_folders = [
        os.path.join(base_path, folder)
        for folder in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, folder))
    ]
    folder_images = {folder: os.listdir(folder) for folder in all_folders}

    # Balance the dataset through oversampling and undersampling
    balanced_folder_images = {}
    for folder, images in folder_images.items():
        if len(images) < target_count_per_class:
            augmented_images = images.copy()
            while len(augmented_images) < target_count_per_class:
                img_to_augment = random.choice(images)
                img_path = os.path.join(folder, img_to_augment)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

                unique_suffix = str(uuid.uuid4())[:8]
                augmented_filename = (
                    f"{os.path.splitext(img_to_augment)[0]}_aug_{unique_suffix}.png"
                )
                augmented_path = os.path.join(folder, augmented_filename)
                augment_image(img, augmented_path)
                augmented_images.append(augmented_filename)
            balanced_folder_images[folder] = augmented_images
        elif len(images) > target_count_per_class:
            balanced_folder_images[folder] = random.sample(
                images, target_count_per_class
            )
        else:
            balanced_folder_images[folder] = images

    # Positive Pairs
    for folder, images in balanced_folder_images.items():
        if len(images) < 2:
            continue
        for _ in range(target_count_per_class):
            img1, img2 = random.sample(images, 2)
            pairs.append((os.path.join(folder, img1), os.path.join(folder, img2), 1))

    # Negative Pairs
    all_folders_list = list(balanced_folder_images.keys())
    for _ in range(len(pairs)):
        folder1, folder2 = random.sample(all_folders_list, 2)
        img1 = random.choice(balanced_folder_images[folder1])
        img2 = random.choice(balanced_folder_images[folder2])
        pairs.append((os.path.join(folder1, img1), os.path.join(folder2, img2), 0))

    return pairs


def create_training_data(
    base_path, new_dataset_path, dataset_prefix, output_csv, num_pairs_per_person=50
):
    # Copy original dataset
    copy_dataset(base_path, new_dataset_path)

    # Generate the dataset pairs
    pairs = generate_pairs(new_dataset_path, num_pairs_per_person)

    # Save pairs to CSV
    with open(output_csv, "w") as f:
        for pair in pairs:
            img1_path, img2_path, label = pair
            relative_img1 = os.path.join(
                dataset_prefix, os.path.relpath(img1_path, new_dataset_path)
            )
            relative_img2 = os.path.join(
                dataset_prefix, os.path.relpath(img2_path, new_dataset_path)
            )
            f.write(f"{relative_img1},{relative_img2},{label}\n")

    print(f"Dataset saved to {output_csv}.")
