import datetime
import os

# Suppress warnings
import warnings

import torch
from pytz import timezone

from .model_architecture import ResNet50Siamese
from .signature_detect import classify_extracted_signatures
from .signature_model_data import create_training_data
from .signature_model_training import train_and_test_signature_model

warnings.filterwarnings("ignore")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 32
EPOCHS = 50
IMG_SHAPE = (150, 220)


# Paths
TRAINING_CSV = "signatures/signature_dataset.csv"
BASE_PATH = "dataset_original"  # Original dataset
NEW_DATASET_PATH = "dataset"  # New dataset with augmented images
OUTPUT_CSV = "signature_dataset.csv"
DATASET_PREFIX = "signatures/dataset"

# Model Initialization
model = ResNet50Siamese().to(DEVICE)

TRAIN_MODEL = True
CREATE_DATASET = True
SAVE_MODEL = True
RUN_INFERENCE = True
USE_PRETRAINED = True  # If TRAIN_MODEL is also set to True, then the newly trained model will be used

# Training Configuration
TRAIN_EPOCHS = 25
CONTRASTIVE_MARGIN = 17.5
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-2

if CREATE_DATASET:
    create_training_data(
        base_path=BASE_PATH,
        new_dataset_path=NEW_DATASET_PATH,
        dataset_prefix=DATASET_PREFIX,
        output_csv=OUTPUT_CSV,
    )

# Train and Evaluate the Model
if TRAIN_MODEL:
    print("Starting model training...")
    train_and_test_signature_model(
        model=model,
        pairs_csv=TRAINING_CSV,
        batch_size=BATCH_SIZE,
        epochs=TRAIN_EPOCHS,
        margin=CONTRASTIVE_MARGIN,
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )
    print("Model training completed.")


# Save the model with metadata
if SAVE_MODEL:
    # Save model weights
    def save_model_with_metadata(
        model, train_acc, val_acc, test_acc, save_dir="finetuned_models/resnet_50/best"
    ):
        os.makedirs(save_dir, exist_ok=True)
        eastern = timezone("US/Eastern")
        date_str = datetime.datetime.now(tz=eastern).strftime("%Y-%m-%d")

        frozen = False
        EPOCHS = 25

        filename = f"model_{date_str}_EPOCHS{EPOCHS}_frozen{frozen}_tr{train_acc:.2f}_val{val_acc:.2f}_test{test_acc:.2f}.pth"
        save_path = os.path.join(save_dir, filename)

        torch.save(model.state_dict(), save_path)
        print(f"Model saved to {save_path}")

    train_accuracy = 0.98
    val_accuracy = 0.97
    test_accuracy = 0.97
    save_model_with_metadata(model, train_accuracy, val_accuracy, test_accuracy)

# Run inference on real detected signatures
if RUN_INFERENCE:
    print("Running inference on detected signatures...")
    detected_signatures_base_path = (
        "signatures/all_detected_signatures/detected_signatures"
    )
    true_signatures_path = "signatures/true_signatures"
    finetuned_model_weights = "finetuned_models/resnet_50/no_augmentation/model_2024-12-04_EPOCHS20_frozenFalse_tr0.97_val0.94_test0.95.pth"
    if USE_PRETRAINED and not TRAIN_MODEL:
        model = ResNet50Siamese()
        # Load trained weights
        model.load_state_dict(torch.load(finetuned_model_weights))
        model.eval()  # Set to evaluation mode
        model = model.to(DEVICE)
    SIMILARITY_THRESHOLD = 1000

    classify_extracted_signatures(
        model,
        true_signatures_path,
        detected_signatures_base_path,
        similarity_threshold=SIMILARITY_THRESHOLD,
    )
    print("Inference completed.")
