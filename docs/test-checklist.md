# Acceptance Checklist

- [x] 1. Clean clone: `pip install`, `pytest`, backend starts, `npm install`, `npm run build`.
- [x] 2. Pipeline runs from a clean checkout, `validate_artifacts` passes, same seed gives identical `accounts.csv`.
- [x] 3. Badge shows `SYNTHETIC` in the final demo.
- [x] 4. Budget slider values match `/api/alerts`.
- [x] 5. Comparison chart and PR-AUC match `/summary`.
- [x] 6. Every alert shows 1-3 readable reasons.
- [x] 7. Connection map renders for the top 10 alerts.
- [x] 8. Error codes: unknown account (404), budget=0 (422), budget=abc (422).
- [x] 9. Backend-offline banner appears when API is unreachable.
- [x] 10. Every component is mounted from App.jsx (no orphans).
- [x] 11. No horizontal scroll at 375px width.
- [x] 12. Ground truth appears only under "demo evaluation" labels.
