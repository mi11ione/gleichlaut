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
 ("blind_agree", "eval/results/fresh166_blind.json", "annotators.agree", "{}", RE), ("blind_n", "eval/results/fresh166_blind.json", "annotators.n", "{}", RE),
 ("blind_kappa", "eval/results/fresh166_blind.json", "annotators.kappa", "{:.3f}", RE),
 ("arl_reg_strict", "eval/results/audit_relabel.json", "sets.register.confirmed_strict_real", "{}", RE), ("arl_reg_strict_pct", "eval/results/audit_relabel.json", "sets.register.precision_strict_pct", "{:.1f}", RE),
 ("arl_lists_strict", "eval/results/audit_relabel.json", "sets.lists.confirmed_strict_real", "{}", RE),
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
 ("m2r_calls", "eval/results/m2_rerun.json", "rerun_calls", "{}", RE), ("m2r_identical", "eval/results/m2_rerun.json", "identical_outputs", "{}", RE),
 ("audit_limitations", "eval/results/audit.json", "summary.n_limitations", "{:,}", RE),
 ("audit_findings", "eval/results/audit.json", "findings", "{}", RE), ("audit_real", "eval/results/audit.json", "real", "{}", RE),
 ("audit_known", "eval/results/audit.json", "known_found", "{}", RE),
 ("audit_lims", "eval/results/audit.json", "limitations_found", "{}", RE),
 ("audit_w_lo", "eval/results/audit.json", "precision_wilson95.0", "{:.1f}", RE), ("audit_w_hi", "eval/results/audit.json", "precision_wilson95.1", "{:.1f}", RE),
 ("audit_values", "eval/results/audit.json", "summary.recall.tests", "{}", RE),
 ("audit_all", "eval/results/audit.json", "v2.findings_all_kinds", "{}", RE),
 ("audit_all_real", "eval/results/audit.json", "v2.real_all_kinds", "{}", RE),
 ("audit_all_prec", "eval/results/audit.json", "v2.precision_all_pct", "{:.1f}", RE),
 ("audit_new_real", "eval/results/audit.json", "v2.new_kinds_real", "{}", RE),
 ("term_f", "eval/results/audit_more.json", "terminology.findings", "{}", RE),
 ("term_r", "eval/results/audit_more.json", "terminology.real", "{}", RE),
 ("lists_f", "eval/results/audit_more.json", "lists_findings", "{}", RE), ("lists_r", "eval/results/audit_more.json", "lists_real", "{}", RE),
 ("lists_p", "eval/results/audit_more.json", "lists_precision_pct", "{:.1f}", RE),
 ("al_de", "data/audit/audit_al_20260701.json", "findings.2.de_only.0.value", "{}", "PYTHONPATH=src python3 -m gleichlaut.audit --list al --file <AL xlsx>"),
 ("al_it", "data/audit/audit_al_20260701.json", "findings.2.tgt_only.0.value", "{}", "PYTHONPATH=src python3 -m gleichlaut.audit --list al --file <AL xlsx>"),
 ("audit_prec", "eval/results/audit.json", "precision_pct", "{:.1f}", RE),
 ("pe_all", "eval/results/post_edit.json", "all.edits_saved_pct", "{:.1f}", RE),
 ("pe_lo", "eval/results/post_edit.json", "all.edits_saved_ci95.0", "{:.1f}", RE),
 ("pe_hi", "eval/results/post_edit.json", "all.edits_saved_ci95.1", "{:.1f}", RE),
 ("pe_ready", "eval/results/post_edit.json", "ready.edits_saved_pct", "{:.1f}", RE),
 ("pe_fewer", "eval/results/post_edit.json", "all.items_draft_fewer", "{}", RE),
 ("pe_more", "eval/results/post_edit.json", "all.items_draft_more", "{}", RE),
 ("rq_carried", "eval/results/ready_quality.json", "carried_forward_mistranslation", "{}", RE),
 ("rq_b_change", "eval/results/ready_quality.json", "bound95_per_change", "{:.1f}", RE),
 ("rq_b_family", "eval/results/ready_quality.json", "bound95_per_family", "{:.1f}", RE),
 ("rq_changes", "eval/results/ready_quality.json", "ready_de_changes", "{}", RE),
 ("rq_families", "eval/results/ready_quality.json", "ready_families", "{}", RE),
 ("rq_gold_dev", "eval/results/ready_quality.json", "fresh_gold_seen_as_dev_input", "{}", RE),
 ("bp_exact", "eval/results/baseline_plus.json", "rules_plus_exact", "{:.1f}", RE),
 ("bp_delta", "eval/results/baseline_plus.json", "delta", "{:+.1f}", RE), ("bp_delta_p", "eval/results/baseline_plus.json", "delta", "{:.1f}", RE),
 ("bp_lo", "eval/results/baseline_plus.json", "ci95.0", "{:.1f}", RE), ("bp_hi", "eval/results/baseline_plus.json", "ci95.1", "{:.1f}", RE),
 ("bp_edits", "eval/results/baseline_plus.json", "edits_saved_pct", "{:.1f}", RE),
 ("bp_e_lo", "eval/results/baseline_plus.json", "edits_saved_ci95.0", "{:.1f}", RE), ("bp_e_hi", "eval/results/baseline_plus.json", "edits_saved_ci95.1", "{:.1f}", RE),
 ("bp_fam_delta", "eval/results/baseline_plus.json", "without_family.delta", "{:+.1f}", RE),
 ("bp_fam_lo", "eval/results/baseline_plus.json", "without_family.ci95.0", "{:.1f}", RE), ("bp_fam_hi", "eval/results/baseline_plus.json", "without_family.ci95.1", "{:.1f}", RE),
 ("m1_exact", "eval/results/m1_q4_k_m.json", "exact.model", "{:.1f}", RE), ("m1_delta", "eval/results/m1_q4_k_m.json", "exact.delta", "{:+.1f}", RE),
 ("m1_delta_p", "eval/results/m1_q4_k_m.json", "exact.delta", "{:.1f}", RE),
 ("m1_lo", "eval/results/m1_q4_k_m.json", "exact.ci95.0", "{:.1f}", RE), ("m1_hi", "eval/results/m1_q4_k_m.json", "exact.ci95.1", "{:.1f}", RE),
 ("m1_flag", "eval/results/m1_q4_k_m.json", "flag_rate", "{:.1f}", RE), ("m1_ready", "eval/results/m1_q4_k_m.json", "ready_rate", "{:.1f}", RE),
 ("m1_ready_n", "eval/results/m1_q4_k_m.json", "unflagged", "{}", RE), ("m1_fix", "eval/results/m1_q4_k_m.json", "ready_needs_fix", "{}", RE),
 ("m1_minor", "eval/results/m1_q4_k_m.json", "ready_minor_terminology", "{}", RE), ("m1_secs", "eval/results/m1_q4_k_m.json", "cpu_secs_per_item", "{:.1f}", RE),
 ("m1_stale", "eval/results/m1_q4_k_m.json", "unflagged_stale", "{}", RE), ("m1_german", "eval/results/m1_q4_k_m.json", "unflagged_german", "{}", RE),
 ("m1_su", "eval/results/m1_q4_k_m.json", "pass_rule.unflagged_stale_untranslated.0", "{:.2f}", RE),
 ("pe8_all", "eval/results/post_edit_8b_q4_k_m.json", "all.edits_saved_pct", "{:.1f}", RE), ("pe8_lo", "eval/results/post_edit_8b_q4_k_m.json", "all.edits_saved_ci95.0", "{:.1f}", RE),
 ("pe8_hi", "eval/results/post_edit_8b_q4_k_m.json", "all.edits_saved_ci95.1", "{:.1f}", RE),
 ("m2_exact", "eval/results/m1_q8_0.json", "exact.model", "{:.1f}", RE), ("m2_flag", "eval/results/m1_q8_0.json", "flag_rate", "{:.1f}", RE),
 ("m2_ready", "eval/results/m1_q8_0.json", "ready_rate", "{:.1f}", RE), ("m2_ready_n", "eval/results/m1_q8_0.json", "unflagged", "{}", RE),
 ("m2_fix", "eval/results/m1_q8_0.json", "ready_needs_fix", "{}", RE), ("m2_secs", "eval/results/m1_q8_0.json", "cpu_secs_per_item", "{:.1f}", RE),
 ("m2_kappa", "eval/results/m1_q8_0.json", "annotators.needs_fix_kappa", "{:.3f}", RE), ("m2_tiebreak", "eval/results/m1_q8_0.json", "annotators.tiebreak", "{}", RE),
 ("pe8q8_all", "eval/results/post_edit_8b_q8_0.json", "all.edits_saved_pct", "{:.1f}", RE), ("pe8q8_lo", "eval/results/post_edit_8b_q8_0.json", "all.edits_saved_ci95.0", "{:.1f}", RE),
 ("pe8q8_hi", "eval/results/post_edit_8b_q8_0.json", "all.edits_saved_ci95.1", "{:.1f}", RE),
 ("size_q8_diff", "eval/results/size_compare.json", "q8_0.saved_diff_pts", "{:.1f}", RE), ("size_q8_lo", "eval/results/size_compare.json", "q8_0.saved_diff_ci95.0", "{:.1f}", RE),
 ("size_q8_hi", "eval/results/size_compare.json", "q8_0.saved_diff_ci95.1", "{:.1f}", RE),
 ("q8q4_diff", "eval/results/size_compare.json", "q8_0_vs_q4_k_m.saved_diff_pts", "{:.1f}", RE), ("q8q4_lo", "eval/results/size_compare.json", "q8_0_vs_q4_k_m.saved_diff_ci95.0", "{:.1f}", RE),
 ("q8q4_hi", "eval/results/size_compare.json", "q8_0_vs_q4_k_m.saved_diff_ci95.1", "{:.1f}", RE),
 ("size_q8_items70", "eval/results/size_compare.json", "q8_0.items_70b_fewer_edits", "{}", RE), ("size_q8_items8", "eval/results/size_compare.json", "q8_0.items_8b_fewer_edits", "{}", RE),
 ("size_q4_diff", "eval/results/size_compare.json", "q4_k_m.saved_diff_pts", "{:.1f}", RE), ("size_q4_lo", "eval/results/size_compare.json", "q4_k_m.saved_diff_ci95.0", "{:.1f}", RE),
 ("size_q4_hi", "eval/results/size_compare.json", "q4_k_m.saved_diff_ci95.1", "{:.1f}", RE),
 ("tb_house", "eval/results/termbase.json", "termbase.house_total", "{}", RE), ("tb_house_fr", "eval/results/termbase.json", "termbase.house.fr", "{}", RE), ("tb_house_it", "eval/results/termbase.json", "termbase.house.it", "{}", RE),
 ("tb_q4_explained", "eval/results/termbase.json", "runs.8b_q4_k_m.ready_needs_fix_with_advisory", "{}", RE),
 ("tb_q8_explained", "eval/results/termbase.json", "runs.8b_q8_0.ready_needs_fix_with_advisory", "{}", RE),
 ("ar_n", "eval/results/audit_recall.json", "injections", "{:,}", RE), ("ar_recall", "eval/results/audit_recall.json", "recall_pct", "{:.1f}", RE),
 ("ar_lo", "eval/results/audit_recall.json", "wilson95_pct.0", "{:.1f}", RE), ("ar_hi", "eval/results/audit_recall.json", "wilson95_pct.1", "{:.1f}", RE),
 ("ar_number", "eval/results/audit_recall.json", "types.number.recall_pct", "{:.1f}", RE), ("ar_language", "eval/results/audit_recall.json", "types.language.recall_pct", "{:.1f}", RE),
 ("ar_unit", "eval/results/audit_recall.json", "types.unit.recall_pct", "{:.1f}", RE), ("ar_deletion", "eval/results/audit_recall.json", "types.deletion.recall_pct", "{:.1f}", RE),
 ("ar_typo", "eval/results/audit_recall.json", "types.typo.recall_pct", "{:.1f}", RE),
 ("ar2_any", "eval/results/audit_recall.json", "v2.number_any.recall_pct", "{:.1f}", RE), ("ar2_word", "eval/results/audit_recall.json", "v2.number_word.recall_pct", "{:.1f}", RE),
 ("ar2_op_n", "eval/results/audit_recall.json", "v2.operator.n", "{}", RE), ("ar2_neg_n", "eval/results/audit_recall.json", "v2.negation.n", "{}", RE),
 ("r15_op", "eval/results/audit_r15.json", "recall.operator.after_pct", "{:.1f}", RE), ("r15_negdrop", "eval/results/audit_r15.json", "recall.negation_drop.after_pct", "{:.1f}", RE),
 ("r15_negadd", "eval/results/audit_r15.json", "recall.negation_add.after_pct", "{:.1f}", RE), ("r15_word", "eval/results/audit_r15.json", "recall.number_word.after_pct", "{:.1f}", RE),
 ("r15_findings", "eval/results/audit_r15.json", "register.findings", "{}", RE), ("r15_real", "eval/results/audit_r15.json", "register.real_or_minor", "{}", RE),
 ("m3_backend_vllm", "eval/results/m3.json", "serving_backends.vllm", "{}", RE), ("m3_backend_fp1", "eval/results/m3.json", "serving_backends.fp1", "{}", RE),
 ("ag_issues", "eval/results/audit_grouping.json", "issues", "{}", RE), ("ag_findings", "eval/results/audit_grouping.json", "findings", "{}", RE), ("ag_term", "eval/results/audit_grouping.json", "terminology", "{}", RE),
 ("v_month", "eval/results/value.json", "items_per_month", "{:.1f}", RE), ("v_rules_m", "eval/results/value.json", "edits_per_month_rules", "{:,}", RE),
 ("v_saved8", "eval/results/value.json", "saved_per_month_8b", "{}", RE), ("v_saved70", "eval/results/value.json", "saved_per_month_70b", "{}", RE),
 ("v_pt_rules", "eval/results/value.json", "edits_per_text_rules", "{:.1f}", RE), ("v_pt_8b", "eval/results/value.json", "edits_per_text_8b", "{:.1f}", RE),
 ("v_pt_70b", "eval/results/value.json", "edits_per_text_70b", "{:.1f}", RE),
 ("sh_items", "eval/results/shadow_20260901_20261001.json", "q4_k_m.items", "{}", RE), ("sh_compared", "eval/results/shadow_20260901_20261001.json", "compared", "{}", RE),
 ("sh_boiler", "eval/results/shadow_20260901_20261001.json", "boilerplate_items", "{}", RE),
 ("sh_ready_total", "eval/results/shadow_20260901_20261001.json", "ready_total", "{}", RE),
 ("sh_flag_70b", "eval/results/shadow_20260901_20261001.json", "70b.flag_rate", "{:.1f}", RE), ("sh_flag_q8", "eval/results/shadow_20260901_20261001.json", "q8_0.flag_rate", "{:.1f}", RE),
 ("sh_flag_q4", "eval/results/shadow_20260901_20261001.json", "q4_k_m.flag_rate", "{:.1f}", RE),
 # PREREG R10: the second shadow month (01.08 -> 01.09.2026), R0 criteria per model
 ("sh2_items", "eval/results/shadow_20260801_20260901.json", "q8_0.items", "{}", RE), ("sh2_human", "eval/results/shadow_20260801_20260901.json", "q8_0.human", "{}", RE),
 ("sh2_compared", "eval/results/shadow_20260801_20260901.json", "compared", "{}", RE), ("sh2_seen", "eval/results/shadow_20260801_20260901.json", "seen_compared", "{}", RE),
 ("sh2_boiler", "eval/results/shadow_20260801_20260901.json", "boilerplate_items", "{}", RE), ("sh2_labelled", "eval/results/shadow_20260801_20260901.json", "labelled", "{}", RE),
 ("sh2_q8_exact", "eval/results/shadow_20260801_20260901.json", "q8_0.exact", "{}", RE), ("sh2_70b_exact", "eval/results/shadow_20260801_20260901.json", "70b.exact", "{}", RE),
 ("sh2_q8_ready", "eval/results/shadow_20260801_20260901.json", "q8_0.ready", "{}", RE), ("sh2_70b_ready", "eval/results/shadow_20260801_20260901.json", "70b.ready", "{}", RE),
 ("sh2_q8_gain", "eval/results/shadow_20260801_20260901.json", "r0.q8_0.month.criteria.exact_gain.0", "{:+.1f}", RE),
 ("sh2_q8_flag", "eval/results/shadow_20260801_20260901.json", "r0.q8_0.month.criteria.flag_rate.0", "{:.1f}", RE),
 ("sh2_70b_flag", "eval/results/shadow_20260801_20260901.json", "r0.70b.month.criteria.flag_rate.0", "{:.1f}", RE),
 ("sh2_q8_sg", "eval/results/shadow_20260801_20260901.json", "r0.q8_0.month.criteria.unflagged_stale_untranslated.0", "{:.1f}", RE),
 ("sh2_70b_sg", "eval/results/shadow_20260801_20260901.json", "r0.70b.month.criteria.unflagged_stale_untranslated.0", "{:.1f}", RE),
 ("sh2_review_share", "eval/results/shadow_20260801_20260901.json", "r0.q8_0.month.review_share_incl_routed.2", "{:.1f}", RE),
 ("fed_q4_k_m_exact", "eval/results/fedlex_compare.json", "8b_gguf_q4_k_m.exact_pct", "{:.1f}", RE), ("fed_q4_k_m_flag", "eval/results/fedlex_compare.json", "8b_gguf_q4_k_m.flag_rate", "{:.1f}", RE),
 ("fed_q4_k_m_ready", "eval/results/fedlex_compare.json", "8b_gguf_q4_k_m.ready_pct", "{:.1f}", RE), ("fed_q4_k_m_real", "eval/results/fedlex_compare.json", "8b_gguf_q4_k_m.unflagged_real", "{}", RE),
 ("fed_q8_0_exact", "eval/results/fedlex_compare.json", "8b_gguf_q8_0.exact_pct", "{:.1f}", RE), ("fed_q8_0_flag", "eval/results/fedlex_compare.json", "8b_gguf_q8_0.flag_rate", "{:.1f}", RE),
 ("fed_q8_0_ready", "eval/results/fedlex_compare.json", "8b_gguf_q8_0.ready_pct", "{:.1f}", RE), ("fed_q8_0_real", "eval/results/fedlex_compare.json", "8b_gguf_q8_0.unflagged_real", "{}", RE),
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
FM = "eval/results/failure_modes_q8_0.json"   # PREREG R8: failure-mode tests on the shipped Q8_0, beside the MLX 4-bit runs
for cid, path, fmt in (
        ("fm_free_exact", "free.q8_0.exact", "{:.1f}"), ("fm_free_flips", "free.q8_0.lexicon_flips", "{}"),
        ("fm_free_sample", "free.q8_0.sample_n", "{}"), ("fm_free_real", "free.q8_0.sample_real_flips", "{}"),
        ("fm_free_real_extrap", "free.q8_0.real_flips_extrapolated", "{}"), ("fm_free_chrf", "free.q8_0.chrf", "{:.1f}"),
        ("fm_free_mlx_flips", "free.mlx.lexicon_flips", "{}"),
        ("fm_win_disobeyed_pct", "window.q8_0.disobeyed_pct", "{:.0f}"), ("fm_win_disobeyed", "window.q8_0.disobeyed", "{}"),
        ("fm_win_windows", "window.q8_0.windows", "{}"), ("fm_win_exact", "window.q8_0.exact", "{:.1f}"),
        ("fm_win_chrf", "window.q8_0.chrf", "{:.1f}"), ("fm_win_rules_chrf", "window.rules.chrf", "{:.1f}"),
        ("fm_win_mlx_pct", "window.mlx.disobeyed_pct", "{:.0f}"), ("fm_win_70b_pct", "window.70b.disobeyed_pct", "{:.0f}"),
        ("fm_judge_gen_hits", "judge.q8_0_generation.hits", "{}"), ("fm_judge_gen_ff", "judge.q8_0_generation.false_flags", "{}"),
        ("fm_judge_gen_nein", "judge.q8_0_generation.nein_answers", "{}"), ("fm_judge_gen_calls", "judge.q8_0_generation.calls", "{}"),
        ("fm_judge_70b_nein", "judge.70b_generation.nein_answers", "{}"),
        ("fm_judge_lp_hits", "judge.q8_0_logprob.hits_at_half", "{}"), ("fm_judge_lp_ff", "judge.q8_0_logprob.false_flags", "{}"),
        ("fm_judge_auroc", "judge.q8_0_logprob.auroc_item", "{:.2f}"), ("fm_judge_auroc_ab", "judge.q8_0_logprob.auroc_item_ab", "{:.2f}"),
        ("fm_judge_auroc_ba", "judge.q8_0_logprob.auroc_item_ba", "{:.2f}"), ("fm_judge_argmax", "judge.q8_0_logprob.argmax_hits", "{}"),
        ("fm_judge_mlx_auroc", "judge.mlx_logprob.auroc_item", "{:.2f}"), ("fm_judge_mlx_argmax", "judge.mlx_logprob.argmax_hits", "{}"),
        ("fm_judge_mlx_auroc_ab", "judge.mlx_logprob.auroc_item_ab", "{:.2f}"), ("fm_judge_mlx_auroc_ba", "judge.mlx_logprob.auroc_item_ba", "{:.2f}"),
        ("fm_typ_op_pct", "typing.q8_0.operator_acc_pct", "{:.0f}"), ("fm_typ_conditions", "typing.q8_0.gold_conditions", "{}"),
        ("fm_typ_ge", "typing.q8_0.top_operator_ge", "{}"), ("fm_typ_mlx_op_pct", "typing.mlx.operator_acc_pct", "{:.0f}"),
        ("fm_typ_all3", "typing.q8_0.held_wrong_all_three", "{}"), ("fm_typ_triples", "typing.q8_0.held_triples", "{}"),
        ("fm_typ_phi_min", "typing.q8_0.held_phi_min", "{:.2f}"), ("fm_typ_phi_max", "typing.q8_0.held_phi_max", "{:.2f}"),
        ("fm_typ_mlx_phi_min", "typing.mlx.held_phi_min", "{:.2f}"), ("fm_typ_mlx_phi_max", "typing.mlx.held_phi_max", "{:.2f}"),
        ("fm_retry_n", "retry.q8_0.retried", "{}"), ("fm_retry_fixed", "retry.q8_0.retry_fixed", "{}"),
        ("fm_retry_mlx_n", "retry.mlx.retried", "{}"), ("fm_retry_mlx_fixed", "retry.mlx.retry_fixed", "{}"),
        ("fm_retry_r1_n", "retry.q8_0_fresh166_r1.retried", "{}"), ("fm_retry_r1_fixed", "retry.q8_0_fresh166_r1.retry_fixed", "{}"),
        ("fm_reask_r1_n", "retry.q8_0_fresh166_r1.reasked", "{}"), ("fm_reask_r1_kept", "retry.q8_0_fresh166_r1.reask_kept", "{}"),
        ("fm_s2b_exact", "retry.q8_0.exact", "{:.1f}"), ("fm_s2b_flag", "retry.q8_0.flag_rate", "{:.1f}"),
        ("fm_s2b_ready", "retry.q8_0.ready", "{}"), ("fm_s2b_ready_real", "retry.q8_0.ready_real", "{}"),
        ("fm_s2b_ready_exact", "retry.q8_0.ready_classes.exact", "{}"), ("fm_s2b_mlx_flag", "retry.mlx.flag_rate", "{:.1f}"),
        ("fm_s2b_mlx_exact", "retry.mlx.exact", "{:.1f}")):
    C.append((cid, FM, path, fmt, RE))
