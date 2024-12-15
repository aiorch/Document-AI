import torch
from sklearn.metrics import accuracy_score
from torch.nn.functional import pairwise_distance

from .model_architecture import ContrastiveLoss
from .signature_model_dataloader import get_signature_data

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_and_test_signature_model(
    model, pairs_csv, batch_size=32, epochs=25, margin=17.5, lr=1e-3, weight_decay=1e-2
):
    """
    Train and evaluate the signature similarity model using contrastive loss.

    Args:
        model (torch.nn.Module): The Siamese model.
        pairs_csv (str): Path to the CSV containing pairs of signature images and labels.
        batch_size (int): Batch size for data loading.
        epochs (int): Number of epochs for training.
        margin (float): Margin for the contrastive loss function.
        lr (float): Learning rate for the optimizer.
        weight_decay (float): Weight decay for the optimizer.

    Returns:
        None
    """
    # Data Loaders
    train_loader, val_loader, test_loader = get_signature_data(
        pairs_csv=pairs_csv, batch_size=batch_size
    )

    # Loss and Optimizer
    criterion = ContrastiveLoss(margin=margin)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    train_accuracies = []
    val_accuracies = []
    positive_distances = []
    negative_distances = []

    print("Starting Training Loop...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        tr_labels = []
        tr_preds = []

        for img1, img2, label in train_loader:
            img1, img2, label = img1.to(DEVICE), img2.to(DEVICE), label.to(DEVICE)

            optimizer.zero_grad()
            embedding1, embedding2 = model(img1, img2)
            loss = criterion(embedding1, embedding2, label)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            distances = pairwise_distance(embedding1, embedding2, p=2)
            preds = (distances < 7.0).float()  # Threshold for similarity
            tr_labels.extend(label.cpu().numpy())
            tr_preds.extend(preds.cpu().numpy())

        tr_accuracy = accuracy_score(tr_labels, tr_preds)
        train_accuracies.append(tr_accuracy)

        model.eval()
        val_loss, all_labels, all_preds = 0.0, [], []
        with torch.no_grad():
            for img1, img2, label in val_loader:
                img1, img2, label = img1.to(DEVICE), img2.to(DEVICE), label.to(DEVICE)
                embedding1, embedding2 = model(img1, img2)
                loss = criterion(embedding1, embedding2, label)
                val_loss += loss.item()

                distances = pairwise_distance(embedding1, embedding2, p=2)
                preds = (distances < 7.0).float()
                all_labels.extend(label.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())

                for i, dist in enumerate(distances.cpu().numpy()):
                    if label[i] == 1:  # Positive pair
                        positive_distances.append(dist)
                    else:  # Negative pair
                        negative_distances.append(dist)

        val_accuracy = accuracy_score(all_labels, all_preds)
        val_accuracies.append(val_accuracy)

        # scheduler.step(val_loss)

        print(
            f"Epoch [{epoch + 1}/{epochs}], Train Loss: {total_loss:.4f}, Train Accuracy: {tr_accuracy:.4f}, Val Loss: {val_loss:.4f}, Val Accuracy: {val_accuracy:.4f}"
        )

    average_train_accuracy = sum(train_accuracies) / len(train_accuracies)
    average_val_accuracy = sum(val_accuracies) / len(val_accuracies)

    print(f"Average Training Accuracy: {average_train_accuracy:.4f}")
    print(f"Average Validation Accuracy: {average_val_accuracy:.4f}")

    # Test the model
    test_labels, test_preds = [], []

    with torch.no_grad():
        for img1, img2, label in test_loader:
            img1, img2, label = img1.to(DEVICE), img2.to(DEVICE), label.to(DEVICE)
            embedding1, embedding2 = model(img1, img2)
            distances = pairwise_distance(embedding1, embedding2, p=2)
            preds = (distances < 8.0).float()
            test_labels.extend(label.cpu().numpy())
            test_preds.extend(preds.cpu().numpy())

    test_accuracy = accuracy_score(test_labels, test_preds)
    print(f"Test Accuracy: {test_accuracy:.4f}")
