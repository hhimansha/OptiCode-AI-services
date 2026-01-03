"""
Multi-Model Refactoring Service
Compares different refactoring approaches
"""

from transformers import pipeline
import time
from typing import Dict, List

class MultiModelService:
    
    def __init__(self):
        # Try to load HuggingFace model
        try:
            print("[MULTI-MODEL] Loading HuggingFace CodeT5...")
            self.hf_model = pipeline(
                "text2text-generation",
                model="Salesforce/codet5-base",
                max_length=512
            )
            print("[MULTI-MODEL] CodeT5 loaded successfully")
        except Exception as e:
            print(f"[MULTI-MODEL] Could not load CodeT5: {e}")
            self.hf_model = None
    
    def refactor_with_all_models(self, code: str, your_model, rule_based_func) -> List[Dict]:
        """Run refactoring with all available models"""
        
        results = []
        
        # 1. Your trained model
        print("[MULTI-MODEL] Running your trained model...")
        result1 = self._run_your_model(code, your_model)
        results.append(result1)
        
        # 2. HuggingFace model
        if self.hf_model:
            print("[MULTI-MODEL] Running HuggingFace CodeT5...")
            result2 = self._run_huggingface(code)
            results.append(result2)
        
        # 3. Rule-based system
        print("[MULTI-MODEL] Running rule-based system...")
        result3 = self._run_rule_based(code, rule_based_func)
        results.append(result3)
        
        return results
    
    def _run_your_model(self, code: str, model_func) -> Dict:
        """Run your trained model"""
        start = time.time()
        
        try:
            refactored = model_func(code)
            processing_time = (time.time() - start) * 1000
            
            return {
                'model_name': 'Your Trained Model',
                'model_id': 'trained',
                'refactored_code': refactored,
                'processing_time': processing_time,
                'success': True,
                'description': 'Custom trained T5 model for Python refactoring'
            }
        except Exception as e:
            return {
                'model_name': 'Your Trained Model',
                'model_id': 'trained',
                'refactored_code': '',
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }
    
    def _run_huggingface(self, code: str) -> Dict:
        """Run HuggingFace CodeT5"""
        start = time.time()
        
        try:
            prompt = f"refactor: {code}"
            result = self.hf_model(prompt, max_length=512, num_return_sequences=1)
            refactored = result[0]['generated_text']
            processing_time = (time.time() - start) * 1000
            
            return {
                'model_name': 'HuggingFace CodeT5',
                'model_id': 'huggingface',
                'refactored_code': refactored,
                'processing_time': processing_time,
                'success': True,
                'description': 'Salesforce CodeT5 - pre-trained code model'
            }
        except Exception as e:
            return {
                'model_name': 'HuggingFace CodeT5',
                'model_id': 'huggingface',
                'refactored_code': '',
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }
    
    def _run_rule_based(self, code: str, rule_func) -> Dict:
        """Run rule-based refactoring"""
        start = time.time()
        
        try:
            refactored = rule_func(code)
            processing_time = (time.time() - start) * 1000
            
            return {
                'model_name': 'Rule-Based System',
                'model_id': 'rules',
                'refactored_code': refactored,
                'processing_time': processing_time,
                'success': True,
                'description': 'Pattern matching and regex-based refactoring'
            }
        except Exception as e:
            return {
                'model_name': 'Rule-Based System',
                'model_id': 'rules',
                'refactored_code': '',
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }