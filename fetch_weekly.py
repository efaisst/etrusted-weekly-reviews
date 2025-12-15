import os
import csv
import requests
from datetime import datetime, timedelta, timezone

TOKEN_URL = "https://login.etrusted.com/oauth/token"
API_BASE = "https://api.etrusted.com"

def get_token():
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["ETRUSTED_CLIENT_ID"],
            "client_secret": os.environ["ETRUSTED_CLIENT_SECRET"],
            "audience": "https://api.etrusted.com",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def api_get(path, token, params=None):
    r = requests.get(
        API_BASE + path,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def main():
    token = get_token()

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    until = now.isoformat().replace("+00:00", "Z")

    channels = api_get("/channels", token)

    rows = []
    total_new = 0
    total_reviews = 0
    weighted_sum = 0.0

    for ch in channels:
        cid = ch["id"]
        name = ch.get("name", cid)

        count_total = api_get("/reviews/count", token, params={"channels": [cid]})["count"]
        count_week = api_get(
            "/reviews/count",
            token,
            params={"channels": [cid], "submittedAfter": since, "submittedBefore": until},
        )["count"]

        agg = api_get(f"/channels/{cid}/service-reviews/aggregate-rating", token)
        overall = agg["overall"]["rating"]

        rows.append([
            now.date().isoformat(),
            name,
            count_week,
            count_total,
            overall,
        ])

        total_new += count_week
        total_reviews += count_total
        weighted_sum += overall * count_total

    if total_reviews > 0:
        rows.append([
            now.date().isoformat(),
            "ALL",
            total_new,
            total_reviews,
            round(weighted_sum / total_reviews, 2),
        ])

    with open("weekly_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run_at", "channel", "weekly_new", "total_reviews", "overall_rating"])
        writer.writerows(rows)

if __name__ == "__main__":
    main()
