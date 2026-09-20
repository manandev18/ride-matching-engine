from collections import defaultdict

from models.driver import Driver


class GridIndex:

    def __init__(
        self,
        cell_size: float = 10.0
    ):
        self.cell_size = cell_size
        self.grid = defaultdict(list)

    def _get_cell(
        self,
        x: float,
        y: float
    ):

        cell_x = int(
            x // self.cell_size
        )

        cell_y = int(
            y // self.cell_size
        )

        return cell_x, cell_y

    def add_driver(
        self,
        driver: Driver
    ):

        cell = self._get_cell(
            driver.x,
            driver.y
        )

        self.grid[cell].append(
            driver
        )

    def remove_driver(
        self,
        driver: Driver
    ):

        cell = self._get_cell(
            driver.x,
            driver.y
        )

        if driver in self.grid[cell]:

            self.grid[cell].remove(
                driver
            )

    def update_driver(
        self,
        driver: Driver,
        old_x: float,
        old_y: float
    ):

        old_cell = self._get_cell(
            old_x,
            old_y
        )

        new_cell = self._get_cell(
            driver.x,
            driver.y
        )

        # Driver stayed inside the same cell
        if old_cell == new_cell:
            return

        if driver in self.grid[old_cell]:

            self.grid[old_cell].remove(
                driver
            )

        self.grid[new_cell].append(
            driver
        )

    def get_nearby_drivers(
        self,
        x: float,
        y: float,
        radius: float
    ):

        center_x, center_y = self._get_cell(
            x,
            y
        )

        cells_to_check = (
            int(radius // self.cell_size) + 1
        )

        candidates = []

        for dx in range(
            -cells_to_check,
            cells_to_check + 1
        ):

            for dy in range(
                -cells_to_check,
                cells_to_check + 1
            ):

                cell = (
                    center_x + dx,
                    center_y + dy
                )

                candidates.extend(
                    self.grid.get(
                        cell,
                        []
                    )
                )

        return candidates