R = "eval/results/research_facts.json"; X = "eval/results/external_facts.json"
for k, f in (("window_disobeyed_8b_pct", "{}"), ("window_disobeyed_70b_pct", "{}"), ("window_8b_unflagged_real", "{}"), ("judge_known_divergences", "{}"),
             ("judge_70b_nein", "{}"), ("typing_operator_accuracy_8b_pct", "{}"), ("typing_wrong_in_all_three", "{}"), ("retry_8b_fixed", "{}"),
             ("publicai_8b_name_identical_cells", "{}"), ("gguf_q4_agree_bf16", "{}"), ("mlx4_agree_bf16", "{}"),
             ("mmlu_shared_route_pct", "{:.1f}"), ("mmlu_v1_8b_route_pct", "{:.1f}"), ("judge_8b_logprob_auroc", "{:.2f}"),
             ("judge_8b_logprob_auroc_order_hi", "{:.2f}"), ("judge_8b_logprob_auroc_order_lo", "{:.2f}"),
             ("judge_8b_logprob_argmax", "{}"), ("gguf_q8_agree_bf16", "{}"), ("free_translation_real_flips_sample", "{}")):
    C.append((k, R, k + ".value", f, HAND))
for k in ("judge_70b_nein", "typing_wrong_in_all_three", "retry_8b_fixed", "publicai_8b_name_identical_cells", "gguf_q4_agree_bf16", "mmlu_shared_route_pct"):
    C.append((k + "_of", R, k + ".of", "{}", HAND))
