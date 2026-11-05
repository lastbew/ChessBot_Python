"""classifier.py - the small neural network that reads a single chess square.

The network looks at a small image of one square (48x48 pixels) and decides
what is on it: an empty square, or one of the 12 pieces.

Label order is important - training and prediction must agree:
    0 empty
    1..6  white P,N,B,R,Q,K
    7..12 black P,N,B,R,Q,K
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

IMG_SIZE = 48
CLASSES = [
    "empty",
    "wP", "wN", "wB", "wR", "wQ", "wK",
    "bP", "bN", "bB", "bR", "bQ", "bK",
]


class PieceClassifier(nn.Module):
    """A tiny convolutional neural network (CNN) for 13-way classification."""

    def __init__(self, num_classes: int = len(CLASSES)):
        super().__init__()
        # "features" turns the image into compact feature maps.
        # BatchNorm makes training converge much faster and more reliably.
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),  # squeeze to 1x1 per channel
        )
        # "classifier" turns those features into 13 scores (one per class).
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def to_tensor(image: Image.Image) -> torch.Tensor:
    """Convert a PIL image into a normalized 3 x 48 x 48 float tensor."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    array = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)  # H,W,C -> C,H,W
    return tensor


def save_model(model: nn.Module, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(path))


def load_model(path: str | Path) -> PieceClassifier:
    model = PieceClassifier()
    model.load_state_dict(torch.load(str(path), map_location="cpu"))
    model.eval()
    return model


@torch.no_grad()
def classify_crop(model: PieceClassifier, image: Image.Image) -> tuple[str, float]:
    """Return (label, confidence) for a single square image."""
    batch = to_tensor(image).unsqueeze(0)  # add the batch dimension
    probs = torch.softmax(model(batch), dim=1)[0]
    index = int(torch.argmax(probs))
    return CLASSES[index], float(probs[index])


@torch.no_grad()
def classify_batch(model: PieceClassifier, images: list[Image.Image]) -> list[str]:
    """Return labels for many square images at once (faster than one-by-one)."""
    batch = torch.stack([to_tensor(image) for image in images])
    indices = torch.argmax(model(batch), dim=1).tolist()
    return [CLASSES[index] for index in indices]
