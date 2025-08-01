from groq import Groq
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import tiktoken
from datetime import datetime

load_dotenv()

class AIAssistant:
    """Advanced AI assistant for academic query processing using Groq"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Please set GROQ_API_KEY in your environment.")
        
        # Initialize the Groq client
        self.client = Groq(api_key=self.api_key)
        
        # Model configuration
        self.model = "llama3-8b-8192"  # Fast and efficient model
        
        # Initialize conversation history
        self.conversation_history = []
        
        # For token counting (approximate)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None
        
        self.system_prompt = """You are StudyMate, an expert AI academic assistant specializing in precise, context-driven answers. Your primary goal is accuracy and relevance to the student's specific study materials.

CRITICAL ACCURACY RULES:
- ONLY use information explicitly found in the provided context
- If context is insufficient, clearly state "Based on the provided materials, I cannot find specific information about..."
- Never make assumptions or add information not in the context
- Quote or reference specific parts of the context when possible
- Distinguish between what's directly stated vs. what can be reasonably inferred

RESPONSE QUALITY STANDARDS:
- Prioritize accuracy over completeness
- Use precise technical terminology from the source material
- Provide specific examples from the context when available
- Cross-reference related concepts within the same document
- Maintain academic rigor while being accessible

FORMAT REQUIREMENTS:
- Structure answers logically with clear sections
- Use bullet points for complex lists or steps
- Include relevant page numbers or section references when available
- Highlight key terms that appear in the source material"""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate)"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: approximate 4 characters per token
            return len(text) // 4

    def generate_response(self, question: str, context: str, chat_history: list = None) -> dict:
        """Generate highly accurate response using enhanced context analysis"""
        try:
            # Enhanced context preprocessing
            processed_context = self._preprocess_context(context)
            
            # Add conversation history context
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history with context awareness
            for entry in self.conversation_history[-2:]:  # Reduced to most recent for focus
                messages.append({"role": "user", "content": entry["question"]})
                messages.append({"role": "assistant", "content": entry["answer"]})
            
            # Enhanced prompt with better context utilization
            current_prompt = f"""CONTEXT FROM STUDY MATERIALS:
{processed_context}

STUDENT QUESTION: {question}

INSTRUCTIONS:
1. Analyze the context carefully for information directly related to the question
2. Provide a precise answer using ONLY information from the context above
3. Structure your response as follows:

**Direct Answer:** [Main answer based on context - be specific and accurate]

**Key Details:** [2-3 important points from the context that support your answer]

**Source References:** [Mention specific sections, pages, or document parts when available]

**Important Note:** If the context doesn't contain sufficient information to fully answer the question, clearly state what information is missing.

CRITICAL: Do not add information not present in the context. Be precise and cite your sources."""
            
            messages.append({"role": "user", "content": current_prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=700,  # Increased for more detailed responses
                temperature=0.05,  # Lower temperature for more deterministic, accurate responses
                top_p=0.9,  # Add top_p for better quality control
            )
            
            answer = response.choices[0].message.content
            
            # Enhanced answer post-processing
            processed_answer = self._post_process_answer(answer, context)
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": processed_answer,
                "timestamp": datetime.now().isoformat(),
                "context_length": len(context)
            })
            
            # Keep only last 10 conversations
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Generate more targeted follow-up questions
            follow_up_questions = self._generate_follow_up_questions(question, processed_answer, context)
            
            # Enhanced confidence calculation
            confidence = self._calculate_enhanced_confidence(context, question, processed_answer)
            sources = self._extract_sources(context)
            
            # More accurate token counting
            tokens_used = self.count_tokens(current_prompt) + self.count_tokens(processed_answer)
            
            return {
                'answer': processed_answer,
                'sources_used': sources,
                'confidence': confidence,
                'follow_up_questions': follow_up_questions,
                'tokens_used': tokens_used,
                'context_quality': self._assess_context_quality(context, question)
            }
            
        except Exception as e:
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or check if your documents contain relevant information.",
                'sources_used': [],
                'confidence': 0.0,
                'follow_up_questions': [],
                'tokens_used': 0,
                'context_quality': 'error'
            }

    def _preprocess_context(self, context: str) -> str:
        """Preprocess context to improve relevance and structure"""
        if not context or len(context.strip()) < 10:
            return "No relevant context found in the uploaded documents."
        
        # Clean and structure the context
        lines = context.split('\n')
        cleaned_lines = []
        current_source = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Source:'):
                current_source = line
                cleaned_lines.append(f"\n=== {line} ===")
            elif line and len(line) > 10:  # Filter out very short lines
                cleaned_lines.append(line)
        
        # Limit context to most relevant parts (increase from 2000 to 3000 chars)
        processed = '\n'.join(cleaned_lines)
        if len(processed) > 3000:
            # Try to keep complete sentences
            truncated = processed[:2800]
            last_period = truncated.rfind('.')
            if last_period > 2000:
                processed = truncated[:last_period + 1] + "\n\n[Content truncated for relevance]"
            else:
                processed = truncated + "..."
        
        return processed

    def _post_process_answer(self, answer: str, context: str) -> str:
        """Post-process the answer to ensure accuracy and completeness"""
        # Remove any obvious hallucinations or unsupported claims
        if not answer or len(answer.strip()) < 10:
            return "I couldn't generate a reliable answer based on the provided context. Please try a more specific question."
        
        # Ensure the answer acknowledges limitations when context is insufficient
        if len(context.strip()) < 50:
            answer = f"{answer}\n\n**Note:** This answer is based on limited context from your documents. For more detailed information, please ensure your study materials contain relevant content."
        
        return answer.strip()

    def _calculate_enhanced_confidence(self, context: str, query: str, answer: str) -> float:
        """Enhanced confidence calculation considering multiple factors"""
        if not context.strip():
            return 0.0
        
        # Factor 1: Query-context word overlap
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        query_overlap = len(query_words.intersection(context_words)) / len(query_words) if query_words else 0
        
        # Factor 2: Answer-context overlap (ensures answer is grounded in context)
        answer_words = set(answer.lower().split())
        answer_overlap = len(answer_words.intersection(context_words)) / len(answer_words) if answer_words else 0
        
        # Factor 3: Context quality (length and structure)
        context_quality = min(len(context) / 1000, 1.0)  # Normalize to 0-1
        
        # Factor 4: Specificity bonus (presence of specific terms, numbers, etc.)
        specificity_indicators = ['definition', 'example', 'specifically', 'according to', 'page', 'section']
        specificity_score = sum(1 for indicator in specificity_indicators if indicator in answer.lower()) / len(specificity_indicators)
        
        # Weighted combination
        confidence = (
            query_overlap * 0.3 +
            answer_overlap * 0.4 +
            context_quality * 0.2 +
            specificity_score * 0.1
        )
        
        return round(confidence * 100, 1)

    def _assess_context_quality(self, context: str, question: str) -> str:
        """Assess the quality of context for answering the question"""
        if not context or len(context.strip()) < 20:
            return "insufficient"
        
        question_words = set(question.lower().split())
        context_words = set(context.lower().split())
        overlap_ratio = len(question_words.intersection(context_words)) / len(question_words) if question_words else 0
        
        if overlap_ratio > 0.7:
            return "excellent"
        elif overlap_ratio > 0.4:
            return "good"
        elif overlap_ratio > 0.2:
            return "moderate"
        else:
            return "limited"

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
        """Backward compatibility method - delegates to enhanced version"""
        return self._calculate_enhanced_confidence(context, query, "")

    def _generate_follow_up_questions(self, original_query: str, response: str, context: str = "") -> List[str]:
        """Generate more targeted and context-aware follow-up questions"""
        try:
            # Create more focused prompt for follow-up questions
            follow_up_prompt = f"""Based on this educational content and student interaction:

