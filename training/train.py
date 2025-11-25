from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import json
import os

DATA_PATH = "training/dataset/clean_dataset.json"
OUTPUT_PATH = "training/model/saved_model"

def load_dataset():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    return [
        InputExample(texts=[item["code"], item["concept"]])
        for item in data
    ]

def train_model():
    print("Loading base model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Preparing dataset...")
    train_examples = load_dataset()
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)

    loss = losses.MultipleNegativesRankingLoss(model)

    print("Training started...")
    model.fit(
        train_objectives=[(train_dataloader, loss)],
        epochs=4,
        output_path=OUTPUT_PATH
    )

    print(f"Training complete. Model saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    train_model()
