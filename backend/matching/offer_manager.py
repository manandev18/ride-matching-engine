from backend.matching.offer import Offer


class OfferManager:
    def __init__(self, offer_timeout=10):
        self.offer_timeout = offer_timeout
        self.active_offers = {}

    def create_offer(self, ride, driver, current_time):
        if driver.status != "available":
            return False

        if ride.id in self.active_offers:
            return False

        driver.status = "offered"

        offer = Offer(
            ride_id=ride.id,
            driver=driver,
            created_at=current_time,
            timeout_at=current_time + self.offer_timeout,
        )

        self.active_offers[ride.id] = offer

        print(
            f"Offer sent: Ride {ride.id} -> Driver {driver.id} "
            f"(expires at {offer.timeout_at}s)"
        )
        return True

    def get_offer(self, ride_id):
        return self.active_offers.get(ride_id)

    def accept_offer(self, ride_id):
        offer = self.active_offers.get(ride_id)
        if offer is None or offer.status != "pending":
            return None

        offer.status = "accepted"
        offer.driver.status = "busy"
        del self.active_offers[ride_id]
        return offer

    def decline_offer(self, ride_id):
        offer = self.active_offers.get(ride_id)
        if offer is None or offer.status != "pending":
            return None

        offer.status = "declined"
        offer.driver.status = "available"
        del self.active_offers[ride_id]
        return offer

    def check_timeouts(self, current_time):
        expired_offers = []

        for ride_id, offer in list(self.active_offers.items()):
            if offer.status != "pending":
                continue

            if current_time < offer.timeout_at:
                continue

            offer.status = "timeout"
            offer.driver.status = "available"
            expired_offers.append(offer)
            del self.active_offers[ride_id]

        return expired_offers
