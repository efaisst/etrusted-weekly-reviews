# Weekly Review Monitoring

Automatisiertes wöchentliches Monitoring von Kundenfeedback-Tools.

## Aktuell aktiv
- **Zenloop**
  - Gesamtübersicht (weekly_summary_zenloop.csv)
  - Einzelne NPS-Surveys (weekly_summary_zenloop_surveys.csv)

## Architektur
- GitHub Actions (1× pro Woche)
- Python-Skripte pro Tool
- CSV-Exports im Repository
- Google Sheets via IMPORTDATA()

## Erweiterbar
- Trusted Shops (vorbereitet)
- Weitere Review- oder Feedback-Tools möglich
