import os
import csv
import requests
from datetime import datetime, timedelta, timezone

ZENLOOP_BASE = "https://api.zenloop.com/v1"  # :contentReference[oaicite:2]{index=2}

def zl_get(path, token, params=None):
    r = requests.get(
        ZENLOOP_BASE + path,
        headers={
            "Authorization": f"Bearer {token}",  # :contentReference[oaicite:3]{index=3}
            "accept": "application/json",
        },
        params=params,
        timeout=30,
    )
    # Damit wir beim nächsten Fehler sofort mehr sehen als nur "403":
    if r.status_code >= 400:
        raise RuntimeError(f"Zenloop API error {r.status_code}: {r.text}")
    return r.json()

def list_all_surveys(token):
    surveys = []
    page = 1
    while True:
        data = zl_get("/surveys", token, params={"page": page})  # :contentReference[oaicite:4]{index=4}
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

def get_answers_count_last_7d(token, survey_id):
    # Wir zählen nicht alle Antworten, sondern holen nur "total" via per_page=1
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
    data = zl_get(
        f"/surveys/{survey_id}/answers",
        token,
        params={"date_from": since, "page": 1, "per_page": 1},
    )
    return int((data.get("meta") or {}).get("total", 0))

def get_overall_nps_and_total(token, survey_id):
    # Summary eines Surveys: enthält u.a. number_of_responses und NPS-Objekt (je nach Account)
    data = zl_get(f"/surveys/{survey_id}", token, params={"date_shortcut": "all_time"})
    survey = data.get("survey", {})
    total = int(survey.get("number_of_responses", 0))
    nps = (survey.get("nps") or {}).get("percentage")
    nps_score = float(nps) if nps is not None else None
    return nps_score, total

def main():
    token = os.environ["ZENLOOP_API_TOKEN"]
    run_at = datetime.now(timezone.utc).date().isoformat()

    surveys = list_all_surveys(token)

    weekly_new = 0
    total_all = 0
    weighted_sum = 0.0

    for s in surveys:
        sid = s.get("id") or s.get("public_hash_id")  # Doku zeigt Bearer-Auth /v1/surveys :contentReference[oaicite:5]{index=5}
        if not sid:
            continue

        nps_score, total = get_overall_nps_and_total(token, sid)
        weekly = get_answers_count_last_7d(token, sid)

        weekly_new += weekly
        total_all += total
        if nps_score is not None and total > 0:
            weighted_sum += nps_score * total

    overall_score = round(weighted_sum / total_all, 2) if total_all > 0 else None

    with open("weekly_summary_zenloop.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_at", "source", "scope", "weekly_new", "total_feedbacks", "overall_score"])
        w.writerow([run_at, "zenloop", "ALL", weekly_new, total_all, overall_score])

if __name__ == "__main__":
    main()
