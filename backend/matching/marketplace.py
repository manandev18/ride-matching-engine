class Marketplace:
    def __init__(self, matching_engine, offer_manager):
        self.matching_engine = matching_engine
        self.offer_manager = offer_manager
        self.active_rides = {}
        self.assigned_rides = {}
        self.completed_rides = {}
        self.current_time = 0

    def request_ride(self, ride, radius=20):
        print(f"\nRide requested: {ride.id}")

        if ride.id in self.active_rides:
            print(f"Ride {ride.id} already has an active request.")
            return False

        candidates = self.matching_engine.rank_candidates(ride, radius)

        if not candidates:
            self.completed_rides[ride.id] = {
                "ride": ride,
                "candidates": [],
                "status": "no_drivers",
            }
            print(f"No drivers available for Ride {ride.id}")
            return False

        self.active_rides[ride.id] = {
            "ride": ride,
            "candidates": candidates,
            "current_index": 0,
        }

        return self._offer_next_driver(ride.id)

    def _offer_next_driver(self, ride_id):
        ride_state = self.active_rides.get(ride_id)
        if ride_state is None:
            return False

        candidates = ride_state["candidates"]
        index = ride_state["current_index"]

        while index < len(candidates):
            candidate = candidates[index]
            driver = candidate["driver"]


            ride_state["current_index"] = index + 1
            index += 1

            if driver.status != "available":
                continue

            print(
                f"\nCandidate: {driver.id} "
                f"| score={candidate['score']:.2f} "
                f"| distance={candidate['distance']:.2f}"
            )

            if self.offer_manager.create_offer(
                ride_state["ride"], driver, self.current_time
            ):
                return True

        print(f"No more drivers available for Ride {ride_id}")

        self.completed_rides[ride_id] = {
            "ride": ride_state["ride"],
            "candidates": candidates,
            "status": "no_more_drivers",
        }
        del self.active_rides[ride_id]
        return False

    def accept_ride(self, ride_id):
        offer = self.offer_manager.accept_offer(ride_id)
        if offer is None:
            print(f"No active offer found for Ride {ride_id}")
            return False

        ride_state = self.active_rides.pop(ride_id, None)
        if ride_state is None:
            # Defensive cleanup if state was already removed.
            offer.driver.status = "available"
            return False

        ride = ride_state["ride"]
        driver = offer.driver

        self.assigned_rides[ride_id] = {"ride": ride, "driver": driver}
        self.completed_rides[ride_id] = {
            "ride": ride,
            "candidates": ride_state["candidates"],
            "status": "assigned",
        }

        print(f"\nDriver {driver.id} accepted Ride {ride_id}")
        print(f"Ride {ride_id} assigned to Driver {driver.id}")
        return True

    def decline_ride(self, ride_id):
        offer = self.offer_manager.decline_offer(ride_id)
        if offer is None:
            print(f"No active offer found for Ride {ride_id}")
            return None

        previous_driver = offer.driver
        print(f"\nDriver {previous_driver.id} declined Ride {ride_id}")

        if self._offer_next_driver(ride_id):
            new_offer = self.offer_manager.get_offer(ride_id)
            return {
                "status": "rematched",
                "ride": ride_id,
                "previous_driver": previous_driver.id,
                "driver": new_offer.driver.id,
            }

        return {
            "status": "no_more_drivers",
            "ride": ride_id,
            "previous_driver": previous_driver.id,
        }

    def advance_time(self, seconds):
        if seconds < 0:
            raise ValueError("Time cannot move backwards.")

        self.current_time += seconds
        print(f"\n--- TIME ADVANCED TO {self.current_time}s ---")

        expired_offers = self.offer_manager.check_timeouts(self.current_time)
        timeout_results = []

        for offer in expired_offers:
            ride_id = offer.ride_id

            print(
                f"Offer timeout: Driver {offer.driver.id} "
                f"for Ride {ride_id}"
            )

            result = {
                "ride": ride_id,
                "previous_driver": offer.driver.id,
                "rematched": False,
                "driver": None,
            }

            # If the ride was accepted/terminated while this timeout was
            # being processed, there is nothing left to rematch.
            if ride_id not in self.active_rides:
                timeout_results.append(result)
                continue

            if self._offer_next_driver(ride_id):
                new_offer = self.offer_manager.get_offer(ride_id)
                result["rematched"] = True
                result["driver"] = new_offer.driver.id
                result["created_at"] = new_offer.created_at
                result["timeout_at"] = new_offer.timeout_at

                print(
                    f"Timeout rematch: Ride {ride_id} -> "
                    f"Driver {new_offer.driver.id}"
                )
            else:
                print(f"Ride {ride_id} has no more available drivers.")

            timeout_results.append(result)

        return timeout_results

    def get_current_offer(self, ride_id):
        return self.offer_manager.get_offer(ride_id)

    def get_active_ride(self, ride_id):
        return self.active_rides.get(ride_id)

    def get_completed_ride(self, ride_id):
        return self.completed_rides.get(ride_id)

    def dispatch_batch_matches(self, matches):
        results = []

        for match in matches:
            ride = match["ride"]
            driver = match["driver"]

            print(
                f"\nBatch match selected: Ride {ride.id} -> Driver {driver.id}"
            )

            self.active_rides[ride.id] = {
                "ride": ride,
                "candidates": [],
                "current_index": 0,
            }

            success = self.offer_manager.create_offer(
                ride, driver, self.current_time
            )

            results.append({
                "ride": ride.id,
                "driver": driver.id,
                "offer_created": success,
            })

        return results