for k, f in (("okp_insured_2025_millions", "{:.2f}"), ("main_language_fr_pct", "{:.1f}"), ("main_language_it_pct", "{:.1f}"),
             ("infomaniak_70b_chf_per_m_in", "{:.2f}"), ("infomaniak_70b_chf_per_m_out", "{:.2f}"), ("efd_language_service_chf_per_page_min", "{}"),
             ("efd_language_service_chf_per_page_max", "{}"), ("apertus_70b_bf16_gb", "{:.1f}"), ("apertus_70b_gguf_q4_gb", "{:.2f}")):
    C.append((k, X, k + ".value", f, HAND))

AS = "eval/results/annotator_sensitivity.json"; ASA, ASB = "protocols.reference_shown.", "protocols.reference_hidden."
for cid, path, fmt in (("as_planted", "counts.planted", "{}"), ("as_untouched", "counts.untouched", "{}"), ("as_real", "counts.real", "{}"),
                       ("as_types", "len:types", "{}"),
                       ("as_a_both", ASA + "planted.severe.both.k", "{}"), ("as_a_both_lo", ASA + "planted.severe.both.wilson95.0", "{:.1f}"),
                       ("as_a_either", ASA + "planted.severe.either.k", "{}"),
                       ("as_b_both", ASB + "planted.severe.both.k", "{}"), ("as_b_both_lo", ASB + "planted.severe.both.wilson95.0", "{:.1f}"),
                       ("as_b_either", ASB + "planted.severe.either.k", "{}"),
                       ("as_a_fa_sev", ASA + "untouched.severe.either.k", "{}"), ("as_b_fa_sev", ASB + "untouched.severe.either.k", "{}"),
                       ("as_a_fa_fix", ASA + "untouched.needs_fix.either.k", "{}"),
                       ("as_real_REAL", ASA + "real.existing.REAL", "{}"),
                       ("as_a_real_REAL_both", ASA + "real.severe_incl_german_by_existing.REAL.both.k", "{}"),
                       ("as_b_real_REAL_either", ASB + "real.severe_incl_german_by_existing.REAL.either.k", "{}")):
    C.append((cid, AS, path, fmt, RE))

