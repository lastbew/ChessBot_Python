"""train_piece_classifier.py - train the CNN on synthetic squares.

Run me with:

    python train_piece_classifier.py

It builds the synthetic dataset, trains a tiny CNN on the CPU, prints the
validation accuracy each epoch, and saves the weights to
assets/model/piece_classifier.pt
"""
from __future__ import annotations

import time

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from bot.classifier import IMG_SIZE, PieceClassifier, save_model
from bot.dataset import build_dataset

MODEL_PATH = "assets/model/piece_classifier.pt"


def main(samples_per_class: int = 400, epochs: int = 12, batch_size: int = 128) -> None:
    print("Building synthetic dataset (this takes a moment)...")
    X, y = build_dataset(samples_per_class=samples_per_class, size=IMG_SIZE, seed=0)
    print(f"  {len(X)} squares, {len(set(y))} classes")

    # uint8 (N,H,W,C) -> float (N,C,H,W) in 0..1
    Xt = torch.from_numpy(X).float().permute(0, 3, 1, 2) / 255.0
    yt = torch.from_numpy(y)

    # 90% for training, 10% held back to measure accuracy.
    n = len(Xt)
    order = torch.randperm(n)
    split = int(n * 0.9)
    train_idx, val_idx = order[:split], order[split:]
    loader = DataLoader(
        TensorDataset(Xt[train_idx], yt[train_idx]),
        batch_size=batch_size,
        shuffle=True,
    )
    val_X, val_y = Xt[val_idx], yt[val_idx]

    model = PieceClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    start = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * len(xb)

        model.eval()
        with torch.no_grad():
            val_acc = (model(val_X).argmax(1) == val_y).float().mean().item()
        print(
            f"epoch {epoch}/{epochs}  "
            f"loss={running_loss / len(train_idx):.3f}  val_acc={val_acc:.3f}"
        )

    save_model(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}  ({time.time() - start:.1f}s)")


if __name__ == "__main__":
    main()
