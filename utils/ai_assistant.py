import google.generativeai as genai
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import tiktoken

load_dotenv()

class AIAssistant:
    """Advanced AI assistant for academic query processing using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in your environment.")
        
        # Configure Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Initialize the Gemini model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # For token counting (approximate)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None
        
        self.system_prompt = """You are StudyMate, an advanced AI academic assistant. Your role is to help students understand and learn from their study materials through intelligent question-answering.

Key capabilities:
- Provide accurate, well-structured answers based on the provided context
- Explain complex concepts in simple terms
- Offer multiple perspectives when appropriate
- Suggest related questions for deeper learning
- Maintain academic integrity and encourage critical thinking

Guidelines:
- Always base your answers on the provided context
- If the context doesn't contain sufficient information, clearly state this
- Use examples and analogies to clarify difficult concepts
- Encourage active learning by suggesting follow-up questions
- Maintain a helpful, encouraging tone
- Format responses clearly with proper structure"""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate)"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: approximate 4 characters per token
            return len(text) // 4

    def generate_response(self, query: str, context: str, conversation_history: List[Dict] = None) -> Dict:
        """Generate AI response based on query and context using Google Gemini"""
        try:
            # Prepare conversation history
            history_text = ""
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 messages for context
                    if msg['role'] == 'user':
                        history_text += f"User: {msg['content']}\n"
                    elif msg['role'] == 'assistant':
                        history_text += f"Assistant: {msg['content']}\n"
            
            # Prepare the main prompt with context
            full_prompt = f"""{self.system_prompt}

CONVERSATION HISTORY:
{history_text}

STUDY MATERIAL CONTEXT:
{context}

CURRENT QUESTION: {query}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Uses information from the provided context
3. Explains concepts clearly
4. Suggests related questions if relevant
5. Maintains academic rigor"""
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            # Prepare response data
            response_data = {
                'answer': response.text,
                'sources_used': self._extract_sources(context),
                'confidence': self._calculate_confidence(context, query),
                'follow_up_questions': self._generate_follow_up_questions(query, response.text),
                'tokens_used': self.count_tokens(context + query + response.text)
            }
            
            return response_data
            
        except Exception as e:
            return {
                'answer': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'sources_used': [],
                'confidence': 0.0,
                'follow_up_questions': [],
                'tokens_used': 0,
                'error': str(e)
            }

    def _extract_sources(self, context: str) -> List[str]:
        """Extract source information from context"""
        sources = []
        lines = context.split('\n')
        for line in lines:
            if line.startswith('Source:'):
                source = line.replace('Source:', '').strip()
                if source not in sources:
                    sources.append(source)
        return sources

    def _calculate_confidence(self, context: str, query: str) -> float:
        """Calculate confidence score based on context relevance"""
        if not context.strip():
            return 0.0
        
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        # Simple overlap-based confidence
        overlap = len(query_words.intersection(context_words))
        confidence = min(overlap / len(query_words) if query_words else 0, 1.0)
        
        return round(confidence * 100, 1)

    def _generate_follow_up_questions(self, original_query: str, response: str) -> List[str]:
        """Generate relevant follow-up questions"""
        try:
            follow_up_prompt = f"""Based on this question: "{original_query}"
And this response: "{response[:500]}..."

Generate 3 relevant follow-up questions that would help the student learn more about this topic. 
Format as a simple list, one question per line."""
            
            follow_up_response = self.model.generate_content(follow_up_prompt)
            questions = [q.strip() for q in follow_up_response.text.split('\n') if q.strip() and '?' in q]
            
            return questions[:3]  # Return max 3 questions
            
        except Exception:
            return [
                "Can you provide more examples of this concept?",
                "How does this relate to other topics in the material?",
                "What are the practical applications of this information?"
            ]

    def summarize_document(self, text: str, document_name: str = "Document") -> Dict:
        """Generate a comprehensive summary of a document"""
        try:
            summary_prompt = f"""Please provide a comprehensive summary of the following document: "{document_name}"

Content:
{text[:4000]}

Please provide:
1. A brief overview (2-3 sentences)
2. Key topics covered (bullet points)
3. Main concepts and definitions
4. Important facts or figures
5. Potential study questions

Format your response clearly with headers for each section."""
            
            response = self.model.generate_content(summary_prompt)
            
            return {
                'summary': response.text,
                'document_name': document_name,
                'word_count': len(text.split()),
                'estimated_reading_time': max(1, len(text.split()) // 200),  # ~200 words per minute
                'tokens_used': self.count_tokens(text + response.text)
            }
            
        except Exception as e:
            return {
                'summary': f"Error generating summary: {str(e)}",
                'document_name': document_name,
                'word_count': 0,
                'estimated_reading_time': 0,
                'tokens_used': 0,
                'error': str(e)
            }

    def generate_quiz_questions(self, context: str, num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions based on the content"""
        try:
            quiz_prompt = f"""Based on the following study material, generate {num_questions} multiple choice questions to test understanding:

Content:
{context[:3000]}

For each question, provide:
- The question text
- 4 answer options (A, B, C, D)
- The correct answer
- A brief explanation

Format as JSON with this structure for each question:
{{
    "question": "Question text",
    "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
    "correct": "A",
    "explanation": "Why this is correct"
}}"""
            
            response = self.model.generate_content(quiz_prompt)
            
            # Try to parse the response as questions
            questions = []
            lines = response.text.split('\n')
            current_question = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Question:') or line.startswith('Q:'):
                    if current_question:
                        questions.append(current_question)
                    current_question = {'question': line.split(':', 1)[1].strip()}
                elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                    if 'options' not in current_question:
                        current_question['options'] = []
                    current_question['options'].append(line)
                elif line.startswith('Correct:') or line.startswith('Answer:'):
                    current_question['correct'] = line.split(':', 1)[1].strip()
                elif line.startswith('Explanation:'):
                    current_question['explanation'] = line.split(':', 1)[1].strip()
            
            if current_question:
                questions.append(current_question)
            
            return questions[:num_questions]
            
        except Exception as e:
            return [{
                'question': f"Error generating quiz questions: {str(e)}",
                'options': ["A. Error", "B. Error", "C. Error", "D. Error"],
                'correct': "A",
                'explanation': "An error occurred while generating questions."
            }]

    def explain_concept(self, concept: str, context: str, difficulty_level: str = "intermediate") -> str:
        """Provide detailed explanation of a specific concept"""
        try:
            explanation_prompt = f"""Please explain the concept "{concept}" based on the provided context.

Context:
{context}

Difficulty level: {difficulty_level}

Please provide:
1. A clear definition
2. Key characteristics or properties
3. Examples if available in the context
4. How it relates to other concepts
5. Real-world applications if relevant

Adjust the explanation complexity for {difficulty_level} level understanding."""
            
            response = self.model.generate_content(explanation_prompt)
            return response.text
            
        except Exception as e:
            return f"I encountered an error while explaining this concept: {str(e)}"
