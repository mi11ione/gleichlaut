"""(Re)write claims.tsv from the registry below: every claim names its source file, a path in it, a format and the command
that produces the source. tools/claims.py then checks the values against the sources and scans the documents.
usage: python3 tools/build_claims.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from claims import get

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RE = "PYTHONPATH=src python3 -m gleichlaut.replay --write"
BT = "PYTHONPATH=src python3 -m gleichlaut.backtest --hist <2026 snapshots> --wb2025 <2025 XML>"
FS = "PYTHONPATH=src python3 -m gleichlaut.fed.score"
HAND = "hand-entered from the cited source (see note in file)"
F, A = "eval/results/fresh166.json", "summary.all."
C = [  # id, source, path, fmt, command
 ("fresh_n", F, A + "n", "{}", RE), ("fresh_exact", F, A + "exact.model", "{:.1f}", RE), ("fresh_rules", F, A + "exact.rules", "{:.1f}", RE),
 ("fresh_delta", F, A + "exact.delta", "{:+.1f}", RE), ("fresh_delta_plain", F, A + "exact.delta", "{:.1f}", RE),
 ("fresh_ci_lo", F, A + "exact.ci95.0", "{:.1f}", RE), ("fresh_ci_hi", F, A + "exact.ci95.1", "{:.1f}", RE),
 ("fresh_flag", F, A + "flag_rate", "{:.1f}", RE), ("fresh_ready", F, A + "ready_rate", "{:.1f}", RE),
 ("fresh_ready_n", F, A + "unflagged", "{}", RE), ("fresh_wilson_hi", F, A + "wilson95_unflagged_real.1", "{:.1f}", RE), ("fresh_wilson_ready_hi", F, A + "wilson95_severe_among_ready.1", "{:.1f}", RE),
 ("fresh_reasked", F, A + "reasked", "{}", RE), ("fresh_replaced", F, A + "replaced", "{}", RE),
 ("fresh_families", F, A + "families", "{}", RE), ("fresh_pairs", F, A + "pairs", "{}", RE),
 ("unseen_n", F, "summary.unseen families.n", "{}", RE), ("unseen_exact", F, "summary.unseen families.exact.model", "{:.1f}", RE),
 ("unseen_delta", F, "summary.unseen families.exact.delta", "{:+.1f}", RE),
 ("unseen_ci_lo", F, "summary.unseen families.exact.ci95.0", "{:.1f}", RE), ("unseen_ci_hi", F, "summary.unseen families.exact.ci95.1", "{:.1f}", RE),
 ("unseen_flag", F, "summary.unseen families.flag_rate", "{:.1f}", RE), ("unseen_ready", F, "summary.unseen families.ready_rate", "{:.1f}", RE),
 ("exfam_n", F, "summary.excluding family 981f07a8.n", "{}", RE), ("exfam_exact", F, "summary.excluding family 981f07a8.exact.model", "{:.1f}", RE),
 ("exfam_delta", F, "summary.excluding family 981f07a8.exact.delta", "{:+.1f}", RE),
 ("exfam_ci_lo", F, "summary.excluding family 981f07a8.exact.ci95.0", "{:.1f}", RE),
 ("exfam_ci_hi", F, "summary.excluding family 981f07a8.exact.ci95.1", "{:.1f}", RE),
 ("exfam_flag", F, "summary.excluding family 981f07a8.flag_rate", "{:.1f}", RE), ("exfam_ready", F, "summary.excluding family 981f07a8.ready_rate", "{:.1f}", RE),
 ("flagged_sample_good", F, "summary.flagged_sample.good", "{}", RE), ("flagged_sample_n", F, "summary.flagged_sample.n", "{}", RE),
 ("flagged_sample_lo", F, "summary.flagged_sample.wilson95.0", "{:.1f}", RE), ("flagged_sample_hi", F, "summary.flagged_sample.wilson95.1", "{:.1f}", RE),
 ("oos_n", "eval/results/oos242.json", A + "n", "{}", RE), ("oos_exact", "eval/results/oos242.json", A + "exact.model", "{:.1f}", RE),
 ("oos_delta", "eval/results/oos242.json", A + "exact.delta", "{:+.1f}", RE),
 ("oos_ci_lo", "eval/results/oos242.json", A + "exact.ci95.0", "{:.1f}", RE), ("oos_ci_hi", "eval/results/oos242.json", A + "exact.ci95.1", "{:.1f}", RE),
 ("oos_flag", "eval/results/oos242.json", A + "flag_rate", "{:.1f}", RE), ("oos_ready", "eval/results/oos242.json", A + "ready_rate", "{:.1f}", RE),
 ("oos_german_pct", "eval/results/oos242.json", A + "unflagged_german_per100", "{:.1f}", RE),
 ("oos_german_n", "eval/results/oos242.json", A + "unflagged_german", "{}", RE),
 ("d8_n", "eval/results/dev120_8b.json", A + "n", "{}", RE), ("d8_exact", "eval/results/dev120_8b.json", A + "exact.model", "{:.1f}", RE),
 ("d8_delta", "eval/results/dev120_8b.json", A + "exact.delta", "{:+.1f}", RE),
 ("d8_ci_lo", "eval/results/dev120_8b.json", A + "exact.ci95.0", "{:.1f}", RE), ("d8_ci_hi", "eval/results/dev120_8b.json", A + "exact.ci95.1", "{:.1f}", RE),
 ("d8_flag", "eval/results/dev120_8b.json", A + "flag_rate", "{:.1f}", RE), ("d8_ready", "eval/results/dev120_8b.json", A + "ready_rate", "{:.1f}", RE),
 ("d70_exact", "eval/results/dev120.json", A + "exact.model", "{:.1f}", RE), ("d70_delta", "eval/results/dev120.json", A + "exact.delta", "{:+.1f}", RE),
 ("d70_rules", "eval/results/dev120.json", A + "exact.rules", "{:.1f}", RE),
 ("free_exact", "eval/results/naive.json", "8B free translation of the new DE.exact", "{:.1f}", RE),
 ("free_flips", "eval/results/naive.json", "8B free translation of the new DE.lexicon_flips", "{}", RE),
 ("w8_flag", "eval/results/naive.json", "8B window-only (locked span edit).flagged", "{:.1f}", RE),
 ("cost_calls", "eval/results/cost_fresh166.json", "unique_calls", "{}", RE),
 ("cost_secs", "eval/results/cost_fresh166.json", "model_secs_per_item", "{:.2f}", RE),
 ("ag_agree", "eval/results/agreement_fresh166.json", "agree", "{}", RE), ("ag_n", "eval/results/agreement_fresh166.json", "n", "{}", RE),
 ("ag_kappa", "eval/results/agreement_fresh166.json", "kappa", "{:.3f}", RE),
 ("tie_n", "eval/results/agreement_fresh166.json", "tiebreak.disagreements", "{}", RE),
 ("tie_sided", "eval/results/agreement_fresh166.json", "tiebreak.third_sided_with_second", "{}", RE),
 ("tie_fix", "eval/results/agreement_fresh166.json", "tiebreak.final_unflagged_needs_fix", "{}", RE),
 ("ag_unfl_n", "eval/results/agreement_fresh166.json", "unflagged_n", "{}", RE),
 ("eco_per_month", "eval/results/economics.json", "de_changes_per_month", "{:.1f}", RE),
 ("eco_changes", "eval/results/economics.json", "de_changes", "{}", RE), ("eco_months", "eval/results/economics.json", "span_months", "{:.1f}", RE),
 ("eco_chf_item", "eval/results/economics.json", "chf_per_item_infomaniak", "{:.4f}", RE),
 ("eco_x1_items", "eval/results/economics.json", "x1.items_per_month", "{}", RE), ("eco_x10_items", "eval/results/economics.json", "x10.items_per_month", "{}", RE),
 ("eco_x1_usd", "eval/results/economics.json", "x1.usd_per_month_publicai", "{:.2f}", RE),
 ("eco_x10_usd", "eval/results/economics.json", "x10.usd_per_month_publicai", "{:.2f}", RE),
 ("eco_x1_chf", "eval/results/economics.json", "x1.chf_per_month_infomaniak", "{:.2f}", RE),
 ("eco_x10_chf", "eval/results/economics.json", "x10.chf_per_month_infomaniak", "{:.2f}", RE),
 ("eco_x1_h", "eval/results/economics.json", "x1.model_hours_per_month_sequential", "{:.1f}", RE),
 ("eco_x10_h", "eval/results/economics.json", "x10.model_hours_per_month_sequential", "{:.1f}", RE),
 ("fed_rules", "eval/results/fedlex_compare.json", "rules_exact_pct", "{:.1f}", RE),
 ("fed8_exact", "eval/results/fedlex_compare.json", "8b_mlx_dwq.exact_pct", "{:.1f}", RE),
 ("fed8_exact_n", "eval/results/fedlex_compare.json", "8b_mlx_dwq.exact", "{}", RE),
 ("fed8_flag", "eval/results/fedlex_compare.json", "8b_mlx_dwq.flag_rate", "{:.1f}", RE),
 ("fed8_ready_pct", "eval/results/fedlex_compare.json", "8b_mlx_dwq.ready", "{}", RE),
 ("fed8_su", "eval/results/fedlex_compare.json", "8b_mlx_dwq.unflagged_stale_untranslated", "{}", RE),
 ("fed8_su_pct", "eval/results/fedlex_compare.json", "8b_mlx_dwq.unflagged_stale_untranslated_pct", "{:.1f}", RE),
 ("fed8_flagged_n", "eval/results/fedlex_compare.json", "8b_mlx_dwq.flagged", "{}", RE),
 ("fed70_exact", "eval/results/fedlex_compare.json", "70b.exact_pct", "{:.1f}", RE),
 ("fed70_exact_n", "eval/results/fedlex_compare.json", "70b.exact", "{}", RE),
 ("fed70_flag", "eval/results/fedlex_compare.json", "70b.flag_rate", "{:.1f}", RE),
 ("fed70_flagged_n", "eval/results/fedlex_compare.json", "70b.flagged", "{}", RE),
 ("fed70_ready", "eval/results/fedlex_compare.json", "70b.ready", "{}", RE),
 ("fed70_real", "eval/results/fedlex_compare.json", "70b.unflagged_real", "{}", RE),
 ("fed70_real_pct", "eval/results/fedlex_compare.json", "70b.unflagged_real_pct", "{:.1f}", RE),
 ("fed70_su", "eval/results/fedlex_compare.json", "70b.unflagged_stale_untranslated", "{}", RE),
 ("fed70_su_pct", "eval/results/fedlex_compare.json", "70b.unflagged_stale_untranslated_pct", "{:.1f}", RE),
 ("fed_n", "eval/results/fedlex_compare.json", "n", "{}", RE),
 ("fed8_ready_pct", "eval/results/fedlex_compare.json", "8b_mlx_dwq.ready_pct", "{:.1f}", RE),
 ("fed70_ready_pct", "eval/results/fedlex_compare.json", "70b.ready_pct", "{:.1f}", RE),
 ("cap_flag", "eval/certificates/recorded-fresh166.json", "pass_rule.flag_rate_max_pct", "{:.0f}", "committed replay certificate (kind=replay); regenerate: PYTHONPATH=src python3 -m gleichlaut.certify --backend cache --name recorded-fresh166 (writes to state/)"),
 ("m3_identical", "eval/results/m3.json", "identical_pct", "{:.1f}", RE), ("m3_kappa", "eval/results/m3.json", "flag_kappa", "{:.3f}", RE),
 ("m3_changed", "eval/results/m3.json", "changed_pct", "{:.1f}", RE),
 ("m3_exact", "eval/results/m3.json", "rerun.exact.model", "{:.1f}", RE), ("m3_delta", "eval/results/m3.json", "rerun.exact.delta", "{:+.1f}", RE),
 ("m3_delta_plain", "eval/results/m3.json", "rerun.exact.delta", "{:.1f}", RE),
 ("m3_ci_lo", "eval/results/m3.json", "rerun.exact.ci95.0", "{:.1f}", RE), ("m3_ci_hi", "eval/results/m3.json", "rerun.exact.ci95.1", "{:.1f}", RE),
 ("m3_flag", "eval/results/m3.json", "rerun.flag_rate", "{:.1f}", RE), ("m3_ready", "eval/results/m3.json", "rerun.ready_rate", "{:.1f}", RE),
 ("m3_calls", "eval/results/m3.json", "calls", "{}", RE),
 ("div_nemluvio", "data/backtest/targeted5.json", "cases.0.tests.0.2", "{}", BT),
 ("div_diaphin_it", "data/backtest/targeted5.json", "cases.1.tests.0.2", "{}", BT),
 ("div_diaphin_de", "data/backtest/targeted5.json", "cases.1.tests.1.2", "{}", BT),
 ("div_etanercept", "data/backtest/targeted5.json", "cases.2.tests.0.2", "{}", BT),
 ("div_cresemba", "data/backtest/targeted5.json", "cases.5.tests.0.2", "{}", BT),
 ("div_dupixent_lo", "data/backtest/targeted5.json", "cases.6.tests.0.2", "{}", BT),
 ("div_dupixent_hi", "data/backtest/targeted5.json", "cases.8.tests.0.2", "{}", BT),
 ("fed_ready_pct_8", "eval/results/fedlex.json", "shipped lane = A+code + lock + slot + G1–G4 (DEV: guard choice made after seeing these outputs).all.ready", "{}", FS),
 ("lag_fr_same", "data/backtest/lag.json", "summary.draft.fr.status.same_step", "{}", BT),
 ("lag_it_same", "data/backtest/lag.json", "summary.draft.it.status.same_step", "{}", BT),
 ("lag_both_same", "data/backtest/lag.json", "summary.draft.fr_and_it.same_step", "{}", BT),
 ("lag_units", "data/backtest/lag.json", "summary.draft.units", "{}", BT),
 ("lag_over60", "data/backtest/lag.json", "vision_figures_check.over60_distinct_text_pairs", "{}", BT),
]
R = "eval/results/research_facts.json"; X = "eval/results/external_facts.json"
for k, f in (("window_disobeyed_8b_pct", "{}"), ("window_disobeyed_70b_pct", "{}"), ("window_8b_unflagged_real", "{}"), ("judge_known_divergences", "{}"),
             ("judge_70b_nein", "{}"), ("typing_operator_accuracy_8b_pct", "{}"), ("typing_wrong_in_all_three", "{}"), ("retry_8b_fixed", "{}"),
             ("publicai_8b_name_identical_cells", "{}"), ("gguf_q4_agree_bf16", "{}"), ("mlx4_agree_bf16", "{}")):
    C.append((k, R, k + ".value", f, HAND))
for k in ("judge_70b_nein", "typing_wrong_in_all_three", "retry_8b_fixed", "publicai_8b_name_identical_cells", "gguf_q4_agree_bf16"):
    C.append((k + "_of", R, k + ".of", "{}", HAND))
for k, f in (("okp_insured_2025_millions", "{:.2f}"), ("main_language_fr_pct", "{:.1f}"), ("main_language_it_pct", "{:.1f}"),
             ("infomaniak_70b_chf_per_m_in", "{:.2f}"), ("infomaniak_70b_chf_per_m_out", "{:.2f}"), ("efd_language_service_chf_per_page_min", "{}"),
             ("efd_language_service_chf_per_page_max", "{}"), ("apertus_70b_bf16_gb", "{:.1f}"), ("apertus_70b_gguf_q4_gb", "{:.2f}")):
    C.append((k, X, k + ".value", f, HAND))

if __name__ == "__main__":
    rows = ["id\tvalue\tsource\tpath\tfmt\tcommand\twhere"]
    for cid, src, path, fmt, cmd in C:
        v = fmt.format(get(json.load(open(os.path.join(ROOT, src), encoding="utf-8")), path))
        rows.append("\t".join((cid, v, src, path, fmt, cmd, "README/report/notes")))
    open(os.path.join(ROOT, "claims.tsv"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("claims.tsv:", len(rows) - 1, "claims")
