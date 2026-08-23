from enum import Enum


class ChurchStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    VISITOR = "VISITOR"
    MEMBER = "MEMBER"
    INACTIVE_MEMBER = "INACTIVE_MEMBER"