# PREREG R14: (A) every labelled audit finding relabelled by two blind annotators + a third; (B) errors inside the amended wording
AR = "eval/results/audit_relabel.json"
for cid, path, fmt in (("ar14_n", "findings", "{}"), ("ar14_agree", "all.annotators.agree", "{}"), ("ar14_kappa", "all.annotators.kappa", "{:.3f}"),
                       ("ar14_answer_agree", "all.annotators.answer_agree", "{}"), ("ar14_tiebreak", "all.annotators.tiebreak", "{}"),
                       ("ar14_vs_first", "all.vs_first.agree", "{}"), ("ar14_vs_first_kappa", "all.vs_first.kappa", "{:.3f}"),
                       ("ar14_reg_first", "sets.register.confirmed_first", "{}"), ("ar14_reg_maj", "sets.register.confirmed_majority", "{}"),
                       ("ar14_term_first", "sets.terminology.confirmed_first", "{}"), ("ar14_term_maj", "sets.terminology.confirmed_majority", "{}"),
                       ("ar14_term_strict", "sets.terminology.confirmed_strict_real", "{}"),
                       ("ar14_lists_first", "sets.lists.confirmed_first", "{}"), ("ar14_lists_maj", "sets.lists.confirmed_majority", "{}"),
                       ("ar14_reg_lo", "sets.register.precision_majority_wilson95.0", "{:.1f}"), ("ar14_reg_hi", "sets.register.precision_majority_wilson95.1", "{:.1f}"),
                       ("ar14_first_prec", "sets.register.precision_first_pct", "{:.1f}"), ("ar14_lists_first_prec", "sets.lists.precision_first_pct", "{:.1f}")):
    C.append((cid, AR, path, fmt, RE))
