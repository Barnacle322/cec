from enum import Enum


class StatusType(Enum):
    SUCCESS = 1
    WARNING = 2
    ERROR = 3


class Status:
    status_type: StatusType
    msg: str

    def __init__(
        self, type: StatusType = StatusType.ERROR, msg="An unknown error occurred."
    ):
        self.status_type = type
        self.msg = msg

    def __repr__(self):
        return f"<{self.status_type} {self.msg}>"

    def get_status(self, **kwargs) -> dict[str, str]:
        return {"type": str(self.status_type.value), "msg": self.msg, **kwargs}
