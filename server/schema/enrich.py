from typing import Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

@dataclass
class EnrichmentResult:
    tags: List[str] 
    contribution: str                 
    used_fallback: bool                   
    fallback_reason: Optional[str]

class Enrich(BaseModel):
    tags: List[str] = Field(description="List of topic keywords describing the abstract")
    contribution: str = Field(description="Main research contribution")

prompt = PromptTemplate.from_template(
"""
Given this paper abstract, return a JSON object with exactly two fields.

Abstract:
{abstract}

Return ONLY valid JSON. No preamble, no markdown, no explanation.

"tags": "<one word, max {tags_max} words>",
"contribution": "<core technical claim only, max {contrib_max} words>"

"""
)