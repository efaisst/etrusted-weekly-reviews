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

def get_weekly_count(token, survey_id):
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    data = zl_get(
        f"/surveys/{survey_id}/answers",
        token,
        params={"date_from": since, "per_page": 1},
    )
    return int((data.get("meta") or {}).get("total", 0))

def get_survey_totals(token, survey_id):
    data = zl_get(f"/surveys/{survey_id}", token, params={"date_shortcut": "all_time"})
    survey = data.get("survey", {})
    total = int(survey.get("number_of_responses", 0))
    nps = (survey.get("nps") or {}).get("percentage")
    return total, nps

def main():
    token = os.environ["ZENLOOP_API_TOKEN"]
    run_at = datetime.now(timezone.utc).date().isoformat()

    surveys = zl_get("/surveys", token).get("surveys", [])

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
            sid = s.get("id")
            name = s.get("name", sid)

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