ASI = "eval/results/annotator_sensitivity_inspan.json"
for cid, path, fmt in (("asi_planted", "counts.planted", "{}"), ("asi_real", "counts.real", "{}"),
                       ("asi_both", "planted.severe.both.k", "{}"), ("asi_both_lo", "planted.severe.both.wilson95.0", "{:.1f}"),
                       ("asi_either", "planted.severe.either.k", "{}"), ("asi_fa_fix", "untouched.needs_fix.either.k", "{}"),
                       ("asi_fa_sev", "untouched.severe.either.k", "{}"), ("asi_bound_70b", "ready_bound.70b.adjusted_both", "{:.1f}"),
                       ("asi_bound_q8", "ready_bound.q8_0.adjusted_both", "{:.1f}")):
    C.append((cid, ASI, path, fmt, RE))

# PREREG R17: (A) real errors BAG fixed without a German change; (B) Apertus 70B as a non-Claude annotator
RA17, RAa, RAb = "eval/results/annotator_real_errors.json", "protocols.reference_shown.", "protocols.reference_hidden."
for cid, path, fmt in (("r17_changes", "counts.changes_mined", "{}"), ("r17_content", "counts.content", "{}"),
                       ("r17_sweep", "counts.families.36d94228", "{}"), ("r17_typo", "counts.by_type.punctuation", "{}"),
                       ("r17_a_fix_both", RAa + "errors.needs_fix.both.k", "{}"), ("r17_a_fix_either", RAa + "errors.needs_fix.either.k", "{}"),
                       ("r17_a_fix_lo", RAa + "errors.needs_fix.both.wilson95.0", "{:.1f}"), ("r17_a_fix_hi", RAa + "errors.needs_fix.both.wilson95.1", "{:.1f}"),
                       ("r17_a_sev_both", RAa + "errors.severe.both.k", "{}"),
                       ("r17_b_fix_both", RAb + "errors.needs_fix.both.k", "{}"), ("r17_b_fix_either", RAb + "errors.needs_fix.either.k", "{}"),
                       ("r17_b_fix_lo", RAb + "errors.needs_fix.both.wilson95.0", "{:.1f}"), ("r17_b_fix_hi", RAb + "errors.needs_fix.both.wilson95.1", "{:.1f}"),
                       ("r17_b_sev_both", RAb + "errors.severe.both.k", "{}"), ("r17_b_sev_either", RAb + "errors.severe.either.k", "{}"),
                       ("r17_a_other_fix_both", RAa + "errors_by_family.other.needs_fix.both.k", "{}"),
                       ("r17_b_other_fix_both", RAb + "errors_by_family.other.needs_fix.both.k", "{}"),
                       ("r17_a_sweep_fix_either", RAa + "errors_by_family.sweep_36d94228.needs_fix.either.k", "{}"),
                       ("r17_a_ctl_fix_either", RAa + "controls.needs_fix.either.k", "{}"), ("r17_b_ctl_fix_either", RAb + "controls.needs_fix.either.k", "{}"),
                       ("r17_b_ctl_sev_either", RAb + "controls.severe.either.k", "{}"),
                       ("r17_a_kappa", RAa + "annotators.kappa", "{:.3f}"), ("r17_b_kappa", RAb + "annotators.kappa", "{:.3f}")):
    C.append((cid, RA17, path, fmt, RE))
