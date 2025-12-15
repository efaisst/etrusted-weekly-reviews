import os
import csv
import requests
from datetime import datetime, timedelta, timezone

ZENLOOP_BASE = "https://api.zenloop.com/v1"

def zl_get(path, token, params=None):
    r = requests.get(
        ZENLOOP_BASE + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def main():
    token = os.environ["ZENLOOP_API_TOKEN"]

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=7)).isoformat().replace("+00:00", "Z")

    metrics = zl_get("/metrics", token)
    overall_score = metrics.get("nps") or metrics.get("csat")
    total_feedbacks = metrics.get("responses_count")

    responses = zl_get(
        "/responses",
        token,
        params={"submitted_after": since, "per_page": 1},
    )
    weekly_new = responses.get("total", 0)

    with open("weekly_summary_zenloop.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_at",
            "source",
            "scope",
            "weekly_new",
            "total_feedbacks",
            "overall_score",
        ])
        writer.writerow([
            now.date().isoformat(),
            "zenloop",
            "ALL",
            weekly_new,
            total_feedbacks,
            overall_score,
        ])

if __name__ == "__main__":
    main()
