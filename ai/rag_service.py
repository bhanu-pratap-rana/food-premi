"""
RAG (Retrieval-Augmented Generation) Service
Handles document ingestion and question answering using vector search + LLM
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

from .llm_client import LLMClient, get_llm_client, chat
from .vector_store import MilvusVectorStore, VectorDocument, SearchResult, get_vector_store

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """A chunk of text from a larger document"""
    content: str
    source: str
    chunk_index: int
    metadata: Dict[str, Any]

@dataclass
class IngestionResult:
    """Result of document ingestion"""
    success: bool
    documents_processed: int
    chunks_created: int
    error_message: Optional[str] = None

@dataclass
class RAGResponse:
    """Response from RAG query"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float

class RAGService:
    """RAG service for Food Premi restaurant"""

    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 vector_store: Optional[MilvusVectorStore] = None,
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):

        self.llm_client = llm_client or get_llm_client()
        self.vector_store = vector_store or get_vector_store()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default system prompt for the restaurant
        self.system_prompt = """You are a helpful AI assistant for Food Premi, a restaurant that serves naturally nutritious and organic food.

Your role is to:
- Answer questions about our menu, ingredients, and food preparation
- Provide information about our services, hours, and location
- Help customers with dietary restrictions and recommendations
- Share information about our commitment to organic and healthy eating

Always be friendly, knowledgeable, and focused on health and nutrition. If you don't know something specific, say so honestly and suggest contacting the restaurant directly.

Use the provided context to answer questions accurately. If the context doesn't contain relevant information, rely on general knowledge about healthy eating and restaurants, but make it clear when you're providing general advice vs. restaurant-specific information."""

    def chunk_text(self, text: str, source: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Split text into overlapping chunks"""
        if metadata is None:
            metadata = {}

        chunks = []
        text_length = len(text)

        for i in range(0, text_length, self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]

            # Don't create tiny chunks at the end
            if len(chunk_text) < 50 and i > 0:
                break

            chunk = DocumentChunk(
                content=chunk_text.strip(),
                source=source,
                chunk_index=len(chunks),
                metadata={
                    **metadata,
                    'chunk_size': len(chunk_text),
                    'start_pos': i,
                    'end_pos': min(i + self.chunk_size, text_length)
                }
            )
            chunks.append(chunk)

        return chunks

    def ingest_documents(self, documents: List[Dict[str, Any]]) -> IngestionResult:
        """
        Ingest documents into the vector store

        Args:
            documents: List of dicts with 'content', 'source', and optional 'metadata'
        """
        try:
            start_time = datetime.now()
            all_chunks = []

            for doc_idx, doc in enumerate(documents):
                content = doc.get('content', '')
                source = doc.get('source', f'document_{doc_idx}')
                metadata = doc.get('metadata', {})

                # Add ingestion timestamp
                metadata['ingested_at'] = start_time.isoformat()
                metadata['document_type'] = metadata.get('type', 'general')

                # Create chunks
                chunks = self.chunk_text(content, source, metadata)
                all_chunks.extend(chunks)

            # Convert chunks to vector documents
            vector_docs = []
            for chunk in all_chunks:
                # Generate unique ID for chunk
                chunk_id = hashlib.md5(
                    f"{chunk.source}_{chunk.chunk_index}_{chunk.content[:100]}".encode()
                ).hexdigest()

                vector_doc = VectorDocument(
                    id=chunk_id,
                    text=chunk.content,
                    metadata={
                        **chunk.metadata,
                        'source': chunk.source,
                        'chunk_index': chunk.chunk_index
                    }
                )
                vector_docs.append(vector_doc)

            # Add to vector store
            success = self.vector_store.add_documents(vector_docs)

            if success:
                logger.info(f"Successfully ingested {len(documents)} documents, {len(vector_docs)} chunks")
                return IngestionResult(
                    success=True,
                    documents_processed=len(documents),
                    chunks_created=len(vector_docs)
                )
            else:
                return IngestionResult(
                    success=False,
                    documents_processed=0,
                    chunks_created=0,
                    error_message="Failed to add documents to vector store"
                )

        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            return IngestionResult(
                success=False,
                documents_processed=0,
                chunks_created=0,
                error_message=str(e)
            )

    def search_relevant_context(self, query: str, top_k: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """Search for relevant context and return formatted context + sources"""
        try:
            # Search for relevant documents
            search_results = self.vector_store.search_similar(
                query=query,
                top_k=top_k,
                score_threshold=0.3  # Minimum similarity threshold
            )

            if not search_results:
                return "", []

            # Format context and collect sources
            context_parts = []
            sources = []

            for idx, result in enumerate(search_results):
                doc = result.document

                # Add to context
                context_parts.append(f"[Context {idx + 1}]\n{doc.text}")

                # Add source information
                source_info = {
                    'source': doc.metadata.get('source', 'Unknown'),
                    'type': doc.metadata.get('document_type', 'general'),
                    'similarity_score': result.score,
                    'chunk_index': doc.metadata.get('chunk_index', 0)
                }
                sources.append(source_info)

            context = "\n\n".join(context_parts)
            return context, sources

        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return "", []

    def ask_question(self, question: str, top_k: int = 5) -> RAGResponse:
        """
        Answer a question using RAG (Retrieval-Augmented Generation)

        Args:
            question: User's question
            top_k: Number of relevant documents to retrieve

        Returns:
            RAGResponse with answer, sources, and metadata
        """
        start_time = datetime.now()

        try:
            # Search for relevant context
            context, sources = self.search_relevant_context(question, top_k)

            # Calculate confidence based on search results
            confidence_score = 0.5  # Default confidence
            if sources:
                # Higher confidence if we have good matches
                avg_similarity = sum(s['similarity_score'] for s in sources) / len(sources)
                confidence_score = min(0.95, avg_similarity)

            # Generate response using simplified chat function
            messages = [{"role": "system", "content": self.system_prompt}]

            if context:
                # Use context in the prompt
                user_content = f"Context: {context}\n\nQuestion: {question}"
            else:
                # No relevant context found, use general knowledge
                user_content = f"{question}\n\nNote: No specific restaurant information was found for this question. Please provide a helpful general response and suggest contacting the restaurant directly for specific details."
                confidence_score = 0.3  # Lower confidence for general responses

            messages.append({"role": "user", "content": user_content})

            # Use the simplified chat function for better provider switching
            response = chat(messages, temperature=0.2)

            processing_time = (datetime.now() - start_time).total_seconds()

            return RAGResponse(
                answer=response,
                sources=sources,
                confidence_score=confidence_score,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()

            return RAGResponse(
                answer=f"I apologize, but I encountered an error while processing your question. Please try again or contact the restaurant directly for assistance.",
                sources=[],
                confidence_score=0.0,
                processing_time=processing_time
            )

    def ingest_restaurant_data(self) -> IngestionResult:
        """Ingest default Food Premi restaurant data"""

        # Default restaurant information
        restaurant_docs = [
            {
                'content': """Food Premi - Naturally Nutritious Restaurant

Food Premi is dedicated to serving naturally nutritious and organic food. We believe in the power of wholesome ingredients to nourish both body and soul. Our menu features fresh, locally-sourced organic vegetables, lean proteins, and whole grains.

Our commitment to health extends beyond just organic ingredients. We use minimal processing, avoid artificial preservatives, and focus on cooking methods that preserve nutritional value. Every dish is prepared with care to maximize both flavor and nutritional benefits.

We cater to various dietary preferences including vegetarian, vegan, gluten-free, and keto-friendly options. Our chefs are trained in nutrition and work to create balanced meals that support your health goals.""",
                'source': 'restaurant_info',
                'metadata': {'type': 'about', 'category': 'general'}
            },
            {
                'content': """Menu Categories at Food Premi:

HEALTHY BOWLS
- Quinoa Power Bowl: Organic quinoa, roasted vegetables, avocado, hemp seeds
- Mediterranean Bowl: Brown rice, grilled chicken, olives, cucumber, hummus
- Green Goddess Bowl: Kale, spinach, broccoli, edamame, tahini dressing

ORGANIC SALADS
- Farm Fresh Salad: Mixed organic greens, seasonal vegetables, olive oil vinaigrette
- Protein Power Salad: Spinach, grilled salmon, nuts, seeds, lemon dressing
- Detox Salad: Arugula, beets, carrots, sprouts, ginger dressing

WHOLESOME MAINS
- Grass-fed beef with roasted vegetables
- Wild-caught salmon with quinoa
- Organic chicken with sweet potato
- Plant-based protein options

All dishes are prepared fresh daily using organic, locally-sourced ingredients when possible.""",
                'source': 'menu',
                'metadata': {'type': 'menu', 'category': 'food'}
            },
            {
                'content': """Services and Information:

HOURS
Monday - Friday: 11:00 AM - 9:00 PM
Saturday: 10:00 AM - 10:00 PM
Sunday: 10:00 AM - 8:00 PM

SERVICES
- Dine-in service with health-conscious atmosphere
- Takeout and delivery available
- Catering for events and corporate meetings
- Meal prep services for weekly healthy eating
- Nutritional consultations available

SPECIAL FEATURES
- All ingredients are organic and locally sourced when possible
- Detailed nutritional information available for all menu items
- Custom meal planning for dietary restrictions
- Seasonal menu updates based on fresh produce availability

DIETARY ACCOMMODATIONS
We proudly accommodate:
- Vegetarian and vegan diets
- Gluten-free requirements
- Keto and low-carb preferences
- Paleo diet followers
- Food allergies and sensitivities

Contact us for specific dietary needs and we'll work with you to create the perfect meal.""",
                'source': 'services',
                'metadata': {'type': 'services', 'category': 'info'}
            },
            {
                'content': """Health and Nutrition Philosophy:

At Food Premi, we believe that food is medicine. Our approach to nutrition focuses on:

WHOLE FOODS FIRST
We prioritize whole, unprocessed foods that provide maximum nutritional value. Our ingredients are chosen for their nutrient density and health benefits.

ORGANIC COMMITMENT
All our produce is certified organic, ensuring you avoid harmful pesticides and chemicals while getting the highest quality nutrients.

BALANCED NUTRITION
Every meal is designed to provide a good balance of:
- Complex carbohydrates for sustained energy
- Lean proteins for muscle health and satiety
- Healthy fats for brain function and hormone balance
- Fiber-rich vegetables for digestive health
- Essential vitamins and minerals

COOKING METHODS
We use cooking methods that preserve nutrients:
- Steaming and roasting instead of deep frying
- Minimal cooking times for vegetables
- Cold-pressed oils and raw preparations when beneficial
- Fermented foods for gut health

Our nutritionist-approved recipes ensure you're getting meals that not only taste great but truly nourish your body.""",
                'source': 'nutrition_philosophy',
                'metadata': {'type': 'philosophy', 'category': 'health'}
            }
        ]

        return self.ingest_documents(restaurant_docs)

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            return {
                'vector_store': vector_stats,
                'llm_provider': self.llm_client.config.provider,
                'llm_model': self.llm_client.config.model,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}

