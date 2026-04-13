from pydantic import BaseModel


class MemberContribution(BaseModel):
    name: str
    completed_tasks: int
    total_weighted_score: float


class ContributionResponse(BaseModel):
    project_id: str
    contributions: list[MemberContribution]
