"""
CodeBERT Model Training Script
Student: IT22601360

This script fine-tunes CodeBERT on your custom dataset of code snippets
labeled with CS concepts. This demonstrates your research contribution.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
import numpy as np
from tqdm import tqdm
import json
import os
from typing import List, Dict, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from app.services.IT22601360.codebert_model import CodeBERTExtractor
from app.utils.constants import CONCEPT_CATEGORIES


class CodeConceptDataset(Dataset):
    """
    Dataset for code concept classification
    
    Each sample:
    - code: Source code snippet
    - categories: Multi-label binary vector [6]
    - concepts: Multi-label binary vector [50]
    """
    
    def __init__(
        self, 
        data: List[Dict],
        tokenizer,
        category_to_idx: Dict[str, int],
        concept_to_idx: Dict[str, int],
        max_length: int = 512
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.category_to_idx = category_to_idx
        self.concept_to_idx = concept_to_idx
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Tokenize code
        encoding = self.tokenizer(
            item['code'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Create category labels (multi-label)
        category_labels = torch.zeros(len(self.category_to_idx))
        for cat in item['categories']:
            if cat in self.category_to_idx:
                category_labels[self.category_to_idx[cat]] = 1.0
        
        # Create concept labels (multi-label)
        concept_labels = torch.zeros(len(self.concept_to_idx))
        for concept in item['concepts']:
            if concept in self.concept_to_idx:
                concept_labels[self.concept_to_idx[concept]] = 1.0
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'category_labels': category_labels,
            'concept_labels': concept_labels
        }


def load_training_data(data_path: str = "data/training_data.json") -> List[Dict]:
    """
    Load training data from JSON file
    
    Expected format:
    [
        {
            "code": "def binary_search(arr, target): ...",
            "language": "python",
            "categories": ["algorithm", "data_structure"],
            "concepts": ["binary_search", "array", "recursion"],
            "description": "Binary search implementation"
        },
        ...
    ]
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Training data not found at {data_path}. "
            "Please run prepare_dataset.py first."
        )
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Loaded {len(data)} training samples")
    return data


def create_mappings(data: List[Dict]) -> Tuple[Dict, Dict]:
    """Create category and concept to index mappings"""
    
    # Category mapping (fixed from constants)
    category_to_idx = {cat: i for i, cat in enumerate(CONCEPT_CATEGORIES)}
    
    # Concept mapping (from data)
    all_concepts = set()
    for item in data:
        all_concepts.update(item['concepts'])
    
    concept_to_idx = {concept: i for i, concept in enumerate(sorted(all_concepts))}
    
    # Pad to 50 concepts
    while len(concept_to_idx) < 50:
        placeholder = f"placeholder_{len(concept_to_idx)}"
        concept_to_idx[placeholder] = len(concept_to_idx)
    
    print(f"📋 Categories: {len(category_to_idx)}")
    print(f"📋 Concepts: {len(concept_to_idx)}")
    
    return category_to_idx, concept_to_idx


def train_epoch(
    model: CodeBERTExtractor,
    dataloader: DataLoader,
    optimizer,
    scheduler,
    device: str
) -> float:
    """Train for one epoch"""
    
    model.codebert.train()
    model.classifier.train()
    
    total_loss = 0
    criterion = nn.BCELoss()
    
    progress_bar = tqdm(dataloader, desc="Training")
    
    for batch in progress_bar:
        # Move to device
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        category_labels = batch['category_labels'].to(device)
        concept_labels = batch['concept_labels'].to(device)
        
        # Forward pass through CodeBERT
        outputs = model.codebert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        
        # Forward pass through classifier
        category_logits, concept_logits = model.classifier(embeddings)
        
        # Calculate loss
        category_loss = criterion(category_logits, category_labels)
        concept_loss = criterion(concept_logits, concept_labels)
        loss = category_loss + concept_loss
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.classifier.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        progress_bar.set_postfix({'loss': loss.item()})
    
    return total_loss / len(dataloader)


