import os
import csv
import requests
from datetime import datetime, timezone

ZENLOOP_BASE = "https://api.zenloop.com/external_app/v1"  # :contentReference[oaicite:1]{index=1}

def zl_get(path, token, params=None):
    r = requests.get(
        ZENLOOP_BASE + path,
        headers={
            "Authorization": f"Bearer {token}",  # :contentReference[oaicite:2]{index=2}
            "accept": "application/json",
        },
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def list_all_surveys(token):
    surveys = []
    page = 1
    while True:
        data = zl_get("/surveys", token, params={"page": page})  # :contentReference[oaicite:3]{index=3}
        surveys.extend(data.get("surveys", []))
        meta = data.get("meta", {})
        total = meta.get("total")
        per_page = meta.get("per_page")
        if not total or not per_page:
            break
        if page * per_page >= total:
            break
        page += 1
    return surveys

def get_survey_summary(token, survey_id, date_shortcut):
    return zl_get(f"/surveys/{survey_id}", token, params={"date_shortcut": date_shortcut})  # :contentReference[oaicite:4]{index=4}

def main():
    token = os.environ["ZENLOOP_API_TOKEN"]

    run_at = datetime.now(timezone.utc).date().isoformat()

    surveys = list_all_surveys(token)

    total_all_time = 0
    weighted_nps_sum = 0.0
    weekly_new = 0

    for s in surveys:
        sid = s.get("public_hash_id") or s.get("id")  # :contentReference[oaicite:5]{index=5}
        if not sid:
            continue

        all_time = get_survey_summary(token, sid, "all_time")
        last_7d = get_survey_summary(token, sid, "last_7_days")

        survey_all = all_time.get("survey", {})
        survey_7d = last_7d.get("survey", {})

        n_all = int(survey_all.get("number_of_responses", 0))  # :contentReference[oaicite:6]{index=6}
        n_7d = int(survey_7d.get("number_of_responses", 0))

        nps = (survey_all.get("nps") or {}).get("percentage")  # :contentReference[oaicite:7]{index=7}
        nps_score = float(nps) if nps is not None else None

        total_all_time += n_all
        weekly_new += n_7d

        if nps_score is not None and n_all > 0:
            weighted_nps_sum += nps_score * n_all

    overall_score = round(weighted_nps_sum / total_all_time, 2) if total_all_time > 0 else None

    with open("weekly_summary_zenloop.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_at", "source", "scope", "weekly_new", "total_feedbacks", "overall_score"])
        w.writerow([run_at, "zenloop", "ALL", weekly_new, total_all_time, overall_score])

if __name__ == "__main__":
    main()
