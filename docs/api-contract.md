# API Contract

All routes under `/api`, all GET, JSON snake_case, floats rounded to 4 decimals. Error envelope for every failure: `{"error":{"code":str,"message":str,"details":object}}`.
Error codes: `ACCOUNT_NOT_FOUND` 404; `NOT_FOUND` 404; `METHOD_NOT_ALLOWED` 405; `VALIDATION_ERROR` 422 (wrong parameter types); `INVALID_BUDGET` 422 (budget not in 1-1000); `INVALID_HOPS` 422 (not 1 or 2); `INVALID_MAX_NODES` 422 (not in 5-100); `ARTIFACTS_NOT_FOUND` 503; `INTERNAL_ERROR` 500; `NOT_IMPLEMENTED` 501 (skeleton stubs only).
Declare budget, hops and max_nodes as int query params (type errors give VALIDATION_ERROR); range checks are done in the service so the specific code is returned.

## Endpoints

### GET /api/health
`{"status":"ok","service":"mulenet-api","version":"1.0.0","artifacts_loaded":bool,"data_source":str|null,"generated_at":str|null}`

### GET /api/summary
`{"data_source","generated_at","seed","dataset":{"n_accounts","n_transactions","n_fraud_accounts","fraud_rate","typology_counts":{}},"model":{"name","cv_scheme","cv_splits","pr_auc","pr_auc_behaviour_only"}}`

### GET /api/alerts?budget=100 (default 100)
`{"budget":int,"budget_summary":{"alerts_returned","true_frauds_caught","false_alerts","total_frauds","recall","precision","false_alerts_per_1000_accounts","behaviour_only_true_frauds_caught"},"alerts":[{"rank":int,"account_id":str,"risk_score":float,"top_reason":str,"ground_truth_fraud":bool,"true_typology":str|null}]}`. Order: risk_score desc, ties account_id asc. top_reason = first reason text or "No strong risk indicators". behaviour_only_true_frauds_caught uses baseline_score with the same budget and tie rule. false_alerts_per_1000_accounts = false_alerts / n_accounts * 1000.

### GET /api/accounts/{account_id}
`{"account_id","rank","risk_score","baseline_score","ground_truth_fraud","true_typology":str|null,"ring_id":str|null,"reasons":[{"feature","text","shap","value"}],"features":{14 FEATURE_COLUMNS: number}}`. rank = 1-based position over all accounts by the alert ordering.

### GET /api/accounts/{account_id}/graph?hops=1&max_nodes=40
`{"center_id","hops","truncated":bool,"nodes":[{"id","risk_score","ground_truth_fraud","is_center"}],"edges":[{"source","target","txn_count","total_amount_inr","first_ts","last_ts"]}`. Center always included; counterparties ranked by total amount with the center; hops=2 adds counterparties of neighbours the same way until max_nodes; edges directed sender->receiver, aggregated per pair, only between included nodes; truncated true if any candidate was dropped.

### GET /api/budget-curve
`{"budgets":[int],"total_frauds":int,"total_accounts":int,"full":{"true_frauds_caught":[int],"false_alerts":[int],"recall":[float]},"behaviour_only":{same}}`. Budgets 10..300 step 10, capped at n_accounts. Computed by the backend from accounts.csv with common.metrics.budget_metrics.

### GET /api/drift
`{"available":false}` if drift.json is absent, else its contents.

Data endpoints (all except /health) return 503 ARTIFACTS_NOT_FOUND when the store is not loaded.
