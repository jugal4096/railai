import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# =====================================================
# PAGE
# =====================================================

st.set_page_config(
    page_title="RailAI Dispatch",
    layout="wide"
)

# =====================================================
# ROUTE MAP
# =====================================================

ROUTE = {
    "Jalna": 0,
    "Dinagaon": 10,
    "Badnapur": 20,
    "Karmad": 40,
    "Chikalthana": 55,
    "CPSN": 70
}

LOOPS = [
    "Dinagaon",
    "Badnapur",
    "Karmad",
    "Chikalthana"
]

# =====================================================
# PRIORITY
# =====================================================

PRIORITY = {
    "VB": 5,
    "SF": 4,
    "JSHTB": 4,
    "EXP": 3,
    "DEMU": 2,
    "PASS": 1
}

# =====================================================
# LOAD TRAINS
# =====================================================

@st.cache_data
def load_trains():

    conn = sqlite3.connect("trains.db")

    df = pd.read_sql(
        "SELECT * FROM trains",
        conn
    )

    conn.close()

    return df

# =====================================================
# LOAD HISTORY
# =====================================================

@st.cache_data
def load_history():

    return pd.read_csv(
        "final_clean_train_dataset.csv"
    )

# =====================================================
# FILTER UPCOMING TRAINS
# =====================================================

def get_relevant_trains(df):

    now = datetime.now()

    current_min = (
        now.hour * 60 + now.minute
    )

    max_min = current_min + 720

    result = []

    for _, row in df.iterrows():

        try:

            h, m = map(
                int,
                row["dep_time"].split(":")
            )

            dep = h * 60 + m

            if current_min <= dep <= max_min:

                result.append(row)

        except:
            pass

    return pd.DataFrame(result)

# =====================================================
# LIVE POSITION ENGINE
# =====================================================

def get_live_position(train):

    try:

        now = datetime.now()

        current_min = (
            now.hour * 60 + now.minute
        )

        h, m = map(
            int,
            train["dep_time"].split(":")
        )

        dep = h * 60 + m

        elapsed = current_min - dep

        if elapsed < 0:
            return None

        speed = float(
            train["avg_speed"]
        )

        distance = (
            speed * elapsed
        ) / 60

        # DOWN = Jalna → CPSN
        if train["direction"] == "DOWN":

            pos = distance

        else:

            pos = 70 - distance

        return max(
            0,
            min(70, pos)
        )

    except:

        return None

# =====================================================
# NEAREST LOOP
# =====================================================

def nearest_loop(position):

    best = None

    best_dist = 999

    for st in LOOPS:

        d = abs(
            ROUTE[st] - position
        )

        if d < best_dist:

            best_dist = d
            best = st

    return best

# =====================================================
# FIND OPPOSING TRAIN
# =====================================================

def find_opposing_train(
    selected,
    trains
):

    pos1 = get_live_position(selected)

    if pos1 is None:
        return None

    candidates = []

    for _, t2 in trains.iterrows():

        if (
            t2["train_no"]
            == selected["train_no"]
        ):
            continue

        if (
            t2["direction"]
            == selected["direction"]
        ):
            continue

        pos2 = get_live_position(t2)

        if pos2 is None:
            continue

        distance = abs(pos1 - pos2)

        # realistic overlap
        if distance <= 40:

            candidates.append(
                (
                    distance,
                    t2
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0]
    )

    return candidates[0][1]

# =====================================================
# HISTORICAL SCORE
# =====================================================

def historical_score(
    halted_train,
    history
):

    try:

        data = history[
            history["halted_train"]
            == halted_train
        ]

        return len(data)

    except:
        return 0

# =====================================================
# DECISION ENGINE
# =====================================================

def make_decision(
    train1,
    train2,
    history
):

    pos1 = get_live_position(train1)
    pos2 = get_live_position(train2)

    loop1 = nearest_loop(pos1)
    loop2 = nearest_loop(pos2)

    # -----------------------------------------
    # PRIORITY
    # -----------------------------------------

    p1 = PRIORITY.get(
        str(train1["type"]).upper(),
        2
    )

    p2 = PRIORITY.get(
        str(train2["type"]).upper(),
        2
    )

    # -----------------------------------------
    # PROXIMITY
    # -----------------------------------------

    prox1 = abs(
        ROUTE[loop1] - pos1
    )

    prox2 = abs(
        ROUTE[loop2] - pos2
    )

    prox_score1 = 10 - prox1
    prox_score2 = 10 - prox2

    # -----------------------------------------
    # HISTORY
    # -----------------------------------------

    h1 = historical_score(
        train1["train_no"],
        history
    )

    h2 = historical_score(
        train2["train_no"],
        history
    )

    # -----------------------------------------
    # FINAL SCORE
    # -----------------------------------------

    score1 = (
        0.45 * p1 +
        0.30 * prox_score1 +
        0.25 * h1
    )

    score2 = (
        0.45 * p2 +
        0.30 * prox_score2 +
        0.25 * h2
    )

    if score1 >= score2:

        halt = train2
        pass_train = train1

    else:

        halt = train1
        pass_train = train2

    crossing = nearest_loop(
        (pos1 + pos2) / 2
    )

    delay = round(
        abs(score1 - score2) * 2 + 4,
        1
    )

    return {

        "crossing_station": crossing,

        "halt_train": halt["train_no"],

        "pass_train": pass_train["train_no"],

        "delay": delay

    }

# =====================================================
# UI
# =====================================================

st.title(
    "🚆 RailAI Dispatch Intelligence"
)

trains = load_trains()

history = load_history()

trains = get_relevant_trains(trains)

# =====================================================
# ROUTE SELECT
# =====================================================

route = st.radio(

    "Select Direction",

    [
        "Jalna → CPSN",
        "CPSN → Jalna"
    ],

    horizontal=True

)

# DOWN
if route == "Jalna → CPSN":

    trains = trains[
        trains["direction"] == "DOWN"
    ]

# UP
else:

    trains = trains[
        trains["direction"] == "UP"
    ]

# =====================================================
# TRAIN DISPLAY
# =====================================================

for _, train in trains.iterrows():

    with st.container():

        c1, c2, c3 = st.columns(
            [4,2,1]
        )

        with c1:

            st.markdown(
                f"""
                ### 🚆 {train['train_no']}
                {train['name']}
                """
            )

        with c2:

            st.write(
                f"⏱ {train['dep_time']}"
            )

            st.write(
                f"⚡ {train['avg_speed']} km/h"
            )

        with c3:

            if st.button(
                "Analyze",
                key=str(train["train_no"])
            ):

                opposing = find_opposing_train(
                    train,
                    trains
                )

                if opposing is None:

                    st.warning(
                        "No realistic opposing train detected"
                    )

                else:

                    result = make_decision(
                        train,
                        opposing,
                        history
                    )

                    st.success(
                        "Dispatch Prediction Generated"
                    )

                    st.markdown(
                        f"""
                        ## 🚦 Dispatch Decision

                        ### ⚔️ Conflict

                        {train['train_no']}
                        ↔
                        {opposing['train_no']}

                        ---

                        ### 📍 Crossing Station

                        {result['crossing_station']}

                        ---

                        ### ⛔ Halt Train

                        {result['halt_train']}

                        ---

                        ### ✅ Passing Train

                        {result['pass_train']}

                        ---

                        ### ⏱ Predicted Delay

                        {result['delay']} min
                        """
                    )