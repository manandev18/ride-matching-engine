from backend.api import matching_engine, drivers, riders

from backend.matching.batch_matching import BatchMatcher
from backend.matching.bipartite_matcher import BipartiteMatcher
from models.ride import RideRequest
from models.rider import Rider


# --------------------------------------------------
# Create batch matcher
# --------------------------------------------------

bipartite_matcher = BipartiteMatcher()

batch_matcher = BatchMatcher(
    matching_engine,
    bipartite_matcher
)


# --------------------------------------------------
# Create rides from existing riders
# --------------------------------------------------

rides = []

for rider_data in riders:

    rider = Rider(
        id=rider_data["id"],
        x=rider_data["x"],
        y=rider_data["y"]
    )

    ride = RideRequest(
        id=rider.id,
        rider=rider,
        destination_x=80,
        destination_y=80
    )

    rides.append(ride)


# --------------------------------------------------
# Build score matrix
# --------------------------------------------------

matrix = batch_matcher.build_score_matrix(
    rides,
    drivers,
    radius=20
)


# --------------------------------------------------
# Print matrix
# --------------------------------------------------

print()
print("=" * 70)
print("                    SCORE MATRIX")
print("=" * 70)
print()

print(f"{'Ride':<10}", end="")

for driver in drivers:
    print(f"{driver.id:>8}", end="")

print()
print("-" * (10 + len(drivers) * 8))


for ride, row in zip(rides, matrix):

    print(f"{ride.id:<10}", end="")

    for score in row:

        if score <= batch_matcher.INVALID_SCORE:
            print(f"{'--':>8}", end="")
        else:
            print(f"{score:>8.2f}", end="")

    print()


# --------------------------------------------------
# Global matching
# --------------------------------------------------

matches = batch_matcher.match(
    rides,
    drivers,
    radius=20
)


print()
print("=" * 70)
print("                    GLOBAL MATCHES")
print("=" * 70)
print()

for match in matches:

    print(
        f"{match['ride'].id} -> "
        f"{match['driver'].id} "
        f"| score = {match['score']:.2f}"
    )

print()