XF, XFa, XFb = "eval/results/annotator_crossfamily.json", "real_errors.reference_shown.", "real_errors.reference_hidden."
for cid, path, fmt in (("xf_requests", "requests", "{}"), ("xf_audit_n", "audit.all.n", "{}"), ("xf_audit_agree", "audit.all.agree", "{}"),
                       ("xf_audit_kappa", "audit.all.kappa", "{:.3f}"), ("xf_audit_answer_agree", "audit.all.answer_agree", "{}"),
                       ("xf_audit_conf", "audit.all.apertus_confirmed", "{}"), ("xf_audit_unparsed", "audit.unparsed", "{}"),
                       ("xf_a_fix", XFa + "errors.needs_fix.k", "{}"), ("xf_a_sev", XFa + "errors.severe.k", "{}"),
                       ("xf_b_fix", XFb + "errors.needs_fix.k", "{}"), ("xf_b_sev", XFb + "errors.severe.k", "{}"),
                       ("xf_a_ctl_fix", XFa + "controls.needs_fix.k", "{}"), ("xf_b_ctl_fix", XFb + "controls.needs_fix.k", "{}")):
    C.append((cid, XF, path, fmt, RE))

# PREREG R18: the certified 8B as a log-probability filter on the round-5 audit findings
AF = "eval/results/audit_apertus_filter.json"
for cid, path, fmt in (("r18_auc_test", "planted.test.auroc", "{:.3f}"), ("r18_auc_lo", "planted.test.auroc_ci95.0", "{:.3f}"),
                       ("r18_auc_hi", "planted.test.auroc_ci95.1", "{:.3f}"), ("r18_auc_op", "planted.by_type.operator.test.auroc", "{:.3f}"),
                       ("r18_auc_negdrop", "planted.by_type.negation_drop.test.auroc", "{:.3f}"),
                       ("r18_kept", "register.all.kept", "{}"), ("r18_kept_conf", "register.all.kept_confirmed", "{}"),
                       ("r18_prec_before", "register.all.precision_before_pct", "{:.1f}"), ("r18_prec_after", "register.all.precision_after_pct", "{:.1f}"),
                       ("r18_pairs", "pairs.n", "{}"), ("r18_shards", "shards.certificate_verified", "{}")):
    C.append((cid, AF, path, fmt, RE))

