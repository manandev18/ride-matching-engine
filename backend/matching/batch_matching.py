from backend.matching.bipartite_matcher import BipartiteMatcher


class BatchMatcher:

    INVALID_SCORE = -1_000_000

    def __init__(
        self,
        matching_engine,
        bipartite_matcher
    ):
        self.matching_engine = matching_engine
        self.bipartite_matcher = bipartite_matcher

    def build_score_matrix(
        self,
        rides,
        drivers,
        radius=10
    ):

        matrix = []

        for ride in rides:

            candidates = (
                self.matching_engine.score_candidates(
                    ride,
                    radius
                )
            )

            scores_by_driver = {
                result["driver"].id: result["score"]
                for result in candidates
            }

            row = []

            for driver in drivers:

                score = scores_by_driver.get(
                    driver.id,
                    self.INVALID_SCORE
                )

                row.append(score)

            matrix.append(row)

        return matrix

    def match(
        self,
        rides,
        drivers,
        radius=10
    ):

        matrix = self.build_score_matrix(
            rides,
            drivers,
            radius
        )

        matches = self.bipartite_matcher.match(
            matrix
        )

        results = []

        for (
            rider_index,
            driver_index,
            score
        ) in matches:

            if score <= self.INVALID_SCORE:
                continue

            results.append({
                "ride": rides[rider_index],
                "driver": drivers[driver_index],
                "score": score
            })

        return results