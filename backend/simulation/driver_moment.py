import random

from models.driver import Driver
from backend.spatial.grid_index import GridIndex


class DriverMovement:

    def __init__(
        self,
        spatial_index: GridIndex,
        city_size=100
    ):
        self.spatial_index = spatial_index
        self.city_size = city_size

    def move_driver(
        self,
        driver: Driver,
        dx: float,
        dy: float
    ):

        old_x = driver.x
        old_y = driver.y

        driver.x += dx
        driver.y += dy

        # Keep driver inside city boundaries
        driver.x = max(
            0,
            min(driver.x, self.city_size)
        )

        driver.y = max(
            0,
            min(driver.y, self.city_size)
        )

        self.spatial_index.update_driver(
            driver,
            old_x,
            old_y
        )

    def random_move(
        self,
        driver: Driver,
        max_step=3
    ):

        dx = random.uniform(
            -max_step,
            max_step
        )

        dy = random.uniform(
            -max_step,
            max_step
        )

        self.move_driver(
            driver,
            dx,
            dy
        )