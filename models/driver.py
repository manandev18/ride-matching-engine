from dataclasses import dataclass


@dataclass
class Driver:
    id : str
    x : float
    y : float
    rating : float = 5.0
    capacity : int = 4
    status: str = "available"
    speed: float = 30.0

