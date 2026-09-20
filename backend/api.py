from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.driver import Driver
from models.rider import Rider
from models.ride import RideRequest

from backend.spatial.grid_index import GridIndex

from backend.simulation.driver_moment import DriverMovement
from backend.simulation.traffic import TrafficModel

from backend.matching.engine import MatchingEngine
from backend.matching.strategies import BalancedStrategy
from backend.matching.candidate_generator import CandidateGenerator
from backend.matching.offer_manager import OfferManager
from backend.matching.marketplace import Marketplace


# ==================================================
# APP
# ==================================================

app = FastAPI()


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# DRIVERS
# ==================================================

drivers = [
    # Around R1 (20, 20)
    Driver("D1", 20, 20, rating=4.8, speed=30),
    Driver("D6", 25, 22, rating=4.7, speed=32),
    Driver("D7", 18, 25, rating=4.9, speed=28),
    Driver("D8", 30, 18, rating=4.6, speed=35),

    # Around R2 (55, 35)
    Driver("D2", 70, 25, rating=4.5, speed=35),
    Driver("D9", 55, 40, rating=4.8, speed=30),
    Driver("D10", 50, 32, rating=4.6, speed=33),

    # Around R3 (70, 70)
    Driver("D3", 45, 65, rating=4.9, speed=25),
    Driver("D5", 80, 75, rating=4.2, speed=28),
    Driver("D11", 68, 66, rating=4.9, speed=31),
    Driver("D12", 76, 67, rating=4.7, speed=29),
]


# ==================================================
# SPATIAL GRID
# ==================================================

grid = GridIndex(
    cell_size=10
)

for driver in drivers:
    grid.add_driver(driver)


# ==================================================
# SIMULATION
# ==================================================

movement = DriverMovement(
    grid,
    city_size=100
)

traffic = TrafficModel()


# ==================================================
# MATCHING
# ==================================================

strategy = BalancedStrategy(
    traffic
)

candidate_generator = CandidateGenerator(
    grid
)

matching_engine = MatchingEngine(
    candidate_generator,
    strategy
)


# ==================================================
# OFFER SYSTEM
# ==================================================

offer_manager = OfferManager(
    offer_timeout=10
)


# ==================================================
# MARKETPLACE
# ==================================================

marketplace = Marketplace(
    matching_engine,
    offer_manager
)


# ==================================================
# RIDERS
# ==================================================

riders = [
    {
        "id": "R1",
        "x": 20,
        "y": 20
    },

    {
        "id": "R2",
        "x": 55,
        "y": 35
    },

    {
        "id": "R3",
        "x": 70,
        "y": 70
    }
]


# ==================================================
# HELPERS
# ==================================================

SEARCH_RADIUS = 20


def get_rider(rider_id):

    for rider in riders:

        if rider["id"] == rider_id:
            return rider

    return None


def candidate_to_dict(candidate):

    driver = candidate["driver"]

    return {
        "driver": driver.id,
        "x": driver.x,
        "y": driver.y,
        "distance": candidate["distance"],
        "score": candidate["score"]
    }


def build_match_response(ride_id):

    active_state = marketplace.get_active_ride(
        ride_id
    )

    if active_state is None:

        completed_state = marketplace.get_completed_ride(
            ride_id
        )

        if completed_state is None:
            return None

        ride = completed_state["ride"]
        candidates = completed_state["candidates"]
        response = {
            "ride": ride.id,
            "rider": {
                "x": ride.rider.x,
                "y": ride.rider.y
            },
            "radius": SEARCH_RADIUS,
            "status": completed_state["status"],
            "candidates": [
                candidate_to_dict(candidate)
                for candidate in candidates
            ]
        }

        assigned = marketplace.assigned_rides.get(ride_id)
        if assigned:
            response["driver"] = assigned["driver"].id

        return response

    ride = active_state["ride"]
    candidates = active_state["candidates"]

    candidate_data = [
        candidate_to_dict(candidate)
        for candidate in candidates
    ]

    current_offer = marketplace.get_current_offer(
        ride_id
    )

    if current_offer is None:

        return {
            "ride": ride.id,
            "rider": {
                "x": ride.rider.x,
                "y": ride.rider.y
            },
            "radius": SEARCH_RADIUS,
            "status": "waiting",
            "candidates": candidate_data
        }

    current_driver = current_offer.driver

    current_candidate = None

    for candidate in candidates:

        if candidate["driver"].id == current_driver.id:

            current_candidate = candidate
            break

    response = {
        "ride": ride.id,
        "rider": {
            "x": ride.rider.x,
            "y": ride.rider.y
        },
        "radius": SEARCH_RADIUS,
        "status": "matched",
        "driver": current_driver.id,
        "offer_status": current_offer.status,
        "created_at": current_offer.created_at,
        "timeout_at": current_offer.timeout_at,
        "current_time": marketplace.current_time,
        "candidates": candidate_data
    }

    if current_candidate:

        response["score"] = current_candidate["score"]
        response["distance"] = current_candidate["distance"]

    return response


