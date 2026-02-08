
import asyncio
import logging
import json
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from app.core.config import settings
from app.services.drafting.models import SubstantiveGap, LegalIssue
from app.services.drafting.prompts import SUBSTANTIVE_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class SubstantiveValidator:
    """
    Analyzes the legal "ingredients" of a case (e.g., Deception, Entrustment)
    and identifies missing elements that could weaken the petition.
    """
    
    def __init__(self):
        # Reuse existing LLM config logic
        provider = settings.LLM_PROVIDER.lower()
        if provider == "groq":
            self.llm = ChatGroq(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.1
            )
        else:
             self.llm = ChatOpenAI(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=0.1
            )

    async def analyze(self, user_story: str, issues: List[LegalIssue]) -> List[SubstantiveGap]:
        """Analysis logic using LLM"""
        try:
            # Prepare section summary
            sections_text = ", ".join([f"{i.act} {i.section}" for i in issues])
            
            prompt = SUBSTANTIVE_ANALYSIS_PROMPT.format(
                user_story=user_story,
                sections=sections_text
            )
            
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content="You are a JSON-outputting Senior Legal Counsel."), 
                    HumanMessage(content=prompt)
                ]
            )
            
            # Robust JSON extraction
            content = response.content.strip()
            start_idx = content.find('[')
            end_idx = content.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]
                
            data = json.loads(content)
            results = [SubstantiveGap(**item) for item in data]
            
            logger.info(f"Substantive Analysis found {len(results)} gaps.")
            return results
            
        except Exception as e:
            logger.error(f"Substantive Analysis Failed: {e}")
            return [] # Fail safe
            
substantive_validator = SubstantiveValidator()
