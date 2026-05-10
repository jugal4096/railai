from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
import pandas as pd

from datetime import datetime

import random

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

SECTIONS = [
    ("Jalna", "Dinagaon"),
    ("Dinagaon", "Badnapur"),
    ("Badnapur", "Karmad"),
    ("Karmad", "Chikalthana"),
    ("Chikalthana", "CPSN")
]

# =====================================================
# PRIORITY
# =====================================================

PRIORITY = {
    "VB": 5,
    "SF": 4,
    "JSHTB": 4,
    "SKR": 4,
    "EXP": 3,
    "DEMU": 2,
    "PASS": 1
}

# =====================================================
# HISTORY
# =====================================================

try:

    history = pd.read_csv(
        "final_clean_all_trains_dataset.csv"
    )

except:

    history = pd.DataFrame()

# =====================================================
# RUNNING TODAY
# =====================================================

def running_today(row):

    try:

        day = datetime.now().weekday()

        mapping = {
            0: row["runs_mon"],
            1: row["runs_tue"],
            2: row["runs_wed"],
            3: row["runs_thu"],
            4: row["runs_fri"],
            5: row["runs_sat"],
            6: row["runs_sun"],
        }

        return mapping[day] == 1

    except:

        return True

# =====================================================
# LOAD TRAINS
# =====================================================

def get_trains():

    conn = sqlite3.connect(
        "trains.db"
    )

    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM trains"
    )

    rows = cur.fetchall()

    conn.close()

    trains = []

    for r in rows:

        if not running_today(r):
            continue

        try:

            raw_dir = str(
                r["direction"]
            ).upper()

            if raw_dir == "UP":

                direction = "reverse"

            else:

                direction = "forward"

            trains.append({

                "train_no":
                str(r["train_no"]),

                "name":
                r["name"],

                "type":
                str(r["type"]).upper(),

                "source":
                r["source"],

                "destination":
                r["destination"],

                "departure_time":
                r["dep_time"],

                "arrival_time":
                r["arr_time"],

                "speed":
                float(r["avg_speed"]),

                "direction":
                direction

            })

        except Exception as e:

            print(e)

    return trains

# =====================================================
# REAL-TIME POSITION ENGINE
# =====================================================

def get_live_position(train):

    try:

        now = datetime.now()

        current_minutes = (
            now.hour * 60 +
            now.minute
        )

        # departure

        dh, dm = map(
            int,
            train["departure_time"]
            .split(":")
        )

        dep_minutes = (
            dh * 60 + dm
        )

        # arrival

        ah, am = map(
            int,
            train["arrival_time"]
            .split(":")
        )

        arr_minutes = (
            ah * 60 + am
        )

        # midnight handling

        if arr_minutes < dep_minutes:

            arr_minutes += 1440

        if current_minutes < dep_minutes:

            current_minutes += 1440

        # elapsed

        elapsed = (
            current_minutes -
            dep_minutes
        )

        journey_duration = (
            arr_minutes -
            dep_minutes
        )

        # inactive train

        if elapsed < 0:
            return None

        if elapsed > journey_duration:
            return None

        # journey ratio

        ratio = (
            elapsed /
            journey_duration
        )

        # simulated realtime randomness

        noise = random.uniform(
            -1.5,
            1.5
        )

        distance = (
            ratio * 70
        ) + noise

        if train["direction"] == "forward":

            pos = distance

        else:

            pos = 70 - distance

        return round(
            max(0, min(70, pos)),
            2
        )

    except:

        return None

# =====================================================
# SECTION
# =====================================================

def get_section(position):

    for s1, s2 in SECTIONS:

        km1 = ROUTE[s1]
        km2 = ROUTE[s2]

        if km1 <= position <= km2:

            return {

                "name":
                f"{s1} ↔ {s2}",

                "start":
                s1,

                "end":
                s2

            }

    return None

# =====================================================
# NEXT LOOP
# =====================================================

def next_loop(train, position):

    try:

        if train["direction"] == "forward":

            for st in LOOPS:

                if ROUTE[st] > position:

                    return st

        else:

            for st in reversed(LOOPS):

                if ROUTE[st] < position:

                    return st

        return None

    except:

        return None

# =====================================================
# ETA
# =====================================================

def eta_to_loop(
    train,
    position,
    loop
):

    dist = abs(
        ROUTE[loop] - position
    )

    eta = (
        dist / train["speed"]
    ) * 60

    return round(eta, 1)

# =====================================================
# HISTORY SCORE
# =====================================================

def history_score(train_no):

    try:

        data = history[
            history["halted_train"]
            == int(train_no)
        ]

        return len(data)

    except:

        return 0

# =====================================================
# REAL CONFLICT ENGINE
# =====================================================

