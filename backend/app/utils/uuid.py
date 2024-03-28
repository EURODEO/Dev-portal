"""
UUID related utilities
"""


def remove_dashes(uuid: str) -> str:
    """
    Remove dashes from a UUID
    """
    return uuid.replace("-", "")


def restore_dashes(uuid: str) -> str:
    """
    Restore dashes to a UUID
    """
    return f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"
