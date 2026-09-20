import random

class TrafficModel:
    def __init__(self):
        self.traffic_multiplier = 1.0

    def update(self):
        """
        Simulate changing traffic conditions.
        1.0 = normal traffic
        0.8 = slower traffic
        1.2 = faster traffic

        """

        self.traffic_multiplier = random.uniform(0.6, 1.2)

    def get_speed(self, driver):
        return (driver.speed*self.traffic_multiplier)