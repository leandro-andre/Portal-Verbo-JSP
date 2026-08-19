from enum import Enum


class ChurchStatus(str, Enum):
    VISITOR = "VISITOR"
    MEMBER = "MEMBER"
    UNKNOWN = "UNKNOWN"
