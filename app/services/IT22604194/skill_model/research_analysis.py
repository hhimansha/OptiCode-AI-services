# research_analysis.py
from typing import Dict, List

class ResearchBasedAnalyzer:
    """Adds research-based insights to quantitative predictions"""
    
    def __init__(self):
        self.research_principles = self._initialize_research_principles()
    
    def _initialize_research_principles(self) -> Dict:
        """Define research principles and their mappings to categories"""
        return {
            'lister': {
                'name': 'Lister et al. - Code Reading & Tracing',
                'categories': ['foundational_coding'],
                'description': 'Focuses on code comprehension through reading rather than writing',
                'low_score_insight': 'Struggles with code tracing and mental execution',
                'low_score_recommendation': 'Practice reading and explaining code before writing',
                'high_score_insight': 'Strong code reading and comprehension skills',
                'high_score_recommendation': 'Leverage reading skills to learn from existing codebases'
            },
            'soloway': {
                'name': 'Soloway - Mental Models & Mechanisms',
                'categories': ['problem_solving', 'computational'],
                'description': 'Emphasizes understanding how programs work at a mechanistic level',
                'low_score_insight': 'Difficulty understanding program mechanisms',
                'low_score_recommendation': 'Focus on how programs work, not just what they do',
                'high_score_insight': 'Excellent understanding of program mechanisms',
                'high_score_recommendation': 'Apply mechanistic thinking to complex problems'
            },
            'parnas': {
                'name': 'Parnas - Modular Design & Information Hiding',
                'categories': ['workflow', 'tools'],
                'description': 'Focuses on software design principles and modularity',
                'low_score_insight': 'Needs improvement in systematic design thinking',
                'low_score_recommendation': 'Study software design patterns and modularity',
                'high_score_insight': 'Strong design and architectural thinking',
                'high_score_recommendation': 'Lead design discussions and mentor others on architecture'
            }
        }
    
    def analyze_cognitive_patterns(self, category_scores: Dict[str, float]) -> List[Dict]:
        """Analyze cognitive patterns based on research principles"""
        patterns = []
        
        # Pattern 1: Code Reader vs Code Writer (Lister)
        foundational = category_scores.get('foundational_coding', 0)
        problem_solving = category_scores.get('problem_solving', 0)
        
        if foundational > problem_solving + 1.0:
            patterns.append({
                'type': 'Cognitive Pattern',
                'pattern': 'Strong Code Reader',
                'description': 'Better at reading and understanding code than writing it from scratch',
                'research_basis': 'Lister et al.',
                'implication': 'May excel in code review and maintenance tasks'
            })
        elif problem_solving > foundational + 1.0:
            patterns.append({
                'type': 'Cognitive Pattern', 
                'pattern': 'Strong Problem Solver',
                'description': 'Better at solving problems than reading complex code',
                'research_basis': 'Soloway',
                'implication': 'May excel in algorithm design and debugging'
            })
        
        # Pattern 2: Designer vs Implementer (Parnas)
        workflow = category_scores.get('workflow', 0)
        if workflow > problem_solving + 0.8:
            patterns.append({
                'type': 'Cognitive Pattern',
                'pattern': 'Design-Oriented Thinker',
                'description': 'Strong in planning and system design',
                'research_basis': 'Parnas',
                'implication': 'May excel in architecture and project planning'
            })
        elif problem_solving > workflow + 0.8:
            patterns.append({
                'type': 'Cognitive Pattern',
                'pattern': 'Implementation-Focused',
                'description': 'Strong in solving immediate problems and debugging',
                'research_basis': 'Soloway',
                'implication': 'May excel in feature implementation and bug fixing'
            })
        
        return patterns
    
    def generate_research_insights(self, category_scores: Dict[str, float]) -> List[Dict]:
        """Generate research-based insights from category scores"""
        insights = []
        
        for principle_key, principle in self.research_principles.items():
            # Calculate average score for principle's categories
            relevant_scores = [category_scores.get(cat, 0) for cat in principle['categories']]
            if relevant_scores:
                avg_score = sum(relevant_scores) / len(relevant_scores)
                
                if avg_score < 3.0:
                    insights.append({
                        'type': 'Research Insight',
                        'principle': principle['name'],
                        'insight': principle['low_score_insight'],
                        'recommendation': principle['low_score_recommendation'],
                        'evidence': f"Average score in {', '.join(principle['categories'])}: {avg_score:.1f}/5.0",
                        'urgency': 'improvement_needed'
                    })
                elif avg_score > 4.0:
                    insights.append({
                        'type': 'Research Insight', 
                        'principle': principle['name'],
                        'insight': principle['high_score_insight'],
                        'recommendation': principle['high_score_recommendation'],
                        'evidence': f"Average score in {', '.join(principle['categories'])}: {avg_score:.1f}/5.0",
                        'urgency': 'strength'
                    })
        
        return insights
    
    def get_research_based_recommendations(self, skill_level: str, category_scores: Dict[str, float]) -> List[str]:
        """Generate specific research-based learning recommendations"""
        recommendations = []
        
        # Level-appropriate research-based recommendations
        if skill_level == 'Beginner':
            recommendations.extend([
                "🎯 Practice code tracing exercises daily (Lister et al.)",
                "🧠 Focus on understanding how programs work, not just what they do (Soloway)",
                "📚 Read and explain existing code before writing new code (Lister et al.)",
                "🔍 Start with simple debugging to build mental models (Soloway)"
            ])
        elif skill_level == 'Intermediate':
            recommendations.extend([
                "🏗️ Study software design patterns and modularity (Parnas)",
                "🔧 Practice systematic debugging approaches (Soloway)",
                "📖 Analyze well-designed codebases to improve reading skills (Lister et al.)",
                "🎨 Work on projects that require planning and design (Parnas)"
            ])
        else:  # Advanced
            recommendations.extend([
                "🌉 Design and document software architectures (Parnas)",
                "🔬 Analyze complex systems to understand their mechanisms (Soloway)",
                "📝 Mentor others in code reading and comprehension (Lister et al.)",
                "💡 Create reusable, well-documented components (Parnas)"
            ])
        
        # Add specific recommendations based on weak areas
        if category_scores.get('foundational_coding', 0) < 3.0:
            recommendations.append("📖 Priority: Daily code reading practice - explain 1 function per day (Lister)")
        
        if category_scores.get('problem_solving', 0) < 3.0:
            recommendations.append("🔧 Priority: Debugging practice - fix 1 bug in existing code daily (Soloway)")
        
        if category_scores.get('workflow', 0) < 3.0:
            recommendations.append("🏗️ Priority: Design exercises - plan before coding (Parnas)")
        
        return recommendations