from collections import defaultdict
import csv
import matplotlib.pyplot as plt
import math



box_scores = {}

with open("mbb-202526-pace.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        box_scores[int(row["GameId"])] = row

# -------------------------
# 1)    This section collects the necessary
#       data from the CSV and turns it into
#       a dictionary.
# -------------------------

games = []

with open("mbb-202526-stats.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        game_id_raw = str(row.get("Id", "")).strip()
        if game_id_raw == "":
            continue

        game_id = int(game_id_raw)

        if game_id not in box_scores:
            continue
        
        home_pts_raw = str(row.get("HomePoints", "")).strip()
        away_pts_raw = str(row.get("AwayPoints", "")).strip()

        if home_pts_raw == "" or away_pts_raw == "":
            continue

        box = box_scores[game_id]

        home_poss_raw = str(box.get("TeamStats Possessions", "")).strip()
        away_poss_raw = str(box.get("OpponentStats Possessions", "")).strip()

        if home_poss_raw == "" or away_poss_raw == "":
            continue

        home_points = int(float(home_pts_raw))
        away_points = int(float(away_pts_raw))
        home_poss = float(home_poss_raw)
        away_poss = float(away_poss_raw)

        games.append({
            "home": row["HomeTeam"],
            "away": row["AwayTeam"],
            "home_eff": home_points * 100 / home_poss,
            "away_eff": away_points * 100 / away_poss
        })


teams = sorted({g["home"] for g in games} | {g["away"] for g in games})

#2) Precompute a "team -> list of (opponent, point_diff)" index
# point diff is from TEAM's perspective

team_games = defaultdict(list)

for g in games:
    home, away = g["home"], g["away"]
    hp, ap = g["home_eff"], g["away_eff"]

    def adjusted_margin(margin):
        return math.copysign(math.log(abs(margin)+1), margin)-3

    # from home teams view: (hp - ap) capped at 20 and -3 for home-court advantape
    team_games[home].append((away, adjusted_margin(hp - ap)-3))

    # from away teams POV
    team_games[away].append((home, adjusted_margin(ap - hp)))

# 3) functions used by code

def average_point_diff(team: str) -> float:
    rows = team_games.get(team, [])
    if not rows:
        return 0.0
    diffs = [diff for _, diff in rows]
    return sum(diffs) / len(diffs)

def average_opponent_rating(team: str, ratings: dict[str, float]) -> float:
    rows = team_games.get(team, [])
    if not rows:
        return 0.0
    opps = [opp for opp, _ in rows]
    return sum(ratings.get(opp, 0.0) for opp in opps) / len(opps)


# 4) Interactive SRS_style rating solve

ratings = {team: 0.0 for team in teams}

for _ in range(50):
    new_ratings = {}
    for team in teams:
        avg_margin = average_point_diff(team)
        avg_opp = average_opponent_rating(team, ratings)
        new_ratings[team] = avg_margin + avg_opp
    
    mean = sum(new_ratings.values()) / len(new_ratings)
    new_ratings = {t: r - mean for t, r in new_ratings.items()}

    ratings = new_ratings

# SOS = avg opponent ratings after convergence

sos = {team: average_opponent_rating(team, ratings) for team in teams}

print("RATINGS:")
for t in sorted(teams):
    print(f"{t}: {ratings[t]: .3f}")

print("\nSOS:")
for t in sorted(teams):
    print(f"{t}: {sos[t]: .3f}")


# visualizing the data:

teams2 = list(ratings.keys())

rating_vals = [ratings[t] for t in teams2]
sos_vals = [sos[t] for t in teams]



plt.figure(figsize=(10,7))
plt.scatter(sos_vals, rating_vals)

for i, team in enumerate(teams2):
    plt.text(sos_vals[i], rating_vals[i], team)

plt.axhline(0, linestyle="--")
plt.axvline(0, linestyle="--")

plt.xlabel("Strength of Schedule")
plt.ylabel("Team Rating (Expected Goal Margin)")
plt.title("NHL Team Strength vs Strength of Schedule")

plt.show()