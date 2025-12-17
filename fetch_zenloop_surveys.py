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
            "accept": "application/json",
        },
        params=params,
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text}")
    return r.json()

def list_all_surveys(token):
    """Fetch ALL surveys using pagination."""
    surveys = []
    page = 1

    while True:
        data = zl_get("/surveys", token, params={"page": page})
        page_surveys = data.get("surveys", [])
        surveys.extend(page_surveys)

        meta = data.get("meta", {}) or {}
        total = meta.get("total")
        per_page = meta.get("per_page")

        # If API doesn't return paging meta, stop.
        if not total or not per_page:
            break

        # Stop when we've fetched all items.
        if page * per_page >= total:
            break

        page += 1

    return surveys

def get_weekly_count(token, survey_id):
    """Count answers in the last 7 days (fast: per_page=1 and read meta.total)."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    data = zl_get(
        f"/surveys/{survey_id}/answers",
        token,
        params={"date_from": since, "page": 1, "per_page": 1},
    )
    return int((data.get("meta") or {}).get("total", 0))

def get_survey_totals(token, survey_id):
    """Get all-time totals + NPS."""
    data = zl_get(f"/surveys/{survey_id}", token, params={"date_shortcut": "all_time"})
    survey = data.get("survey", {}) or {}
    total = int(survey.get("number_of_responses", 0))
    nps = (survey.get("nps") or {}).get("percentage")
    return total, nps

def main():
    token = os.environ["ZENLOOP_API_TOKEN"]
    run_at = datetime.now(timezone.utc).date().isoformat()

    surveys = list_all_surveys(token)

    with open("weekly_summary_zenloop_surveys.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_at",
            "source",
            "survey_id",
            "survey_name",
            "weekly_new",
            "total_feedbacks",
            "nps",
        ])

        for s in surveys:
            sid = s.get("public_hash_id") or s.get("id")
            if not sid:
                continue

            name = s.get("name") or s.get("title") or sid

            weekly = get_weekly_count(token, sid)
            total, nps = get_survey_totals(token, sid)

            writer.writerow([
                run_at,
                "zenloop",
                sid,
                name,
                weekly,
                total,
                nps,
            ])

if __name__ == "__main__":
    main()
