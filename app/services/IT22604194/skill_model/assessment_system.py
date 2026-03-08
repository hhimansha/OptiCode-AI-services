# coding_skill_assessor/02_assessment_system.py
import pandas as pd
import numpy as np
import joblib
from typing import List, Dict, Any
from research_analysis import ResearchBasedAnalyzer  # Add this import

class CodingSkillAssessor:
    def __init__(self, model_path: str = 'coding_skill_classifier.pkl', 
                 encoder_path: str = 'label_encoder.pkl'):
        print("Loading coding skill assessment system...")
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            self.feature_names = ['foundational_coding', 'problem_solving', 'workflow', 
                                'tools', 'computational', 'confidence', 'average_score']
            self.quiz_structure = self._define_quiz_structure()
            self.research_analyzer = ResearchBasedAnalyzer()  # Add research analyzer
            print("Assessment system loaded successfully!")
        except FileNotFoundError as e:
            print(f"Error loading files: {e}")
            print("Please run train_model.py first to create the model files")
            raise
    
    def _define_quiz_structure(self) -> Dict[str, List[int]]:
        return {
            'foundational_coding': list(range(0, 5)),
            'problem_solving': list(range(5, 10)),
            'workflow': list(range(10, 15)),
            'tools': list(range(15, 20)),
            'computational': list(range(20, 25)),
            'confidence': list(range(25, 30))
        }
    
    def answer_to_score(self, answer_index: int) -> int:
        return answer_index + 1
    
    def process_quiz_responses(self, quiz_answers: List[int]) -> Dict[str, float]:
        if len(quiz_answers) != 30:
            raise ValueError(f"Expected 30 answers, got {len(quiz_answers)}")
        
        print("Processing quiz responses...")
        
        answer_scores = [self.answer_to_score(ans) for ans in quiz_answers]
        
        category_scores = {}
        for category, question_indices in self.quiz_structure.items():
            category_total = sum(answer_scores[i] for i in question_indices)
            category_avg = category_total / len(question_indices)
            category_scores[category] = round(category_avg, 2)
            print(f"  {category}: {category_avg:.2f}")
        
        category_scores['average_score'] = round(sum(category_scores.values()) / 6, 2)
        print(f"  Overall average: {category_scores['average_score']:.2f}")
        
        return category_scores
    
    def predict_skill_level(self, quiz_answers: List[int]) -> Dict[str, Any]:
        print("Making skill level prediction...")
        
        features = self.process_quiz_responses(quiz_answers)
        
        feature_vector = [features[col] for col in self.feature_names]
        feature_df = pd.DataFrame([feature_vector], columns=self.feature_names)
        
        prediction_encoded = self.model.predict(feature_df)[0]
        prediction_proba = self.model.predict_proba(feature_df)[0]
        
        skill_level = self.encoder.inverse_transform([prediction_encoded])[0]
        confidence = round(prediction_proba[prediction_encoded] * 100, 1)
        
        print(f"Prediction: {skill_level} (Confidence: {confidence}%)")
        
        # Generate research-based analysis
        research_analysis = self._generate_research_analysis(skill_level, features)
        
        class_probabilities = {}
        for i, class_name in enumerate(self.encoder.classes_):
            class_probabilities[class_name] = f"{prediction_proba[i]*100:.1f}%"
        
        return {
            'skill_level': skill_level,
            'confidence': f"{confidence}%",
            'confidence_raw': confidence,
            'category_scores': features,
            'probabilities': class_probabilities,
            'research_analysis': research_analysis  # Add research analysis
        }
    
    def _generate_research_analysis(self, skill_level: str, category_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate research-based analysis of the assessment results"""
        return {
            'cognitive_patterns': self.research_analyzer.analyze_cognitive_patterns(category_scores),
            'research_insights': self.research_analyzer.generate_research_insights(category_scores),
            'research_recommendations': self.research_analyzer.get_research_based_recommendations(
                skill_level, category_scores
            ),
            'research_principles_applied': list(self.research_analyzer.research_principles.keys())
        }