from pydantic import BaseModel, Field


class BriefingResponse(BaseModel):
    headline: str
    executive_summary: str
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    policy_options: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)


class ChartExplanationResponse(BaseModel):
    paragraph: str


class ChatResponse(BaseModel):
    answer: str
    data_used: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
