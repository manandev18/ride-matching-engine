from models.driver import Driver 
from models.rider import Rider 
from models.ride import RideRequest 
 
from backend.spatial.grid_index import GridIndex 
 
from backend.matching.candidate_generator import CandidateGenerator 
from backend.matching.strategies import BalancedStrategy 
from backend.matching.engine import MatchingEngine 
from backend.matching.offer_manager import OfferManager 
from backend.matching.marketplace import Marketplace 
from backend.matching.batch_matching import BatchMatcher 
from backend.matching.bipartite_matcher import BipartiteMatcher 
 
from backend.simulation.driver_moment import DriverMovement 
from backend.simulation.traffic import TrafficModel 
 
 
def main(): 
 
    # -------------------------------- 
    # 1. Create drivers 
    # -------------------------------- 
 
    drivers = [ 
        Driver( 
            id="D1", 
            x=10, 
            y=10, 
            rating=4.8, 
            speed=30 
        ), 
 
        Driver( 
            id="D2", 
            x=12, 
            y=11, 
            rating=4.5, 
            speed=35 
        ), 
 
        Driver( 
            id="D3", 
            x=15, 
            y=13, 
            rating=4.9, 
            speed=25 
        ), 
 
        Driver( 
            id="D4", 
            x=30, 
            y=30, 
            rating=4.7, 
            speed=40 
        ), 
 
        Driver( 
            id="D5", 
            x=8, 
            y=14, 
            rating=4.2, 
            speed=28 
        ) 
    ] 
 
    # -------------------------------- 
    # 2. Create spatial grid 
    # -------------------------------- 
 
    grid = GridIndex( 
        cell_size=10 
    ) 
 
    for driver in drivers: 
        grid.add_driver(driver) 
 
    # -------------------------------- 
    # 3. Candidate generator 
    # -------------------------------- 
 
    candidate_generator = CandidateGenerator( 
        grid 
    ) 
 
    # -------------------------------- 
    # 4. Matching strategy 
    # -------------------------------- 
 
    traffic = TrafficModel() 
    strategy = BalancedStrategy(traffic) 
 
    # -------------------------------- 
    # 5. Matching engine 
    # -------------------------------- 
 
    matching_engine = MatchingEngine( 
        candidate_generator, 
        strategy 
    ) 
 
    # -------------------------------- 
    # 6. Batch matcher 
    # -------------------------------- 
 
    batch_matcher = BatchMatcher( 
        matching_engine, 
        BipartiteMatcher() 
    ) 
 
    # -------------------------------- 
    # BATCH MATCHING TEST 
    # -------------------------------- 
 
    print("\n==============================") 
    print("BATCH MATCHING TEST") 
    print("==============================") 
 
    # Create multiple riders 
 
    rider1 = Rider( 
        id="R1", 
        x=11, 
        y=10 
    ) 
 
    rider2 = Rider( 
        id="R2", 
        x=14, 
        y=12 
    ) 
 
    rider3 = Rider( 
        id="R3", 
        x=9, 
        y=15 
    ) 
 
    # Create multiple ride requests 
 
    ride1 = RideRequest( 
        id="R1", 
        rider=rider1, 
        destination_x=40, 
        destination_y=40 
    ) 
 
    ride2 = RideRequest( 
        id="R2", 
        rider=rider2, 
        destination_x=50, 
        destination_y=30 
    ) 
 
    ride3 = RideRequest( 
        id="R3", 
        rider=rider3, 
        destination_x=20, 
        destination_y=50 
    ) 
 
    rides = [ 
        ride1, 
        ride2, 
        ride3 
    ] 
 
    # Select available drivers 
 
    batch_drivers = [ 
        drivers[0], 
        drivers[1], 
        drivers[2], 
        drivers[4] 
    ] 
 
    # Build score matrix 
 
    score_matrix = batch_matcher.build_score_matrix( 
        rides, 
        batch_drivers, 
        radius=10 
    ) 
 
    print("\nScore Matrix:") 
 
    for row in score_matrix: 
        print( 
            [ 
                round(score, 2) 
                for score in row 
            ] 
        ) 
 
    # Run global matching 
 
    matches = batch_matcher.match( 
        rides, 
        batch_drivers, 
        radius=10 
    ) 
 
    print("\nGlobal Matches:") 
 
    for match in matches: 
 
        print( 
            f"Ride {match['ride'].id} " 
            f"-> Driver {match['driver'].id} " 
            f"| score={match['score']:.2f}" 
        ) 
 
    # -------------------------------- 
    # 7. Offer manager 
    # -------------------------------- 
 
    offer_manager = OfferManager( 
        offer_timeout=10 
    ) 
 
    # -------------------------------- 
    # 8. Marketplace 
    # -------------------------------- 
 
    marketplace = Marketplace( 
        matching_engine, 
        offer_manager 
    ) 
    marketplace.dispatch_batch_matches(matches)
    # --------------------------------
