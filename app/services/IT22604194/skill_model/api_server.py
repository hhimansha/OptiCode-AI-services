# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from assessment_system import CodingSkillAssessor

app = Flask(__name__)
CORS(app)
assessor = CodingSkillAssessor()

@app.route('/')
def home():
    return jsonify({
        "message": "Enhanced Skill Model API is running",
        "version": "2.0",
        "features": ["Machine Learning Assessment", "Research-Based Insights", "Cognitive Pattern Analysis"],
        "research_principles": ["Lister et al. - Code Reading", "Soloway - Mental Models", "Parnas - Modular Design"]
    })

@app.route('/api/predict-skill', methods=['POST'])
def predict_skill():
    try:
        data = request.get_json()
        print("Flask received:", data)
        answers = data.get('quiz_answers', [])
        prediction = assessor.predict_skill_level(answers)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/research-principles', methods=['GET'])
def research_principles():
    """Endpoint to get information about the research principles used"""
    return jsonify({
        "research_principles": {
            "lister": {
                "name": "Lister et al. - Code Reading & Tracing",
                "key_paper": "A Qualitative Study of Novice Programmers (2004)",
                "focus": "Code comprehension through reading rather than writing",
                "application": "Foundational coding skills assessment"
            },
            "soloway": {
                "name": "Soloway - Mental Models & Mechanisms", 
                "key_paper": "Learning to Program = Learning to Construct Mechanisms and Explanations (1986)",
                "focus": "Understanding how programs work at a mechanistic level",
                "application": "Problem-solving and computational thinking assessment"
            },
            "parnas": {
                "name": "Parnas - Modular Design & Information Hiding",
                "key_paper": "On the Criteria To Be Used in Decomposing Systems into Modules (1972)", 
                "focus": "Software design principles and modularity",
                "application": "Workflow and tools assessment"
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)