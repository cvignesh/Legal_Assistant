import logging
from app.services.chat.chat_service import chat_service

logger = logging.getLogger(__name__)


LLM_VALIDATION_PROMPT = """
You are a legal assistant. Given the following CONTEXT and ARGUMENT, answer YES if the ARGUMENT is a valid legal argument (not a fact, not a court observation, not metadata), otherwise answer NO. Only answer YES or NO.

CONTEXT:
{context}

ARGUMENT:
{argument}
"""

async def validate_argument_with_llm(argument: str, context: str = "") -> bool:
    """
    Use Groq LLM to validate if the argument is a valid legal argument, given the context.
    Returns True if valid, False otherwise.
    """
    prompt = LLM_VALIDATION_PROMPT.format(argument=argument, context=context)
    try:
        response = await chat_service.llm.apredict(prompt)
        answer = response.strip().upper()
        logger.info(f"LLM validation for argument: {argument[:100]}... => {answer}")
        return answer.startswith("YES")
    except Exception as e:
        logger.error(f"LLM validation failed: {e}")
        return False
