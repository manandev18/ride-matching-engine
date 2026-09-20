from abc import ABC, abstractmethod

from models.driver import Driver
from models.ride import RideRequest


class MatchingStrategy(ABC):

    @abstractmethod
    def calculate_score(
        self,
        driver: Driver,
        ride: RideRequest,
        distance: float
    ) -> float:
        pass


class NearestDriverStrategy(MatchingStrategy):

    def calculate_score(
        self,
        driver: Driver,
        ride: RideRequest,
        distance: float
    ) -> float:

        return max(
            0,
            100 - (distance * 10)
        )


class LowestETAStrategy(MatchingStrategy):

    def calculate_score(
        self,
        driver: Driver,
        ride: RideRequest,
        distance: float
    ) -> float:

        if driver.speed <= 0:
            return 0

        eta_minutes = (
            distance / driver.speed
        ) * 60

        return max(
            0,
            100 - (eta_minutes * 5)
        )


class BalancedStrategy(MatchingStrategy):

    def __init__(
        self,
        traffic_model=None
    ):
        self.traffic_model = traffic_model

    def calculate_score(
        self,
        driver: Driver,
        ride: RideRequest,
        distance: float
    ) -> float:



        distance_score = max(
            0,
            100 - (distance * 10)
        )



        if self.traffic_model:

            effective_speed = (
                self.traffic_model.get_speed(
                    driver
                )
            )

        else:

            effective_speed = driver.speed


        if effective_speed > 0:

            eta_minutes = (
                distance / effective_speed
            ) * 60

            eta_score = max(
                0,
                100 - (eta_minutes * 5)
            )

        else:

            eta_score = 0



        rating_score = (
            driver.rating / 5
        ) * 100


        score = (
            0.45 * distance_score +
            0.35 * eta_score +
            0.20 * rating_score
        )

        return score