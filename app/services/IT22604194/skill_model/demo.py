# coding_skill_assessor/03_demo.py
from typing import Dict
from assessment_system import CodingSkillAssessor

def display_enhanced_results(prediction: Dict):
    print("\n" + "="*70)
    print("ENHANCED CODING SKILL ASSESSMENT RESULTS (Research-Based)")
    print("="*70)
    
    # Original results
    print(f" OVERALL ASSESSMENT:")
    print(f"  Skill Level: {prediction['skill_level']}")
    print(f"  Confidence: {prediction['confidence']}")
    print(f"  Overall Score: {prediction['category_scores']['average_score']}/5.0")
    
    print(f"\n CATEGORY SCORES:")
    for category, score in prediction['category_scores'].items():
        if category != 'average_score':
            stars = "★" * int(score)
            dots = "☆" * (5 - int(score))
            print(f"  {category.replace('_', ' ').title():<20}: {score:.2f} {stars}{dots}")
    
    # Research-based insights
    research = prediction.get('research_analysis', {})
    
    print(f"\n RESEARCH-BASED INSIGHTS:")
    if research.get('research_insights'):
        for insight in research['research_insights']:
            urgency_icon = " " if insight['urgency'] == 'improvement_needed' else ""
            print(f"  {urgency_icon} {insight['principle']}")
            print(f"     Insight: {insight['insight']}")
            print(f"     Evidence: {insight['evidence']}")
            print(f"     Recommendation: {insight['recommendation']}")
    else:
        print("  No specific research insights identified")
    
    print(f"\n COGNITIVE PATTERNS:")
    if research.get('cognitive_patterns'):
        for pattern in research['cognitive_patterns']:
            print(f"   {pattern['pattern']}")
            print(f"     Description: {pattern['description']}")
            print(f"     Research Basis: {pattern['research_basis']}")
            print(f"     Implication: {pattern['implication']}")
    else:
        print("  No distinct cognitive patterns identified")
    
    print(f"\n RESEARCH-BASED RECOMMENDATIONS:")
    if research.get('research_recommendations'):
        for i, rec in enumerate(research['research_recommendations'], 1):
            print(f"  {i}. {rec}")
    else:
        print("  No specific recommendations available")
    
    print(f"\n RESEARCH PRINCIPLES APPLIED:")
    if research.get('research_principles_applied'):
        principles = research['research_principles_applied']
        print(f"  • Lister et al. - Code Reading & Comprehension")
        print(f"  • Soloway - Mental Models & Program Mechanisms") 
        print(f"  • Parnas - Modular Design & Information Hiding")
    
    print(f"\n PROBABILITY DISTRIBUTION:")
    for level in ['Beginner', 'Intermediate', 'Advanced']:
        if level in prediction['probabilities']:
            print(f"  {level:<12}: {prediction['probabilities'][level]}")
    
    print("="*70)

def run_enhanced_demo():
    print("ENHANCED CODING SKILL ASSESSMENT SYSTEM DEMO")
    print("Now with Research-Based Insights!")
    print("=" * 60)
    
    try:
        assessor = CodingSkillAssessor()
        print(" Enhanced assessor initialized successfully!")
    except Exception as e:
        print(f" Failed to initialize assessor: {e}")
        return
    
    # Test profiles with different skill patterns
    student_profiles = {
        "Strong Code Reader": 
            [4, 4, 4, 3, 4,   # High foundational_coding
             2, 2, 3, 2, 2,   # Medium problem_solving  
             3, 3, 2, 3, 3,   # Medium workflow
             3, 3, 3, 3, 3,   # Medium tools
             2, 2, 3, 2, 2,   # Medium computational
             4, 4, 3, 4, 4],  # High confidence
        
        "Strong Problem Solver":
            [2, 2, 3, 2, 2,   # Medium foundational_coding
             4, 4, 4, 4, 4,   # High problem_solving
             3, 3, 3, 3, 3,   # Medium workflow
             3, 3, 3, 3, 3,   # Medium tools
             4, 4, 4, 4, 4,   # High computational
             4, 4, 4, 4, 4],  # High confidence
        
        "Design-Oriented Thinker":
            [3, 3, 3, 3, 3,   # Medium foundational_coding
             3, 3, 3, 3, 3,   # Medium problem_solving
             4, 4, 4, 4, 4,   # High workflow
             4, 4, 4, 4, 4,   # High tools
             3, 3, 3, 3, 3,   # Medium computational
             4, 4, 4, 4, 4]   # High confidence
    }
    
    for profile_name, quiz_answers in student_profiles.items():
        print(f"\n{'='*60}")
        print(f" TESTING: {profile_name}")
        print(f"{'='*60}")
        
        try:
            prediction = assessor.predict_skill_level(quiz_answers)
            display_enhanced_results(prediction)
            
        except Exception as e:
            print(f" Error processing {profile_name}: {e}")
            continue
    
    print("\n Enhanced demo completed successfully!")

if __name__ == "__main__":
    run_enhanced_demo()