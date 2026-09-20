from backend.matching.candidate_generator import CandidateGenerator
from backend.matching.strategies import MatchingStrategy
from models.ride import RideRequest


class MatchingEngine:

    def __init__(
        self,
        candidate_generator: CandidateGenerator,
        strategy: MatchingStrategy
    ):
        self.candidate_generator = candidate_generator
        self.strategy = strategy

    def score_candidates(
        self,
        ride: RideRequest,
        radius: float = 10
    ):

        candidates = (
            self.candidate_generator.find_candidates(
                ride.rider.x,
                ride.rider.y,
                radius
            )
        )

        scored_candidates = []

        for driver in candidates:

            distance = (
                self.candidate_generator.distance(
                    ride.rider.x,
                    ride.rider.y,
                    driver.x,
                    driver.y
                )
            )

            score = self.strategy.calculate_score(
                driver,
                ride,
                distance
            )

            scored_candidates.append(
                {
                    "driver": driver,
                    "distance": distance,
                    "score": score
                }
            )

        return scored_candidates

    def rank_candidates(
        self,
        ride: RideRequest,
        radius: float = 10
    ):

        candidates = self.score_candidates(
            ride,
            radius
        )

        candidates.sort(
            key=lambda candidate: candidate["score"],
            reverse=True
        )

        return candidates