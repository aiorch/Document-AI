import torch.nn as nn
from torch import clamp
from torch.nn.functional import pairwise_distance
from torchvision.models import resnet50


class ResNet50Siamese(nn.Module):
    def __init__(self):
        super(ResNet50Siamese, self).__init__()
        # Load pre-trained ResNet50
        self.resnet = resnet50(pretrained=True)

        # Modify the input layer to handle grayscale images (1 channel)
        self.resnet.conv1 = nn.Conv2d(
            1, 64, kernel_size=7, stride=2, padding=3, bias=False
        )

        # Extract up to the average pooling layer
        self.feature_extractor = nn.Sequential(*list(self.resnet.children())[:-1])

        # Add a projection head for embeddings
        self.embedding_dim = 512
        self.fc = nn.Sequential(
            nn.Linear(2048, self.embedding_dim),
            nn.ReLU(),
            nn.BatchNorm1d(self.embedding_dim),
        )

    def forward_once(self, x):
        # Feature extraction
        x = self.feature_extractor(x)
        x = x.view(x.size(0), -1)
        # Project to embedding space
        x = self.fc(x)
        return x

    def forward(self, img1, img2):
        embedding1 = self.forward_once(img1)
        embedding2 = self.forward_once(img2)
        return embedding1, embedding2


class ContrastiveLoss(nn.Module):
    def __init__(self, margin=1.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, embedding1, embedding2, label):
        distances = pairwise_distance(embedding1, embedding2, p=2)
        losses = (
            0.5 * label * distances**2
            + 0.5 * (1 - label) * clamp(self.margin - distances, min=0.0) ** 2
        )
        return losses.mean()
