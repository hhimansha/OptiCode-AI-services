"""
CodeBERT Integration for Concept Classification
Student: IT22601360

This module implements a fine-tuned CodeBERT model for concept classification,
combined with the existing Gemini API for detailed explanations.
"""

import torch
import torch.nn as nn
from transformers import RobertaTokenizer, RobertaModel
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import pickle
import os

from app.utils.constants import CONCEPT_CATEGORIES


@dataclass
class CodeBERTOutput:
    """Output from CodeBERT model"""
    predicted_categories: List[str]
    confidence_scores: Dict[str, float]
    embeddings: np.ndarray
    top_concepts: List[Tuple[str, float]]


class ConceptClassifier(nn.Module):
    """
    Fine-tuned classification head on top of CodeBERT
    
    Architecture:
    - CodeBERT base (frozen/partially frozen)
    - Multi-label classification head
    - Concept-specific output layer
    """
    
    def __init__(
        self, 
        num_categories: int = 6,
        num_concepts: int = 50,
        hidden_dim: int = 256,
        dropout: float = 0.3
    ):
        super(ConceptClassifier, self).__init__()
        
        # CodeBERT embedding dimension
        self.codebert_dim = 768
        
        # Multi-head classification
        self.category_classifier = nn.Sequential(
            nn.Linear(self.codebert_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_categories),
            nn.Sigmoid()  # Multi-label
        )
        
        # Concept-specific classifier
        self.concept_classifier = nn.Sequential(
            nn.Linear(self.codebert_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_concepts),
            nn.Sigmoid()
        )
        
    def forward(self, codebert_embeddings):
        """
        Forward pass
        
        Args:
            codebert_embeddings: [batch_size, 768] from CodeBERT
            
        Returns:
            category_logits, concept_logits
        """
        category_logits = self.category_classifier(codebert_embeddings)
        concept_logits = self.concept_classifier(codebert_embeddings)
        
        return category_logits, concept_logits