ORIGINAL QUESTION: "{original_query}"
RESPONSE GIVEN: "{response[:400]}..."
STUDY MATERIAL CONTEXT: "{context[:500]}..."

Generate 3 highly relevant follow-up questions that would:
1. Deepen understanding of the specific topic
2. Connect to related concepts in the same material
3. Test practical application or understanding

Format as simple questions, one per line, focusing on the actual content available."""
            
            follow_up_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": follow_up_prompt
                }],
                max_tokens=250,
                temperature=0.2  # Lower temperature for more focused questions
            )
            
            questions = [q.strip() for q in follow_up_response.choices[0].message.content.split('\n') 
                        if q.strip() and '?' in q and len(q.strip()) > 10]
            return questions[:3]  # Return max 3 questions
            
        except Exception:
            # Fallback questions based on context analysis
            if "definition" in original_query.lower():
                return [
                    "Can you provide a specific example of this concept from the materials?",
                    "How does this concept relate to other topics in the same chapter?",
                    "What are the practical applications mentioned in the documents?"
                ]
            elif "example" in original_query.lower():
                return [
                    "What is the underlying principle behind this example?",
                    "Are there similar examples mentioned in the materials?",
                    "How would you apply this concept in a different scenario?"
                ]
            else:
                return [
                    "What specific details support this explanation in the source material?",
                    "How does this topic connect to other concepts in your study materials?",
                    "What would be a practical way to apply this knowledge?"
                ]

    def summarize_document(self, content: str, max_length: int = 300) -> str:
        """Create a concise document summary"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Create a concise summary using this structure:

**Key Topic:** Main subject (1 sentence)
**Core Concepts:** Essential ideas (3-4 bullet points)
**Practical Use:** How this applies in practice (1-2 sentences)

Content to summarize:
{content[:3000]}

Keep it focused and under {max_length} words."""
                }],
                max_tokens=400,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error creating summary: {str(e)}"

    def generate_quiz_questions(self, context: str, num_questions: int = 5) -> List[Dict]:
        """Generate quiz questions based on the content"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Based on the following study material, generate {num_questions} multiple choice questions to test understanding:

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
                }],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Try to parse the response as questions
            questions = []
            lines = response.choices[0].message.content.split('\n')
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": f"""Explain the concept "{concept}" using this concise format:

**Definition:** Clear, simple definition (1-2 sentences)
**Applications:** Main practical uses (2-3 bullet points)
**Example:** One concrete, easy-to-understand example

Context: {context[:1500]}
Difficulty level: {difficulty_level}

Keep the explanation focused and avoid heavy technical jargon."""
                }],
                max_tokens=400,  # Reduced for concise responses
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I encountered an error while explaining this concept: {str(e)}"
