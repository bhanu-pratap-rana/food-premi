"""
Test Flask app to demonstrate AI functionality
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()

from ai.llm_client import chat

app = Flask(__name__)
CORS(app)

# In-memory knowledge base for testing
RESTAURANT_KNOWLEDGE = {
    "menu": """
    Food Premi Menu:

    HEALTHY POWER BOWLS:
    - Quinoa Power Bowl ($12.99) - Organic quinoa, roasted sweet potato, steamed broccoli, chickpeas, avocado, hemp seeds, tahini dressing
    - Mediterranean Bowl ($13.99) - Brown rice, grilled organic chicken, cucumber, cherry tomatoes, feta, olives, hummus
    - Green Goddess Bowl ($11.99) - Kale, spinach, broccoli, edamame, avocado, pumpkin seeds, green goddess dressing

    ORGANIC FRESH SALADS:
    - Farm Fresh Garden Salad ($9.99) - Mixed organic greens, cherry tomatoes, carrots, bell peppers, olive oil vinaigrette
    - Protein Power Salad ($15.99) - Baby spinach, wild salmon, quinoa, walnuts, goat cheese, lemon herb dressing
    - Detox Rainbow Salad ($10.99) - Arugula, shredded beets, carrots, purple cabbage, ginger turmeric dressing

    WHOLESOME MAIN DISHES:
    - Grass-Fed Beef & Roasted Vegetables ($22.99) - 6oz grass-fed beef, roasted vegetables, herb-roasted sweet potatoes
    - Wild-Caught Salmon with Quinoa ($19.99) - Pan-seared salmon, tri-color quinoa, steamed asparagus, lemon dill sauce
    - Free-Range Chicken & Sweet Potato ($17.99) - Herb-marinated chicken, mashed sweet potato, sautéed green beans
    - Plant-Based Buddha Bowl ($14.99) - Lentil-mushroom patty, brown rice, roasted vegetables, tahini sauce
    """,

    "info": """
    Food Premi Restaurant Information:

    HOURS:
    Monday-Friday: 11:00 AM - 9:00 PM
    Saturday: 10:00 AM - 10:00 PM
    Sunday: 10:00 AM - 8:00 PM

    DIETARY ACCOMMODATIONS:
    - Vegan options available (Green Goddess Bowl, Plant-Based Buddha Bowl)
    - Gluten-free options available (most bowls and salads)
    - Organic, locally-sourced ingredients
    - High-protein options (Mediterranean Bowl, Protein Power Salad)
    - Keto-friendly options available

    SERVICES:
    - Dine-in service
    - Takeout and delivery
    - Catering for events
    - Meal prep services
    - Nutritional consultations

    PHILOSOPHY:
    We believe in naturally nutritious food using only organic, locally-sourced ingredients.
    All dishes are prepared fresh daily with minimal processing to preserve nutritional value.
    """
}

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '')

        if not question:
            return jsonify({'success': False, 'error': 'No question provided'})

        # Create context from knowledge base
        context = RESTAURANT_KNOWLEDGE['menu'] + "\n\n" + RESTAURANT_KNOWLEDGE['info']

        # Create RAG prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for Food Premi, a naturally nutritious restaurant. Use the provided context to answer questions about our menu, hours, services, and food philosophy. Be friendly, knowledgeable, and focus on health and nutrition."
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nCustomer Question: {question}"
            }
        ]

        # Get response from LLM
        response = chat(messages, temperature=0.2)

        return jsonify({
            'success': True,
            'answer': response,
            'sources': [{'source': 'restaurant_knowledge', 'type': 'menu_info'}],
            'confidence_score': 0.9
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify({
        'success': True,
        'menu': RESTAURANT_KNOWLEDGE['menu']
    })

@app.route('/api/info', methods=['GET'])
def get_info():
    return jsonify({
        'success': True,
        'info': RESTAURANT_KNOWLEDGE['info']
    })

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'success': True,
        'message': 'Food Premi AI API is working!',
        'components': {
            'llm_client': 'OK',
            'knowledge_base': 'OK',
            'api_endpoints': 'OK'
        }
    })

if __name__ == '__main__':
    print("Starting Food Premi Test Server...")
    print("LLM Model:", os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile'))
    print("Available endpoints:")
    print("- GET  /api/test")
    print("- POST /api/ask")
    print("- GET  /api/menu")
    print("- GET  /api/info")
    app.run(debug=True, host='127.0.0.1', port=5001)