# ==================================================
# RIDE STATE
# ==================================================

@app.get("/ride-state/{ride_id}")
def get_ride_state(ride_id: str):
    state = build_match_response(ride_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ride {ride_id} not found."
        )

    return state


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/")
def root():

    return {
        "status": "Ride Matching Engine running",
        "simulation_time": marketplace.current_time
    }


# ==================================================
# DRIVERS
# ==================================================

@app.get("/drivers")
def get_drivers():

    return [
        {
            "id": driver.id,
            "x": driver.x,
            "y": driver.y,
            "status": driver.status
        }

        for driver in drivers
    ]


# ==================================================
# RIDERS
# ==================================================

@app.get("/riders")
def get_riders():

    return riders


# ==================================================
# SIMULATION STEP
# ==================================================

@app.post("/simulate-step")
def simulate_step():

    traffic.update()

    # Move only available drivers.
    # Offered/busy drivers stay where they are.
    for driver in drivers:

        if driver.status == "available":

            movement.random_move(
                driver,
                max_step=2
            )

    # One simulation step = one second
    timeout_results = marketplace.advance_time(
        1
    )

    return {
        "status": "simulation step completed",
        "current_time": marketplace.current_time,
        "timeouts": timeout_results
    }


# ==================================================
# ADVANCE TIME MANUALLY
# ==================================================

@app.post("/advance-time/{seconds}")
def advance_time(seconds: int):

    if seconds < 0:

        raise HTTPException(
            status_code=400,
            detail="Seconds cannot be negative."
        )

    timeout_results = marketplace.advance_time(
        seconds
    )

    return {
        "status": "time advanced",
        "current_time": marketplace.current_time,
        "timeouts": timeout_results
    }


# ==================================================
# REQUEST RIDE
# ==================================================

@app.post("/request-ride")
def request_ride(rider_id: str = "R1"):

    rider_data = get_rider(
        rider_id
    )

    if rider_data is None:

        raise HTTPException(
            status_code=404,
            detail=f"Rider {rider_id} not found."
        )

    # Don't allow a new request while this
    # rider already has an active ride.
    if marketplace.get_active_ride(
        rider_id
    ) is not None:

        return build_match_response(
            rider_id
        )

    if rider_id in marketplace.assigned_rides:

        return {
            "ride": rider_id,
            "status": "already_assigned"
        }

    ride = RideRequest(
        id=rider_data["id"],

        rider=Rider(
            id=rider_data["id"],
            x=rider_data["x"],
            y=rider_data["y"]
        ),

        destination_x=80,
        destination_y=80
    )

    # Request ride through Marketplace.
    success = marketplace.request_ride(
        ride,
        radius=SEARCH_RADIUS
    )

    if not success:
        return build_match_response(ride.id)

    return build_match_response(
        ride.id
    )


# ==================================================
# ACCEPT OFFER
# ==================================================

@app.post("/accept-offer")
def accept_offer(ride_id: str | None = None):

    # Find the currently active offer.
    if ride_id is None and not offer_manager.active_offers:

        return {
            "status": "no_offer"
        }

    if ride_id is None:
        ride_id = next(iter(offer_manager.active_offers))

    offer = offer_manager.get_offer(
        ride_id
    )

    if offer is None:

        return {
            "status": "no_offer"
        }

    driver_id = offer.driver.id

    success = marketplace.accept_ride(
        ride_id
    )

    if not success:

        return {
            "status": "failed"
        }

    return {
        "status": "accepted",
        "ride": ride_id,
        "driver": driver_id
    }


# ==================================================
# DECLINE OFFER
# ==================================================

@app.post("/decline-offer")
def decline_offer(ride_id: str | None = None):

    if ride_id is None and not offer_manager.active_offers:

        return {
            "status": "no_offer"
        }

    if ride_id is None:
        ride_id = next(iter(offer_manager.active_offers))

    result = marketplace.decline_ride(
        ride_id
    )

    if result is None:

        return {
            "status": "failed"
        }

    if result["status"] == "rematched":

        active_state = marketplace.get_active_ride(
            ride_id
        )

        current_offer = marketplace.get_current_offer(
            ride_id
        )

        score = None
        distance = None

        if active_state and current_offer:

            for candidate in active_state["candidates"]:

                if (
                    candidate["driver"].id
                    == current_offer.driver.id
                ):

                    score = candidate["score"]
                    distance = candidate["distance"]
                    break

        return {
            "status": "rematched",
            "ride": ride_id,
            "previous_driver": result[
                "previous_driver"
            ],
            "driver": result["driver"],
            "score": score,
            "distance": distance
        }

    return {
        "status": "no_more_drivers",
        "ride": ride_id,
        "previous_driver": result[
            "previous_driver"
        ]
    }