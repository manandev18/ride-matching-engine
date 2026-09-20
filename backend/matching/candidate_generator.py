import math
from models.driver import Driver
from backend.spatial.grid_index import GridIndex


class CandidateGenerator:
    def __init__(self, spatial_Index:GridIndex):
        self.spatial_index = spatial_Index

    @staticmethod
    def distance(x1:float, y1:float, x2:float, y2:float)->float:
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def find_candidates(self, x:float, y:float, radius: float)->list[Driver]:
        possible_drivers = self.spatial_index.get_nearby_drivers(x, y, radius)
        candidates = []
        for driver in possible_drivers:     
            if driver.status != "available":
                continue

            distance = self.distance(x, y, driver.x, driver.y)
            if distance <= radius:
                candidates.append(driver)
        return candidates