# BATCH OFFER RESPONSE TEST
# --------------------------------

    print("\n==============================")
    print("BATCH OFFER RESPONSE TEST")
    print("==============================")
    
    # Driver D1 accepts Ride R1
    marketplace.accept_ride("R1")
    
    # Driver D3 declines Ride R2
    marketplace.decline_ride("R2")
    
    # Driver D5 accepts Ride R3
    marketplace.accept_ride("R3")
 
    # -------------------------------- 
    # 9. Driver movement system 
    # -------------------------------- 
 
    movement = DriverMovement( 
        grid, 
        city_size=100 
    ) 
 
    # -------------------------------- 
    # 10. Test driver movement 
    # -------------------------------- 
 
    print("\n==============================") 
    print("DRIVER MOVEMENT TEST") 
    print("==============================") 
 
    driver = drivers[0] 
 
    print( 
        f"D1 before: " 
        f"({driver.x:.2f}, {driver.y:.2f})" 
    ) 
 
    movement.move_driver( 
        driver, 
        5, 
        3 
    ) 
 
    print( 
        f"D1 after: " 
        f"({driver.x:.2f}, {driver.y:.2f})" 
    ) 
 
    # -------------------------------- 
    # 11. Traffic test 
    # -------------------------------- 
 
    print("\n==============================") 
    print("TRAFFIC TEST") 
    print("==============================") 
 
    print( 
        f"Initial traffic multiplier: " 
        f"{traffic.traffic_multiplier:.2f}" 
    ) 
 
    traffic.update() 
 
    print( 
        f"Updated traffic multiplier: " 
        f"{traffic.traffic_multiplier:.2f}" 
    ) 
 
    print( 
        f"D1 normal speed: " 
        f"{drivers[0].speed:.2f} km/h" 
    ) 
 
    print( 
        f"D1 effective speed: " 
        f"{traffic.get_speed(drivers[0]):.2f} km/h" 
    ) 
 
    # -------------------------------- 
    # 12. Create rider 
    # -------------------------------- 
 
    rider = Rider( 
        id="R1", 
        x=11, 
        y=10 
    ) 
 
    ride = RideRequest( 
        id="R1", 
        rider=rider, 
        destination_x=40, 
        destination_y=40 
    ) 
 
    # -------------------------------- 
    # 13. Ride matching test 
    # -------------------------------- 
 
    print("\n==============================") 
    print("RIDE MATCHING TEST") 
    print("==============================") 
 
    marketplace.request_ride( 
        ride, 
        radius=10 
    ) 
 
    # -------------------------------- 
    # 14. Simulate offer timeout 
    # -------------------------------- 
 
    marketplace.advance_time(10) 
 
    # -------------------------------- 
    # 15. Accept next driver 
    # -------------------------------- 
 
    marketplace.accept_ride( 
        "R1" 
    ) 
 
 
if __name__ == "__main__": 
    main()