class CodeBERTExtractor:
    """
    CodeBERT-based concept extractor
    
    This is YOUR custom trained model that demonstrates research contribution.
    It works alongside Gemini for a hybrid approach.
    """
    
    def __init__(
        self, 
        model_path: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize CodeBERT extractor
        
        Args:
            model_path: Path to fine-tuned model checkpoint
            device: 'cuda' or 'cpu'
        """
        self.device = device
        
        # Load CodeBERT tokenizer and base model
        print("Loading CodeBERT base model...")
        self.tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
        self.codebert = RobertaModel.from_pretrained("microsoft/codebert-base")
        self.codebert.to(self.device)
        self.codebert.eval()  # Inference mode
        
        # Load concept mappings
        self.category_names = CONCEPT_CATEGORIES
        self.concept_names = self._load_concept_names()
        
        # Initialize classification head
        self.classifier = ConceptClassifier(
            num_categories=len(self.category_names),
            num_concepts=len(self.concept_names)
        )
        self.classifier.to(self.device)
        
        # Load fine-tuned weights if available
        if model_path and os.path.exists(model_path):
            print(f"Loading fine-tuned model from {model_path}")
            self._load_checkpoint(model_path)
        else:
            print("⚠️ No fine-tuned model found. Using randomly initialized classifier.")
            print("   For production, train the model using train_codebert.py")
        
        self.classifier.eval()
    
    def extract_embeddings(self, code: str, max_length: int = 512) -> torch.Tensor:
        """
        Extract CodeBERT embeddings from code
        
        Args:
            code: Source code string
            max_length: Maximum sequence length
            
        Returns:
            Embeddings tensor [768]
        """
        # Tokenize
        inputs = self.tokenizer(
            code,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.codebert(**inputs)
            # Use [CLS] token embedding
            embeddings = outputs.last_hidden_state[:, 0, :]
        
        return embeddings.squeeze(0)  # [768]
    
    def predict_concepts(self, code: str) -> CodeBERTOutput:
        """
        Predict concepts from code using fine-tuned model
        
        Args:
            code: Source code string
            
        Returns:
            CodeBERTOutput with predictions
        """
        # Get embeddings
        embeddings = self.extract_embeddings(code)
        
        # Run through classifier
        with torch.no_grad():
            category_logits, concept_logits = self.classifier(embeddings.unsqueeze(0))
        
        # Convert to numpy
        category_probs = category_logits.cpu().numpy()[0]
        concept_probs = concept_logits.cpu().numpy()[0]
        embeddings_np = embeddings.cpu().numpy()
        
        # Get predicted categories (threshold = 0.5)
        predicted_categories = [
            self.category_names[i] 
            for i, prob in enumerate(category_probs) 
            if prob > 0.5
        ]
        
        # Get confidence scores
        confidence_scores = {
            self.category_names[i]: float(prob)
            for i, prob in enumerate(category_probs)
        }
        
        # Get top concepts
        top_k = 10
        top_indices = np.argsort(concept_probs)[-top_k:][::-1]
        top_concepts = [
            (self.concept_names[i], float(concept_probs[i]))
            for i in top_indices
            if concept_probs[i] > 0.3  # Threshold
        ]
        
        return CodeBERTOutput(
            predicted_categories=predicted_categories,
            confidence_scores=confidence_scores,
            embeddings=embeddings_np,
            top_concepts=top_concepts
        )
    
    def _load_concept_names(self) -> List[str]:
        """Load concept names from constants"""
        from app.utils.constants import KNOWN_CONCEPTS
        
        concepts = []
        for category, concept_dict in KNOWN_CONCEPTS.items():
            for concept_name in concept_dict.keys():
                if concept_name not in concepts:
                    concepts.append(concept_name)
        
        # Pad to 50 concepts (for model architecture)
        while len(concepts) < 50:
            concepts.append(f"placeholder_{len(concepts)}")
        
        return concepts[:50]
    
    def _load_checkpoint(self, path: str):
        """Load fine-tuned model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.classifier.load_state_dict(checkpoint['model_state_dict'])
        print(f"✅ Loaded checkpoint from epoch {checkpoint.get('epoch', 'unknown')}")
    
    def save_checkpoint(self, path: str, epoch: int, train_loss: float):
        """Save model checkpoint"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.classifier.state_dict(),
            'train_loss': train_loss,
            'category_names': self.category_names,
            'concept_names': self.concept_names
        }, path)
        print(f"💾 Saved checkpoint to {path}")


class HybridExtractor:
    """
    Hybrid extractor combining CodeBERT and Gemini
    
    This demonstrates your research contribution:
    1. CodeBERT for fast, accurate classification
    2. Gemini for detailed explanations and relationships
    3. Fusion strategy for best results
    """
    
    def __init__(
        self, 
        codebert_extractor: CodeBERTExtractor,
        gemini_extractor
    ):
        self.codebert = codebert_extractor
        self.gemini = gemini_extractor
    
    async def extract_hybrid(
        self,
        code: str,
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> Tuple[List["ExtractedConcept"], CodeBERTOutput]:
        """
        Hybrid extraction combining CodeBERT and Gemini
        
        Strategy:
        1. CodeBERT predicts categories and concepts (fast, local)
        2. Gemini provides detailed descriptions and relationships (accurate, context-aware)
        3. Fuse results with confidence-weighted combination
        """
        from app.services.IT22601360.gemini_extractor import ExtractedConcept
        
        # Step 1: Get CodeBERT predictions
        codebert_output = self.codebert.predict_concepts(code)
        
        # Step 2: Enhance pre-detected patterns with CodeBERT predictions
        enhanced_patterns = pre_detected_patterns.copy()
        
        for concept_name, confidence in codebert_output.top_concepts:
            # Map concept to category
            category = self._map_concept_to_category(concept_name)
            if category:
                category_key = f"{category}s"  # Pluralize
                if category_key not in enhanced_patterns:
                    enhanced_patterns[category_key] = []
                if concept_name not in enhanced_patterns[category_key]:
                    enhanced_patterns[category_key].append(concept_name)
        
        # Step 3: Get Gemini's detailed analysis DIRECTLY (not through gemini.extract_concepts)
        gemini_concepts = await self._extract_with_gemini_directly(
            code=code,
            language=language,
            structural_summary=structural_summary,
            pre_detected_patterns=enhanced_patterns
        )
        
        # Step 4: Fusion - Boost confidence for concepts found by both
        fused_concepts = []
        codebert_concept_names = set(c[0].lower() for c in codebert_output.top_concepts)
        
        for concept in gemini_concepts:
            # Check if CodeBERT also found this concept
            concept_normalized = concept.name.lower().replace(' ', '_')
            
            boost = 0.0
            for cb_name, cb_conf in codebert_output.top_concepts:
                if cb_name.lower() in concept_normalized or concept_normalized in cb_name.lower():
                    boost = 0.2 * cb_conf  # Boost based on CodeBERT confidence
                    break
            
            # Create enhanced concept
            enhanced_concept = ExtractedConcept(
                name=concept.name,
                category=concept.category,
                description=f"{concept.description} [CodeBERT confidence: {boost:.2f}]" if boost > 0 else concept.description,
                confidence=min(1.0, concept.confidence + boost),
                evidence=concept.evidence,
                related_concepts=concept.related_concepts,
                code_snippet=concept.code_snippet,
                line_numbers=concept.line_numbers
            )
            fused_concepts.append(enhanced_concept)
        
        # Step 5: Add high-confidence CodeBERT concepts not found by Gemini
        gemini_names = set(c.name.lower() for c in fused_concepts)
        
        for concept_name, confidence in codebert_output.top_concepts:
            if confidence > 0.7 and concept_name.lower() not in gemini_names:
                category = self._map_concept_to_category(concept_name)
                fused_concepts.append(ExtractedConcept(
                    name=concept_name.replace('_', ' ').title(),
                    category=category or "programming_concept",
                    description=f"Detected by CodeBERT model with high confidence",
                    confidence=confidence,
                    evidence="CodeBERT neural network classification",
                    related_concepts=[]
                ))
        
        return fused_concepts, codebert_output
    
    async def _extract_with_gemini_directly(
        self,
        code: str,
        language: str,
        structural_summary: Dict,
        pre_detected_patterns: Dict[str, List[str]]
    ) -> List["ExtractedConcept"]:
        """
        Direct Gemini extraction without recursion
        """
        from app.services.IT22601360.gemini_extractor import ExtractedConcept
        
        prompt = self.gemini._build_extraction_prompt(
            code, 
            language, 
            structural_summary, 
            pre_detected_patterns
        )
        
        try:
            response = self.gemini.client.models.generate_content(
                model=self.gemini.model_name,
                contents=[{"text": prompt}],
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=4096
            )
            
            concepts = self.gemini._parse_response(response.text)
            concepts = self.gemini._merge_with_predetected(concepts, pre_detected_patterns)
            
            # Mark as Gemini-only
            for concept in concepts:
                concept.source = "gemini"
            
            return concepts
            
        except Exception as e:
            print(f"Gemini direct extraction error: {str(e)}")
            return self.gemini._convert_predetected_to_concepts(pre_detected_patterns)
    
    def _map_concept_to_category(self, concept_name: str) -> Optional[str]:
        """Map concept name to category"""
        from app.utils.constants import KNOWN_CONCEPTS
        
        concept_lower = concept_name.lower().replace(' ', '_')
        
        for category, concepts in KNOWN_CONCEPTS.items():
            if concept_lower in concepts:
                # Convert plural to singular
                category_map = {
                    "data_structures": "data_structure",
                    "algorithms": "algorithm",
                    "design_patterns": "design_pattern",
                    "architectures": "architecture",
                    "paradigms": "paradigm",
                    "programming_concepts": "programming_concept"
                }
                return category_map.get(category, "programming_concept")
        
        return None