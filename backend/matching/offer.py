from dataclasses import dataclass
from models.driver import Driver

@dataclass
class Offer:
    ride_id: str
    driver: Driver
    created_at: float
    timeout_at:float
    status: str = "pending"  
