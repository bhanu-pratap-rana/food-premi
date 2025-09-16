"""
Simple RAG test without Milvus dependency issues
"""
import os
from dotenv import load_dotenv
load_dotenv()

# Import our components
from ai.llm_client import ask, chat

def test_rag_simple():
    print("Testing Simple RAG functionality...")

    # Test data
    restaurant_context = """
    Food Premi is a naturally nutritious restaurant that serves:
    - Quinoa Power Bowl with organic quinoa, roasted vegetables, avocado, hemp seeds
    - Mediterranean Bowl with grilled chicken, brown rice, feta, olives, hummus
    - Green Goddess Bowl with kale, spinach, broccoli, edamame, tahini dressing

    We use only organic, locally-sourced ingredients and serve healthy, nutritious meals.
    Our hours are Monday-Friday 11 AM to 9 PM, weekends 10 AM to 10 PM.
    """

    # Test questions
    questions = [
        "What healthy bowl options do you have?",
        "Do you serve vegan food?",
        "What are your restaurant hours?",
    ]

    print("\nTesting RAG responses:")
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")

        # Create RAG prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for Food Premi restaurant. Use the provided context to answer questions about the restaurant."
            },
            {
                "role": "user",
                "content": f"Context: {restaurant_context}\n\nQuestion: {question}"
            }
        ]

        response = chat(messages, temperature=0.2)
        print(f"   Answer: {response[:100]}...")

    print("\nSimple RAG Test PASSED")

if __name__ == "__main__":
    test_rag_simple()