def evaluate(
    model: CodeBERTExtractor,
    dataloader: DataLoader,
    device: str
) -> Dict[str, float]:
    """Evaluate model"""
    
    model.codebert.eval()
    model.classifier.eval()
    
    all_category_preds = []
    all_category_labels = []
    all_concept_preds = []
    all_concept_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            category_labels = batch['category_labels'].to(device)
            concept_labels = batch['concept_labels'].to(device)
            
            # Forward pass
            outputs = model.codebert(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            embeddings = outputs.last_hidden_state[:, 0, :]
            category_logits, concept_logits = model.classifier(embeddings)
            
            # Convert to predictions (threshold = 0.5)
            category_preds = (category_logits > 0.5).float()
            concept_preds = (concept_logits > 0.5).float()
            
            all_category_preds.append(category_preds.cpu())
            all_category_labels.append(category_labels.cpu())
            all_concept_preds.append(concept_preds.cpu())
            all_concept_labels.append(concept_labels.cpu())
    
    # Concatenate
    category_preds = torch.cat(all_category_preds, dim=0).numpy()
    category_labels = torch.cat(all_category_labels, dim=0).numpy()
    concept_preds = torch.cat(all_concept_preds, dim=0).numpy()
    concept_labels = torch.cat(all_concept_labels, dim=0).numpy()
    
    # Calculate metrics
    metrics = {
        'category_f1': f1_score(category_labels, category_preds, average='micro'),
        'category_precision': precision_score(category_labels, category_preds, average='micro', zero_division=0),
        'category_recall': recall_score(category_labels, category_preds, average='micro', zero_division=0),
        'concept_f1': f1_score(concept_labels, concept_preds, average='micro'),
        'concept_precision': precision_score(concept_labels, concept_preds, average='micro', zero_division=0),
        'concept_recall': recall_score(concept_labels, concept_preds, average='micro', zero_division=0),
    }
    
    return metrics


def train_codebert(
    data_path: str = "training/data/training_data.json",
    output_dir: str = "training/model/codebert_finetuned",
    epochs: int = 10,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    test_size: float = 0.2
):
    """
    Main training function
    
    Args:
        data_path: Path to training data JSON
        output_dir: Directory to save model checkpoints
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        test_size: Fraction of data for testing
    """
    
    # Setup
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔧 Using device: {device}")
    
    # Load data
    data = load_training_data(data_path)
    
    # Create mappings
    category_to_idx, concept_to_idx = create_mappings(data)
    
    # Save mappings
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/mappings.json", 'w') as f:
        json.dump({
            'category_to_idx': category_to_idx,
            'concept_to_idx': concept_to_idx
        }, f, indent=2)
    
    # Split data
    train_data, test_data = train_test_split(data, test_size=test_size, random_state=42)
    print(f"📊 Train: {len(train_data)}, Test: {len(test_data)}")
    
    # Initialize model
    model = CodeBERTExtractor(device=device)
    
    # Create datasets
    train_dataset = CodeConceptDataset(
        train_data,
        model.tokenizer,
        category_to_idx,
        concept_to_idx
    )
    test_dataset = CodeConceptDataset(
        test_data,
        model.tokenizer,
        category_to_idx,
        concept_to_idx
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2
    )
    
    # Optimizer and scheduler
    optimizer = AdamW(model.classifier.parameters(), lr=learning_rate)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps  # <-- FIXED
    )

    
    # Training loop
    best_f1 = 0
    
    for epoch in range(epochs):
        print(f"\n{'='*50}")
        print(f"Epoch {epoch + 1}/{epochs}")
        print(f"{'='*50}")
        
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, device)
        print(f"Train Loss: {train_loss:.4f}")
        
        # Evaluate
        metrics = evaluate(model, test_loader, device)
        print(f"\nTest Metrics:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")
        
        # Save best model
        current_f1 = (metrics['category_f1'] + metrics['concept_f1']) / 2
        if current_f1 > best_f1:
            best_f1 = current_f1
            checkpoint_path = f"{output_dir}/best_model.pt"
            model.save_checkpoint(checkpoint_path, epoch, train_loss)
            print(f"💾 Saved new best model (F1: {best_f1:.4f})")
        
        # Save checkpoint every 5 epochs
        if (epoch + 1) % 5 == 0:
            checkpoint_path = f"{output_dir}/checkpoint_epoch_{epoch + 1}.pt"
            model.save_checkpoint(checkpoint_path, epoch, train_loss)
    
    print(f"\n{'='*50}")
    print(f"✅ Training Complete!")
    print(f"Best F1 Score: {best_f1:.4f}")
    print(f"Model saved to: {output_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train CodeBERT model")
    parser.add_argument('--data', type=str, default="training/data/training_data.json")
    parser.add_argument('--output', type=str, default="training/model/codebert_finetuned")
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--lr', type=float, default=2e-5)
    
    args = parser.parse_args()
    
    train_codebert(
        data_path=args.data,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )