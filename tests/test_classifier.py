"""Tests for the CNN piece classifier (shape checks + model load)."""
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from bot.classifier import CLASSES, IMG_SIZE, PieceClassifier, to_tensor

MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "model" / "piece_classifier.pt"


def test_forward_pass_output_shape():
    model = PieceClassifier()
    x = torch.randn(2, 3, IMG_SIZE, IMG_SIZE)
    out = model(x)
    assert out.shape == (2, len(CLASSES))


def test_to_tensor_shape_and_range():
    from PIL import Image

    image = Image.new("RGB", (100, 80), (10, 20, 30))
    tensor = to_tensor(image)
    assert tensor.shape == (3, IMG_SIZE, IMG_SIZE)
    assert 0.0 <= float(tensor.min()) <= float(tensor.max()) <= 1.0


def test_saved_model_loads_and_predicts_a_class():
    if not MODEL_PATH.exists():
        pytest.skip("model not trained yet")
    from PIL import Image

    from bot.classifier import classify_crop, load_model

    model = load_model(MODEL_PATH)
    label, confidence = classify_crop(model, Image.new("RGB", (48, 48), (200, 200, 200)))
    assert label in CLASSES
    assert 0.0 <= confidence <= 1.0
