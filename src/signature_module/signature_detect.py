import os

import matplotlib.pyplot as plt
import numpy as np
import torch
from model_architecture import ResNet50Siamese
from PIL import Image
from skimage import transform
from skimage.io import imread
from skimage.util import img_as_ubyte

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def preprocess_signature(img: np.ndarray) -> np.ndarray:
    """Pre-process a signature image: center, resize, crop, and normalize."""
    resized_img = transform.resize(img, (150, 220), anti_aliasing=True)
    return resized_img


def load_signature(path: str) -> np.ndarray:
    """Loads a grayscale signature image."""
    return img_as_ubyte(imread(path, as_gray=True))


def preprocess_and_load_signature(image_path):
    raw_image = load_signature(image_path)  # Load as grayscale
    processed_image = preprocess_signature(raw_image)  # Normalize and resize
    # Convert to a PyTorch tensor with 1 channel
    processed_image = (
        torch.tensor(processed_image, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    )
    return processed_image


def extract_features_resnet(model, image_path):
    img_tensor = preprocess_and_load_signature(image_path)
    with torch.no_grad():
        features = model.forward_once(img_tensor.to(DEVICE))
    return features.cpu().numpy()


from torch.nn.functional import pairwise_distance


def euclidean_similarity_fn(feature1, feature2):
    # Compute the Euclidean distance
    distance = pairwise_distance(torch.tensor(feature1), torch.tensor(feature2), p=2)
    return distance.item()  # Return as scalar


def classify_extracted_signatures(
    model,
    true_signatures_path,
    detected_signatures_base_path,
    similarity_threshold=1000,
):
    # Load true signature features
    true_signatures = {}
    true_signature_images = {}
    for filename in os.listdir(true_signatures_path):
        if filename.endswith(".png") and not "long" in filename:
            name = filename.rsplit("-", 1)[0]
            img_path = os.path.join(true_signatures_path, filename)
            feature = extract_features_resnet(model, img_path)
            true_signatures[name] = feature
            true_signature_images[name] = img_path

    page_dirs = sorted(
        os.listdir(detected_signatures_base_path),
        key=lambda x: int(x.replace("page", "")),
    )

    names = []

    for page_dir in page_dirs:
        detected_signatures_path = os.path.join(detected_signatures_base_path, page_dir)

        if os.path.isdir(detected_signatures_path):
            print(f"\n{'=' * 50}")
            print(f"Processing signatures for {page_dir}")
            print(f"{'=' * 50}\n")

            results = {}
            detected = False

            for detected_filename in os.listdir(detected_signatures_path):
                if detected_filename.endswith(".png"):
                    detected_img_path = os.path.join(
                        detected_signatures_path, detected_filename
                    )
                    detected_feature = extract_features_resnet(model, detected_img_path)

                    # Compare with each true signature
                    best_match = None
                    min_distance = float("inf")

                    for name, true_feature in true_signatures.items():
                        distance = pairwise_distance(
                            torch.Tensor(detected_feature),
                            torch.Tensor(true_feature),
                            p=2,
                        )[0]
                        # distance = euclidean_similarity_fn(detected_feature, true_feature)
                        if distance < min_distance:
                            min_distance = distance
                            best_match = name
                            names.append(name)

                    # Only accept matches below the threshold
                    if min_distance <= similarity_threshold:
                        results[detected_filename] = (best_match, min_distance)
                        detected = True
                        print(
                            f"Detected signature {detected_filename} best matches with: {best_match} - Distance: {min_distance}"
                        )
                    else:
                        detected = False
                        print(
                            f"Detected signature {detected_filename} did not meet the distance threshold."
                        )

                    if detected:
                        # Visualization: Display detected and matched true signature side by side
                        detected_img = Image.open(detected_img_path).convert("L")
                        true_img = Image.open(
                            true_signature_images[best_match]
                        ).convert("L")

                        plt.figure(figsize=(10, 5))
                        plt.subplot(1, 2, 1)
                        plt.imshow(detected_img, cmap="gray")
                        plt.title(f"Detected: {detected_filename}")
                        plt.axis("off")

                        plt.subplot(1, 2, 2)
                        plt.imshow(true_img, cmap="gray")
                        plt.title(f"Matched: {best_match}\nDistance: {min_distance}")
                        plt.axis("off")

                        plt.show()

            # Output results for the current page
            print(f"\nResults for {page_dir}:")
            for detected_filename, (name, similarity) in results.items():
                print(f"{detected_filename}: {name} - Similarity: {similarity}")
    return names


if __name__ == "__main__":
    detected_signatures_base_path = (
        "signatures/all_detected_signatures/detected_signatures"
    )
    true_signatures_path = "signatures/true_signatures"
    finetuned_model_weights = "finetuned_models/resnet_50/no_augmentation/model_2024-12-04_EPOCHS20_frozenFalse_tr0.97_val0.94_test0.95.pth"
    model = ResNet50Siamese()

    # Load trained weights
    model.load_state_dict(torch.load(finetuned_model_weights))
    model.eval()  # Set to evaluation mode
    model = model.to(DEVICE)
    employee_names = classify_extracted_signatures(
        model, true_signatures_path, detected_signatures_base_path
    )