def find_conflict(
    selected,
    trains
):

    pos1 = get_live_position(selected)

    if pos1 is None:
        return None

    loop1 = next_loop(
        selected,
        pos1
    )

    if loop1 is None:
        return None

    eta1 = eta_to_loop(
        selected,
        pos1,
        loop1
    )

    candidates = []

    for t2 in trains:

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

        loop2 = next_loop(
            t2,
            pos2
        )

        if loop2 is None:
            continue

        eta2 = eta_to_loop(
            t2,
            pos2,
            loop2
        )

        # realistic conflict zone

        same_zone = abs(
            pos1 - pos2
        ) <= 25

        eta_gap = abs(
            eta1 - eta2
        )

        if same_zone and eta_gap <= 20:

            candidates.append({

                "train":
                t2,

                "loop":
                loop1,

                "eta_gap":
                eta_gap,

                "distance":
                abs(pos1 - pos2)

            })

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x["eta_gap"],
            x["distance"]
        )
    )

    return candidates[0]

# =====================================================
# DISPATCH ENGINE
# =====================================================

def dispatch_decision(
    train1,
    train2,
    crossing_loop
):

    pos1 = get_live_position(train1)
    pos2 = get_live_position(train2)

    # priority

    p1 = PRIORITY.get(
        train1["type"],
        2
    )

    p2 = PRIORITY.get(
        train2["type"],
        2
    )

    # proximity

    prox1 = abs(
        ROUTE[crossing_loop]
        - pos1
    )

    prox2 = abs(
        ROUTE[crossing_loop]
        - pos2
    )

    # history

    h1 = history_score(
        train1["train_no"]
    )

    h2 = history_score(
        train2["train_no"]
    )

    # score

    score1 = (
        0.45 * p1 +
        0.30 * (10 - prox1) +
        0.25 * h1
    )

    score2 = (
        0.45 * p2 +
        0.30 * (10 - prox2) +
        0.25 * h2
    )

    if score1 >= score2:

        halt = train2
        pass_train = train1

    else:

        halt = train1
        pass_train = train2

    delay = round(
        abs(score1 - score2) * 2 + 4,
        1
    )

    return {

        "halt_train":
        halt["train_no"],

        "pass_train":
        pass_train["train_no"],

        "delay":
        delay,

        "confidence":
        round(

            (
                max(score1, score2)
                /
                (score1 + score2)
            ) * 100,

            1
        )

    }

# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():

    return {

        "message":
        "RailAI Realtime Dispatch Running"

    }

# =====================================================
# TRAINS
# =====================================================

@app.get("/trains")
def trains():

    active = []

    for t in get_trains():

        pos = get_live_position(t)

        if pos is not None:

            t["position"] = pos

            active.append(t)

    return active

# =====================================================
# PREDICT
# =====================================================

@app.get("/predict/{train_no}")
def predict(train_no: str):

    trains = get_trains()

    selected = None

    for t in trains:

        if t["train_no"] == train_no:

            selected = t
            break

    if not selected:

        return {
            "error":
            "Train not found"
        }

    pos1 = get_live_position(selected)

    if pos1 is None:

        return {

            "message":
            "Train not active currently"

        }

    section = get_section(pos1)

    next_station = next_loop(
        selected,
        pos1
    )

    if next_station is None:

        return {

            "message":
            "Train near terminal"

        }

    eta = eta_to_loop(
        selected,
        pos1,
        next_station
    )

    conflict = find_conflict(
        selected,
        trains
    )

    # NO CONFLICT

    if conflict is None:

        return {

            "selected_train":
            selected["train_no"],

            "selected_name":
            selected["name"],

            "current_section":
            section["name"],

            "current_position":
            pos1,

            "next_loop":
            next_station,

            "distance_to_loop":
            round(
                abs(
                    ROUTE[next_station]
                    - pos1
                ),
                1
            ),

            "eta_to_loop":
            eta,

            "message":
            "No opposing train conflict detected"

        }

    opposing = conflict["train"]

    decision = dispatch_decision(
        selected,
        opposing,
        conflict["loop"]
    )

    return {

        "selected_train":
        selected["train_no"],

        "selected_name":
        selected["name"],

        "current_section":
        section["name"],

        "current_position":
        pos1,

        "next_loop":
        next_station,

        "distance_to_loop":
        round(
            abs(
                ROUTE[next_station]
                - pos1
            ),
            1
        ),

        "eta_to_loop":
        eta,

        "opposing_train":
        opposing["train_no"],

        "opposing_name":
        opposing["name"],

        "opposing_position":
        get_live_position(opposing),

        "crossing_station":
        conflict["loop"],

        "halt_train":
        decision["halt_train"],

        "pass_train":
        decision["pass_train"],

        "predicted_delay":
        decision["delay"],

        "confidence":
        decision["confidence"]

    }