"""
waiting for pydantic2 to support deserialization of subclasses
"""

from .core import Box


# MAX

class Message(Box):
    maxclass: str = "message"
    numinlets: int = 2
    numoutlets: int = 1

class Comment(Box):
    maxclass: str = "comment"

class Float(Box):
    maxclass: str = "flonum"
    numinlets: int = 1
    numoutlets: int = 2
    outlettype: list[str] = ["", "bang"]
    parameter_enable: int = 0

class Int(Box):
    maxclass: str = "number"
    numinlets: int = 1
    numoutlets: int = 2
    outlettype: list[str] = ["", "bang"]
    parameter_enable: int = 0