# PREREG R12: house wording in the drafting prompt (variant v3-terms) beside the frozen pipeline on both live months
R12 = "eval/results/r12_terms.json"
for mk, mon in (("aug", "20260801-20260901"), ("sep", "20260901-20261001")):
    C.append((f"r12_{mk}_drafted", R12, f"months.{mon}.drafted", "{}", RE))
    C.append((f"r12_{mk}_changed", R12, f"months.{mon}.prompts_changed", "{}", RE))
    C.append((f"r12_{mk}_calls", R12, f"months.{mon}.model_calls", "{}", RE))
    for m in ("q8_0", "70b"):
        for a, ak in (("frozen", "f"), ("v3_terms", "v")):
            b = f"months.{mon}.{m}.{a}."
            for cid, path, fmt in (("n", "n", "{}"), ("exact", "exact", "{}"), ("ready", "ready", "{}"), ("flagged", "flagged", "{}"),
                                   ("flag", "criteria.flag_rate.0", "{:.1f}"), ("gain", "criteria.exact_gain.0", "{:+.1f}"),
                                   ("sg", "criteria.unflagged_stale_untranslated.0", "{:.1f}"), ("real", "criteria.unflagged_real.0", "{:.1f}"),
                                   ("sg_n", "unflagged_stale_german_n", "{}"), ("real_n", "unflagged_real_n", "{}"),
                                   ("newsent", "new_sentence_exact", "{}"), ("newsent_n", "new_sentence_items", "{}")):
                C.append((f"r12_{mk}_{m}_{ak}_{cid}", R12, b + path, fmt, RE))
for cid, path in (("r12_labelled", "labelled"), ("r12_agree", "annotators_agree"), ("r12_tiebreak", "tiebreak")):
    C.append((cid, R12, path, "{}", RE))

# PREREG R16: memorisation probe (continue the first half of each text word for word)
MEM = "eval/results/memorisation.json"
for s_ in "TPN":
    C.append((f"mem_{s_}_n", MEM, f"sizes.{s_}", "{}", RE))
    for m, mk in (("70b", "70b"), ("8b_q8_0", "8b")):
        C.append((f"mem_{mk}_{s_}_next10", MEM, f"models.{m}.sets.{s_}.next10_count", "{}", RE))
C.append(("mem_70b_requests", MEM, "models.70b.requests", "{}", RE))

if __name__ == "__main__":
    rows = ["id\tvalue\tsource\tpath\tfmt\tcommand\twhere"]
    for cid, src, path, fmt, cmd in C:
        v = fmt.format(get(json.load(open(os.path.join(ROOT, src), encoding="utf-8")), path))
        rows.append("\t".join((cid, v, src, path, fmt, cmd, "README/report/notes")))
    open(os.path.join(ROOT, "claims.tsv"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("claims.tsv:", len(rows) - 1, "claims")
