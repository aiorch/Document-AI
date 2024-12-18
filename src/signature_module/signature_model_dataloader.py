import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms


class SignaturePairDataset(Dataset):
    def __init__(self, csv_file, transform=None):
        self.data = pd.read_csv(csv_file, header=None)
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Extract paths and label
        img1_path = self.data.iloc[idx, 0]
        img2_path = self.data.iloc[idx, 1]
        label = torch.tensor(self.data.iloc[idx, 2], dtype=torch.float32)

        # Load images
        img1 = Image.open(img1_path).convert("L")
        img2 = Image.open(img2_path).convert("L")

        # Apply transformations if specified
        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)
        else:
            img1 = torch.tensor(np.array(img1)).unsqueeze(0).float() / 255.0
            img2 = torch.tensor(np.array(img2)).unsqueeze(0).float() / 255.0

        return img1, img2, label


def get_signature_data(pairs_csv, batch_size=32):
    transform = transforms.Compose(
        [
            transforms.Resize((150, 220)),
            transforms.ToTensor(),
        ]
    )

    # Load dataset
    dataset = SignaturePairDataset(pairs_csv, transform=transform)

    # Split into train and validation
    train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=42)
    train_data, val_data = train_test_split(train_data, test_size=0.2, random_state=42)

    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    return train_loader, val_loader, test_loader
