# Artifacts Contract & Python Interfaces

## ARTIFACTS CONTRACT
artifacts/accounts.csv columns (exact order): account_id, risk_score, baseline_score, is_fraud, typology, ring_id, then the 14 FEATURE_COLUMNS. Scores are out-of-fold, in [0,1].
artifacts/transactions.csv: txn_id, timestamp (naive ISO YYYY-MM-DDTHH:MM:SS), sender_id, receiver_id, amount_inr, typology (empty for normal).
artifacts/reasons.json: {"ACC-00412":[{"feature":str,"text":str,"shap":float,"value":float}, ...up to 3]}
artifacts/metrics.json: data_source, generated_at, seed, n_accounts, n_transactions, n_fraud_accounts, typology_counts{}, cv{scheme,n_splits}, model{name,pr_auc,pr_auc_behaviour_only}
artifacts/drift.json (stretch, optional): {"available":true,"windows":[{"window","start","end","psi","recall_frozen","recall_retrained"}],"psi_alert_threshold":0.2,"new_typology_window":str,"note":"Precomputed by offline pipeline"}
Rules: the pipeline must call validate_artifacts before finishing and must write data_source "synthetic_pipeline". Only the pipeline (Dev 1) overwrites artifacts/.

## PYTHON INTERFACES
ml.simulator.generate_dataset(n_accounts,days,seed) -> (accounts_truth[account_id,account_age_days,is_fraud,typology,ring_id], transactions[txn_id,timestamp(datetime64),sender_id,receiver_id,amount_inr,typology])
ml.features.build_features(transactions, accounts_truth) -> DataFrame indexed by account_id with exactly FEATURE_COLUMNS
ml.train_eval.cross_val_scores(features, labels, groups, feature_cols, n_splits=5, seed=42, return_contribs=False) -> (oof_scores: Series, oof_contribs: DataFrame|None) with SHAP values from XGBoost pred_contribs (bias column dropped, columns = feature_cols)
ml.explain.build_reasons(features, contribs, top_k=3) -> {account_id: [{"feature","text","shap","value"}]} using only positive-SHAP features sorted by shap desc
ml.run_pipeline.run(out_dir="artifacts", seed=42, n_accounts=3000, days=30)
