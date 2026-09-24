from pydantic import BaseModel


class NewsSummary(BaseModel):

    headline: str

    summary: str

    key_points: list[str]

    source_differences: list[str]

    uncertain_claims: list[str]