from typing import List, Optional
from pydantic import BaseModel, Field

class ArgumentMinerRequest(BaseModel):
    mode: str = Field(
        default="case",
        description="case | facts | hybrid"
    )
    case_id: Optional[str] = None
    facts: Optional[str] = None


class WinningArgument(BaseModel):
    reasoning: str
    confidence: int


class ArgumentMinerResponse(BaseModel):
    prosecution_arguments: List[str]
    defense_arguments: List[str]
    winning_argument: WinningArgument
