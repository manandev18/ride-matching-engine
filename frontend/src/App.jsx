import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [drivers, setDrivers] = useState([]);
  const [riders, setRiders] = useState([]);

  const [selectedRider, setSelectedRider] = useState("R1");

  const [matchResult, setMatchResult] = useState(null);

  const [offerStatus, setOfferStatus] = useState(null);

  const [simulationTime, setSimulationTime] = useState(0);
  const activeRideRef = useRef(null);
  const simulationInFlightRef = useRef(false);

  const [events, setEvents] = useState([
    {
      source: "SYS",
      message: "Simulation initialized",
    },
  ]);

  // --------------------------------------------------
  // ADD EVENT
  // --------------------------------------------------

  const addEvent = (source, message) => {
    setEvents((previousEvents) => [
      ...previousEvents,
      {
        source,
        message,
      },
    ]);
  };

  useEffect(() => {
    activeRideRef.current = matchResult?.ride ?? null;
  }, [matchResult?.ride]);

  // --------------------------------------------------
  // LOAD DRIVERS + RIDERS
  // --------------------------------------------------

  const loadState = async () => {
    try {
      const driversResponse = await fetch(`${API_URL}/drivers`);

      const ridersResponse = await fetch(`${API_URL}/riders`);

      const driverData = await driversResponse.json();
      const riderData = await ridersResponse.json();

      setDrivers(driverData);
      setRiders(riderData);
    } catch (error) {
      console.error("Failed to load simulation state:", error);
    }
  };

  const syncActiveRide = async () => {
    const rideId = activeRideRef.current;
    if (!rideId) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/ride-state/${rideId}`);
      if (!response.ok) {
        return;
      }

      const data = await response.json();
      setMatchResult(data);

      if (data.status === "matched") {
        setOfferStatus(null);
      } else if (data.status === "assigned") {
        setOfferStatus("accepted");
      } else if (
        data.status === "no_more_drivers" ||
        data.status === "no_drivers"
      ) {
        setOfferStatus("declined");
      } else {
        setOfferStatus(null);
      }
    } catch (error) {
      console.error("Failed to sync active ride:", error);
    }
  };

  // --------------------------------------------------
  // SIMULATION LOOP
  // --------------------------------------------------

  useEffect(() => {
    const updateSimulation = async () => {
      if (simulationInFlightRef.current) {
        return;
      }

      simulationInFlightRef.current = true;

      try {
        const simulationResponse = await fetch(`${API_URL}/simulate-step`, {
          method: "POST",
        });

        const simulationData = await simulationResponse.json();
        setSimulationTime(simulationData.current_time ?? 0);

        if (simulationData.timeouts?.length > 0) {
          for (const timeout of simulationData.timeouts) {
            addEvent(
              timeout.previous_driver,
              `Offer timed out for ${timeout.ride}`,
            );

            if (timeout.rematched) {
              addEvent(timeout.driver, `New offer sent to ${timeout.driver}`);
            } else {
              addEvent(timeout.ride, "No more drivers available");
            }
          }
        }

        await loadState();

        // The backend is authoritative for the current offer.
        // This prevents the UI from displaying an expired driver.
        if (activeRideRef.current) {
          await syncActiveRide();
        }
      } catch (error) {
        console.error("Simulation update failed:", error);
      } finally {
        simulationInFlightRef.current = false;
      }
    };

    updateSimulation();

    const interval = setInterval(updateSimulation, 1000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // --------------------------------------------------
  // REQUEST RIDE
  // --------------------------------------------------

  const requestRide = async () => {
    setOfferStatus(null);

    addEvent("SYS", `Ride request received for ${selectedRider}`);

    try {
      const response = await fetch(
        `${API_URL}/request-ride?rider_id=${selectedRider}`,
        {
          method: "POST",
        },
      );

      const data = await response.json();

      setMatchResult(data);

      if (data.status === "matched") {
        setOfferStatus(null);

        addEvent(data.ride, `Offer sent to ${data.driver}`);

        return;
      }

      if (data.status === "no_drivers") {
        setOfferStatus("declined");

        addEvent(data.ride, "No available drivers within search radius");

        return;
      }

      if (data.status === "already_assigned") {
        setOfferStatus("accepted");

        addEvent(data.ride, "Ride is already assigned");

        return;
      }

      addEvent(data.ride ?? selectedRider, `Request status: ${data.status}`);
    } catch (error) {
      console.error("Ride request failed:", error);

      addEvent("ERROR", "Ride request failed");
    }
  };

  // --------------------------------------------------
  // ACCEPT OFFER
  // --------------------------------------------------

  const acceptOffer = async () => {
    try {
      const response = await fetch(
        `${API_URL}/accept-offer?ride_id=${matchResult?.ride ?? ""}`,
        {
          method: "POST",
        },
      );

      const data = await response.json();

      if (data.status === "accepted") {
        setOfferStatus("accepted");

        setMatchResult((previous) => ({
          ...previous,
          status: "assigned",
          driver: data.driver,
        }));

        addEvent(data.driver, `Offer accepted for ${data.ride}`);

        await loadState();

        return;
      }

      addEvent("SYS", `Accept failed: ${data.status}`);
      await syncActiveRide();
    } catch (error) {
      console.error("Accept offer failed:", error);

      addEvent("ERROR", "Accept offer failed");
    }
  };

  // --------------------------------------------------
  // DECLINE OFFER
  // --------------------------------------------------

  const declineOffer = async () => {
    try {
      const previousDriver = matchResult?.driver;

      const response = await fetch(
        `${API_URL}/decline-offer?ride_id=${matchResult?.ride ?? ""}`,
        {
          method: "POST",
        },
      );

      const data = await response.json();

      if (data.status === "rematched") {
        setOfferStatus(null);

        setMatchResult((previous) => ({
          ...previous,
          status: "matched",
          driver: data.driver,
          score: data.score,
          distance: data.distance,
        }));

        addEvent(previousDriver ?? data.previous_driver, "Offer declined");

        addEvent(data.driver, `New offer sent to ${data.driver}`);

        await loadState();

        return;
      }

      if (data.status === "no_more_drivers") {
        setOfferStatus("declined");

        setMatchResult((previous) => ({
          ...previous,
          status: "no_more_drivers",
        }));

        addEvent(data.previous_driver, "Offer declined");

        addEvent(data.ride, "No more drivers available");

        await loadState();

        return;
      }

      addEvent("SYS", `Decline failed: ${data.status}`);
      await syncActiveRide();
    } catch (error) {
      console.error("Decline offer failed:", error);

      addEvent("ERROR", "Decline offer failed");
    }
  };

  // --------------------------------------------------
  // MAP HELPERS
  // --------------------------------------------------

  const isCandidate = (driverId) => {
    if (!matchResult) {
      return false;
    }

    return (
      matchResult.candidates?.some(
        (candidate) => candidate.driver === driverId,
      ) ?? false
    );
  };

  const isSelected = (driverId) => {
    return matchResult?.status === "matched" && matchResult.driver === driverId;
  };

  const selectedRiderData = riders.find((rider) => rider.id === selectedRider);

  // --------------------------------------------------
  // RENDER
  // --------------------------------------------------

  return (
    <div className="app">
      {/* ==========================================
          HEADER
      ========================================== */}

      <header className="header">
        <div>
          <h1>Ride Matching Engine</h1>

          <span className="subtitle">Real-time marketplace simulation</span>
        </div>

        <div className="header-right">
          <span className="simulation-time">T = {simulationTime}s</span>

          <span className="status">● Simulation Running</span>
        </div>
      </header>

      {/* ==========================================
          MAIN DASHBOARD
      ========================================== */}

      <main className="dashboard">
        {/* ========================================
            MAP
        ======================================== */}

        <section className="map-panel">
          <div className="panel-header">
            <div>
              <h2>City Map</h2>

              <span>100 × 100 simulation space</span>
            </div>

            <div className="map-legend">
              <span>
                <i className="legend-dot driver-dot" />
                Driver
              </span>

              <span>
                <i className="legend-dot rider-dot" />
                Rider
              </span>
            </div>
          </div>

          <div className="city-map">
            {/* SEARCH RADIUS */}

            {matchResult?.rider && (
              <div
                className="search-radius"
                style={{
                  left: `${matchResult.rider.x}%`,
                  top: `${matchResult.rider.y}%`,
                  width: `${matchResult.radius * 2}%`,
                  height: `${matchResult.radius * 2}%`,
                }}
              />
            )}

            {/* CANDIDATE LINES */}

            {matchResult?.rider &&
              matchResult.candidates?.map((candidate) => (
                <svg
                  key={`line-${candidate.driver}`}
                  className="candidate-line"
                >
                  <line
                    x1={`${matchResult.rider.x}%`}
                    y1={`${matchResult.rider.y}%`}
                    x2={`${candidate.x}%`}
                    y2={`${candidate.y}%`}
                    className={
                      candidate.driver === matchResult.driver
                        ? "selected-line"
                        : ""
                    }
                  />
                </svg>
              ))}

            {/* DRIVERS */}

            {drivers.map((driver) => (
              <div
                key={driver.id}
                className={`
                  driver
                  ${driver.status}
                  ${isCandidate(driver.id) ? "candidate" : ""}
                  ${isSelected(driver.id) ? "selected" : ""}
                `}
                style={{
                  left: `${driver.x}%`,
                  top: `${driver.y}%`,
                }}
                title={`Driver ${driver.id}`}
              >
                {driver.id}
              </div>
            ))}

            {/* RIDERS */}

            {riders.map((rider) => (
              <div
                key={rider.id}
                className={`
                  rider
                  ${rider.id === selectedRider ? "selected-rider" : ""}
                `}
                style={{
                  left: `${rider.x}%`,
                  top: `${rider.y}%`,
                }}
                title={`Ride ${rider.id}`}
                onClick={() => setSelectedRider(rider.id)}
              >
                {rider.id}
              </div>
            ))}
          </div>
        </section>

        {/* ========================================
            SIDE PANEL
        ======================================== */}

        <aside className="side-panel">
          {/* ======================================
              DRIVERS
          ====================================== */}

          <div className="card">
            <div className="card-title-row">
              <h3>Drivers</h3>

              <span>{drivers.length} online</span>
            </div>

            {drivers.map((driver) => (
              <div className="driver-row" key={driver.id}>
                <div className="driver-info">
                  <span className="driver-name">{driver.id}</span>

                  <span className="driver-location">
                    ({driver.x.toFixed(1)}, {driver.y.toFixed(1)})
                  </span>
                </div>

                <span className={`driver-status ${driver.status}`}>
                  {driver.status}
                </span>
              </div>
            ))}
          </div>

          {/* ======================================
              RIDE REQUEST
          ====================================== */}

          <div className="card">
            <h3>Ride Request</h3>

            <div className="rider-selector">
              <p>Select Rider</p>

              <div className="rider-buttons">
                {riders.map((rider) => (
                  <button
                    key={rider.id}
                    className={
                      selectedRider === rider.id
                        ? "rider-button selected-rider-button"
                        : "rider-button"
                    }
                    onClick={() => setSelectedRider(rider.id)}
                  >
                    {rider.id}
                  </button>
                ))}
              </div>
            </div>

            {selectedRiderData && (
              <div className="selected-rider-info">
                <strong>Selected rider: {selectedRider}</strong>

                <span>
                  Location: ({selectedRiderData.x}, {selectedRiderData.y})
                </span>
              </div>
            )}

            <button className="request-button" onClick={requestRide}>
              Request Ride for {selectedRider}
            </button>

            {/* MATCH RESULT */}

            {matchResult && (
              <div className="match-result">
                <div className="result-header">
                  <strong>{matchResult.ride}</strong>

                  <span className={`result-status ${matchResult.status}`}>
                    {matchResult.status}
                  </span>
                </div>

                <p>
                  <strong>Search radius:</strong> {matchResult.radius}
                </p>

                {matchResult.status === "matched" && (
                  <>
                    <div className="selected-driver">
                      <strong>Current Offer</strong>

                      <div className="selected-driver-name">
                        {matchResult.driver}
                      </div>

                      {matchResult.score !== undefined && (
                        <div>Score: {Number(matchResult.score).toFixed(2)}</div>
                      )}

                      {matchResult.distance !== undefined && (
                        <div>
                          Distance: {Number(matchResult.distance).toFixed(2)}
                        </div>
                      )}
                    </div>

                    {/* OFFER CONTROLS */}

                    {offerStatus === null && (
                      <div className="offer-controls">
                        <p>
                          <strong>Offer sent to {matchResult.driver}</strong>
                        </p>

                        <p className="timeout-info">
                          Offer timeout: 10 seconds
                        </p>

                        <div className="offer-buttons">
                          <button
                            className="accept-button"
                            onClick={acceptOffer}
                          >
                            Accept
                          </button>

                          <button
                            className="decline-button"
                            onClick={declineOffer}
                          >
                            Decline
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {matchResult.status === "assigned" && (
                  <div className="offer-status accepted-status">
                    ✓ Ride assigned to <strong>{matchResult.driver}</strong>
                  </div>
                )}

                {offerStatus === "accepted" &&
                  matchResult.status !== "assigned" && (
                    <div className="offer-status accepted-status">
                      ✓ Offer accepted
                    </div>
                  )}

                {matchResult.status === "no_more_drivers" && (
                  <div className="offer-status declined-status">
                    No more drivers available for this ride.
                  </div>
                )}

                {matchResult.status === "no_drivers" && (
                  <div className="no-drivers">
                    No available drivers within the search radius.
                  </div>
                )}

                {/* CANDIDATES */}

                {matchResult.candidates &&
                  matchResult.candidates.length > 0 && (
                    <div className="candidate-list">
                      <h4>Ranked Candidates</h4>

                      {matchResult.candidates.map((candidate, index) => (
                        <div
                          className={`
                              candidate-row
                              ${
                                candidate.driver === matchResult.driver
                                  ? "candidate-selected"
                                  : ""
                              }
                            `}
                          key={candidate.driver}
                        >
                          <span className="candidate-rank">#{index + 1}</span>

                          <span>{candidate.driver}</span>

                          <span>{Number(candidate.distance).toFixed(2)}</span>

                          <span>{Number(candidate.score).toFixed(2)}</span>
                        </div>
                      ))}

                      <div className="candidate-header">
                        <span />
                        <span>Driver</span>
                        <span>Distance</span>
                        <span>Score</span>
                      </div>
                    </div>
                  )}
              </div>
            )}
          </div>

          {/* ======================================
              EVENT LOG
          ====================================== */}

          <div className="card">
            <div className="card-title-row">
              <h3>Event Log</h3>

              <span>{events.length} events</span>
            </div>

            <div className="event-log">
              {events
                .slice()
                .reverse()
                .map((event, index) => (
                  <div className="event" key={index}>
                    <span className="event-source">{event.source}</span>

                    <p>{event.message}</p>
                  </div>
                ))}
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
