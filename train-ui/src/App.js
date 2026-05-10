import React, {
  useEffect,
  useState
} from "react";

import "./App.css";

function App() {

  const [trains, setTrains] =
    useState([]);

  const [filtered, setFiltered] =
    useState([]);

  const [selectedRoute,
    setSelectedRoute] =
    useState("forward");

  const [selectedTrain,
    setSelectedTrain] =
    useState(null);

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  // =================================================
  // FETCH TRAINS
  // =================================================

  useEffect(() => {

    fetch(
      "http://127.0.0.1:8000/trains"
    )

      .then((res) => res.json())

      .then((data) => {

        setTrains(data);

      })

      .catch((err) => {

        console.log(err);

      });

  }, []);

  // =================================================
  // FILTER ROUTE
  // =================================================

  useEffect(() => {

    const f = trains.filter((t) => {

      return (
        t.direction === selectedRoute
      );

    });

    setFiltered(f);

  }, [trains, selectedRoute]);

  // =================================================
  // ANALYZE TRAIN
  // =================================================

  const analyzeTrain = async (
    train
  ) => {

    setSelectedTrain(train);

    setLoading(true);

    setResult(null);

    try {

      const response = await fetch(

        `http://127.0.0.1:8000/predict/${train.train_no}`

      );

      const data = await response.json();

      setResult(data);

    } catch {

      setResult({

        error:
        "Backend connection failed"

      });

    }

    setLoading(false);
  };

  // =================================================
  // UI
  // =================================================

  return (

    <div className="app">

      {/* SIDEBAR */}

      <div className="sidebar">

        <div className="logo">

          🚆 RailAI

        </div>

        <div className="route-title">

          Dispatch Intelligence

        </div>

        <div className="stats">

          <div className="stat">

            <h2>
              {filtered.length}
            </h2>

            <p>
              Active Trains
            </p>

          </div>

          <div className="stat">

            <h2>4</h2>

            <p>
              Loop Stations
            </p>

          </div>

        </div>

      </div>

      {/* MAIN */}

      <div className="main">

        {/* HEADER */}

        <div className="header">

          <h1>

            Train Traffic Dashboard

          </h1>

          <p>

            AI-based crossing prediction system

          </p>

        </div>

        {/* TABS */}

        <div className="tabs">

          <button

            className={
              selectedRoute === "forward"
              ? "tab active-tab"
              : "tab"
            }

            onClick={() =>
              setSelectedRoute(
                "forward"
              )
            }

          >

            Jalna → CPSN

          </button>

          <button

            className={
              selectedRoute === "reverse"
              ? "tab active-tab"
              : "tab"
            }

            onClick={() =>
              setSelectedRoute(
                "reverse"
              )
            }

          >

            CPSN → Jalna

          </button>

        </div>

        {/* CONTENT */}

        <div className="content">

          {/* LEFT PANEL */}

          <div className="train-panel">

            {filtered.map((t, i) => (

              <div

                key={i}

                className={

                  selectedTrain?.train_no
                  === t.train_no

                  ? "train-card selected"

                  : "train-card"

                }

                onClick={() =>
                  analyzeTrain(t)
                }

              >

                <div className="train-top">

                  <h3>

                    {t.train_no}

                  </h3>

                  <span className="live">

                    LIVE

                  </span>

                </div>

                <p className="train-name">

                  {t.name}

                </p>

                <div className="train-meta">

                  <span>

                    {t.departure_time}

                  </span>

                  <span>

                    {t.speed} km/h

                  </span>

                </div>

              </div>

            ))}

          </div>

          {/* RIGHT PANEL */}

          <div className="analysis">

            {!selectedTrain && (

              <div className="empty">

                <h2>

                  Select Train

                </h2>

                <p>

                  Click a train to
                  generate dispatch prediction

                </p>

              </div>

            )}

            {loading && (

              <div className="loading">

                <h2>

                  Analyzing railway traffic...

                </h2>

              </div>

            )}

            {result?.error && (

              <div className="error">

                {result.error}

              </div>

            )}

            {result &&
             !loading &&
             !result.error && (

              <div>

                {/* HEADER */}

                <div className="analysis-header">

                  <h2>

                    🚆 {result.selected_train}

                  </h2>

                  <p>

                    {result.selected_name}

                  </p>

                </div>

                {/* NO CONFLICT */}

                {result.message ? (

                  <div className="safe">

                    {result.message}

                  </div>

                ) : (

                  <div className="conflict">

                    <div className="conflict-row">

                      <h3>

                        ⚔️ Opposing Train

                      </h3>

                      <span>

                        {result.confidence}%
                        confidence

                      </span>

                    </div>

                    <p>

                      🚆 {result.opposing_train}

                    </p>

                    <p>

                      {result.opposing_name}

                    </p>

                    <div className="station">

                      📍 Crossing:
                      {" "}
                      {result.crossing_station}

                    </div>

                    <div className="dispatch-box">

                      <div>

                        ⛔ Halt:
                        {" "}

                        <strong>

                          {result.halt_train}

                        </strong>

                      </div>

                      <div>

                        ✅ Pass:
                        {" "}

                        <strong>

                          {result.pass_train}

                        </strong>

                      </div>

                    </div>

                    <div className="delay">

                      ⏱ Predicted Delay:
                      {" "}

                      <strong>

                        {result.predicted_delay}
                        {" "}
                        min

                      </strong>

                    </div>

                  </div>

                )}

              </div>

            )}

          </div>

        </div>

      </div>

    </div>

  );
}

export default App;