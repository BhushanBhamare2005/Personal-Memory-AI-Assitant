"""
LLM Integration Handler for OpenAI and Google Gemini with RAG support
"""
import os
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM operations with RAG support"""
    
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = None
        self.openai_client = None
        self.gemini_client = None
        
        # Initialize based on provider
        if self.llm_provider == "gemini":
            self._init_gemini()
        else:
            self._init_openai()
        
        # System prompt for the AI memory assistant
        self.system_prompt = self._get_system_prompt()
        
        # Response settings
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        
        logger.info(f"LLM Handler initialized with provider: {self.llm_provider}, model: {self.model}")

    @staticmethod
    def _get_configured_api_key(*environment_names: str) -> Optional[str]:
        for name in environment_names:
            value = os.getenv(name, "").strip()
            if not value:
                continue
            if value.lower().startswith(("your_", "<")):
                continue
            if value.lower() in {"changeme", "replace_me"}:
                continue
            return value
        return None
        
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.api_key = self._get_configured_api_key("OPENAI_API_KEY")
            if not self.api_key:
                logger.warning("OPENAI_API_KEY not set. Using development mode.")
            else:
                self.openai_client = OpenAI(api_key=self.api_key)
                self.llm_provider = "openai"
                logger.info(f"OpenAI initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            self.api_key = self._get_configured_api_key(
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
            )
            if not self.api_key:
                logger.warning("GEMINI_API_KEY not set. Using development mode.")
            else:
                genai.configure(api_key=self.api_key)
                self.gemini_client = genai.GenerativeModel(
                    model_name=self.model or "gemini-2.0-flash"
                )
                self.llm_provider = "gemini"
                logger.info(f"Gemini initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get enhanced system prompt for memory assistant"""
        return """You are an advanced AI Memory Assistant that remembers everything about the user. 

Your Core Responsibilities:
- Recall and reference past conversations, memories, and preferences
- Learn user interests, skills, goals, and habits
- Provide highly personalized suggestions based on user history
- Maintain consistency across multiple conversations
- Be empathetic, helpful, and proactive
- Ask clarifying questions to better understand user needs
- Suggest connections between user interests and goals

Guidelines:
- Always acknowledge relevant past memories when available
- Personalize responses based on retrieved context
- Be concise yet comprehensive
- Cite sources when referencing documents or memories
- Ask permission before making significant decisions
- Be honest about limitations and uncertainties
- Format responses clearly with sections when helpful"""

    async def generate_response_with_context(
        self,
        user_message: str,
        context: str = "",
        user_profile: Dict[str, Any] = None
    ) -> str:
        """Generate a response using LLM with context"""
        if user_profile is None:
            user_profile = {}
        
        try:
            messages = self._build_messages(user_message, context, user_profile)
            
            if self.llm_provider == "gemini" and self.gemini_client:
                return await self._generate_gemini_response(messages)
            elif self.llm_provider == "openai" and self.openai_client:
                return await self._generate_openai_response(messages)
            else:
                return self._generate_development_response(user_message, context)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error: {str(e)}"
    
    def _build_messages(
        self,
        user_message: str,
        context: str,
        user_profile: Dict
    ) -> List[Dict]:
        """Build message list for LLM"""
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Context Information:\n{context}"
            })
        
        if user_profile:
            profile_str = "User Profile: " + json.dumps(user_profile, indent=2)
            messages.append({
                "role": "system",
                "content": profile_str
            })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def _generate_openai_response(self, messages: List[Dict]) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model or "gpt-4o-mini",
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.95
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_gemini_response(self, messages: List[Dict]) -> str:
        """Generate response using Google Gemini"""
        try:
            content = messages[-1]["content"]
            
            response = self.gemini_client.generate_content(
                content,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                    "top_p": 0.95,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _generate_development_response(
        self,
        user_message: str,
        context: str
    ) -> str:
        """Generate intelligent response in development mode"""
        message_lower = user_message.lower()
        response = f"I understand you're asking: {user_message}\n\n"
        
        if context:
            response += "Based on your previous memories and documents:\n"
            response += context[:500] + "\n\n"
        
        response += "Here's my thoughtful response:\n"
        
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            response += "Hello! I'm your Personal AI Assistant. How can I help you today?"
        elif any(word in message_lower for word in ["remember", "memory", "tell me"]):
            response += "I've stored all our conversations and your preferences. I can recall relevant information to give you personalized responses."
        elif any(word in message_lower for word in ["goal", "plan", "suggest"]):
            response += "Based on your profile and history, I can suggest:\n1) Set clear objectives\n2) Break into actionable steps\n3) Track progress regularly"
        elif any(word in message_lower for word in ["learn", "study", "improve"]):
            response += "Great! I can help you learn. I'll:\n1) Find relevant resources\n2) Create a personalized learning path\n3) Track your progress"
        else:
            response += "That's an interesting question. I'll analyze it in the context of your goals and preferences to give you the best answer."
        
        return response
    
    async def generate_suggestion(
        self,
        user_profile: Dict = None,
        recent_conversations: List[Dict] = None
    ) -> str:
        """Generate personalized suggestions for user"""
        if user_profile is None:
            user_profile = {}
        if recent_conversations is None:
            recent_conversations = []
        
        try:
            conv_summary = "\n".join([
                f"- {c.get('user_message', '')} → {c.get('assistant_response', '')[:100]}"
                for c in recent_conversations[:5]
            ])
            
            prompt = f"""Based on this user profile and conversation history, provide ONE personalized suggestion:

User Profile:
{json.dumps(user_profile, indent=2)}

Recent Conversations:
{conv_summary}

Provide a specific, actionable suggestion in 1-2 sentences."""
            
            messages = [
                {"role": "system", "content": "You are a helpful suggestion engine for a personal AI assistant."},
                {"role": "user", "content": prompt}
            ]
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content
            else:
                return "Keep practicing and stay consistent with your goals!"
                
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return "Focus on one goal at a time and track your progress!"
    
    async def extract_insights(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Extract insights from conversations"""
        try:
            conv_text = "\n".join([
                f"User: {c.get('user_message', '')}\nAssistant: {c.get('assistant_response', '')[:200]}"
                for c in conversations[:10]
            ])
            
            prompt = f"""Analyze these conversations and extract insights about the user:

{conv_text}

Provide:
1. Main interests/topics
2. Learning style
3. Goals mentioned
4. Challenges faced
5. Personality traits

Format as JSON."""
            
            messages = [
                {"role": "system", "content": "You are an AI analyst. Extract insights and return as JSON."},
                {"role": "user", "content": prompt}
            ]
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=500
                )
                return json.loads(response.choices[0].message.content)
            else:
                return {
                    "interests": "Based on conversations",
                    "learning_style": "Self-paced",
                    "goals": "Continuous learning"
                }
                
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return {"error": str(e)}