# Convenience functions
def get_rag_service() -> RAGService:
    """Get a configured RAG service instance"""
    return RAGService()

def initialize_restaurant_knowledge() -> IngestionResult:
    """Initialize the vector store with default restaurant knowledge"""
    rag = get_rag_service()
    return rag.ingest_restaurant_data()

# Example usage and testing
if __name__ == "__main__":
    try:
        # Initialize RAG service
        rag = get_rag_service()

        # Ingest default restaurant data
        print("Ingesting restaurant data...")
        result = rag.ingest_restaurant_data()
        print(f"Ingestion result: {result}")

        # Test questions
        test_questions = [
            "What healthy food options do you have?",
            "Do you have vegan menu items?",
            "What are your restaurant hours?",
            "Can you accommodate gluten-free diets?",
            "Tell me about your organic ingredients"
        ]

        print("\nTesting questions:")
        for question in test_questions:
            print(f"\nQ: {question}")
            response = rag.ask_question(question)
            print(f"A: {response.answer[:200]}...")
            print(f"Confidence: {response.confidence_score:.2f}")
            print(f"Sources: {len(response.sources)}")

        # Get stats
        stats = rag.get_stats()
        print(f"\nRAG Stats: {stats}")

    except Exception as e:
        print(f"Error: {e}")