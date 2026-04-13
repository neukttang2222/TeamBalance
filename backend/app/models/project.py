from enum import StrEnum


class ProjectRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"


class ProjectTaskView(StrEnum):
    MY = "my"
    OVERVIEW = "overview"
    SENSITIVE_REVIEW = "sensitive-review"
