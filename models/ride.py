from dataclasses import dataclass
from models.rider import Rider

@dataclass
class RideRequest:
    id : str
    rider: Rider
    destination_x: float
    destination_y: float
    passengers: int = 1