from enum import Enum


class ChangeType(str, Enum):
    BECAME_ADMIN = "became_admin"
    LEFT_ADMIN = "left_admin"
