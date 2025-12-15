import os
import csv
import requests
from datetime import datetime, timezone

ZENLOOP_BASE = "https://api.zenloop.com/external_app/v1"  # :contentReference[oaicite:1]{index=1}

def zl_get(path, api_key, params=None):
    params = params or {}
    params["api_key"] = api_key  # external_app API nutzt api_key als Query Param :contentReference[oaicite:2]{index=2}
    r = requests.get(
        ZENLOOP_BASE + path,
        headers={"accept": "application/json"},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def list_all_surveys(api_key):
    surveys = []
    page = 1
    while True:
        data = zl_get("/surveys", api_key, params={"page": page})  # :contentReference[oaicite:3]{index=3}
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

def get_survey_summary(api_key, survey_id, date_shortcut):
    # GET /surveys/{survey_id}?date_shortcut=... :contentReference[oaicite:4]{index=4}
    return zl_get(f"/surveys/{survey_id}", api_key, params={"date_shortcut": date_shortcut})

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def main():
    api_key = os.environ["ZENLOOP_API_TOKEN"]  # wir verwenden deinen Token als api_key Param

    now = datetime.now(timezone.utc).date().isoformat()

    surveys = list_all_surveys(api_key)

    total_all_time = 0
    weighted_nps_sum = 0.0
    weekly_new = 0

    for s in surveys:
        # in der List-Response steht public_hash_id (als Survey-ID) :contentReference[oaicite:5]{index=5}
        sid = s.get("public_hash_id") or s.get("id")
        if not sid:
            continue

        all_time = get_survey_summary(api_key, sid, "all_time")
        last_7d = get_survey_summary(api_key, sid, "last_7_days")  # erlaubter date_shortcut :contentReference[oaicite:6]{index=6}

        survey_all = all_time.get("survey", {})
        survey_7d = last_7d.get("survey", {})

        n_responses_all = int(survey_all.get("number_of_responses", 0))
        n_responses_7d = int(survey_7d.get("number_of_responses", 0))

        nps_obj = survey_all.get("nps", {})
        nps_score = safe_float(nps_obj.get("percentage"))  # NPS score :contentReference[oaicite:7]{index=7}

        total_all_time += n_responses_all
        weekly_new += n_responses_7d

        if nps_score is not None and n_responses_all > 0:
            weighted_nps_sum += nps_score * n_responses_all

    overall_score = round(weighted_nps_sum / total_all_time, 2) if total_all_time > 0 else None

    with open("weekly_summary_zenloop.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_at", "source", "scope", "weekly_new", "total_feedbacks", "overall_score"])
        w.writerow([now, "zenloop", "ALL", weekly_new, total_all_time, overall_score])

if __name__ == "__main__":
    main()
