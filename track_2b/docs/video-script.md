# Demo video script (≤ 2:00, screen recording + voice-over)

Every number spoken or shown is in `claims.tsv`. Screens: the review page (`make local-run` or `make run`, then open
`out/ui/index.html`), a terminal, and two slides (the five divergences; the deployment table). Record at 1440×900, dark mode.

| Time | Screen | Voice-over (≈ 290 words in total) |
|---|---|---|
| 0:00–0:18 | Slide: Nemluvio limitation, DE / FR / IT side by side, "alle acht Wochen" / "toutes les huit semaines" / "ogni quattro settimane" highlighted | "BAG publishes the conditions under which basic insurance pays for a medicine in German, French and Italian. In today's list we found five divergences. Nemluvio: every eight weeks in German and French, every four weeks in Italian. All five are numbers." |
| 0:18–0:42 | Review page, card wb000 (Rybrevant): German old→new highlighted, FR and IT drafts, number chips, all lights green | "When the German changes, Gleichlaut drafts the French and Italian change with Apertus. The old translation is locked outside the edit. Numbers never reach the model: they become slot codes, and code writes them back. These blue chips were placed by code. Every guard is green, so this draft is ready for a translator to accept." |
| 0:42–1:02 | Filter "Flagged"; open a draft with G1/G5 red and the complaint text visible | "Here a guard caught German left in the Italian draft and named it. The model gets one re-ask with that complaint; if any guard still fails, the draft goes to a translator. No model judges anything; the guards are code, frozen before we tested them." |
| 1:02–1:22 | Slide or terminal: free-translation output with "dovrebbe" vs "deve" | "Compare the naive approach: let the model translate the new German. It turned 'deve', must, into 'dovrebbe', should. Nothing flags it. That is why Gleichlaut never translates from scratch." |
| 1:22–1:42 | Header tiles of the review page (17.5% vs 6.0%, 39.8% ready, 0 errors) | "On 166 held-out items, with guards hashed before any output existed, Apertus 70B drafts match the official text 17.5% of the time against 6.0% for rules; 40% come out ready, with no meaning errors among them. We also publish what failed: our first out-of-sample run, and the 8B on these texts." |
| 1:42–2:00 | Terminal: `make run` scrolling to "replay PASSED" and "make run PASSED"; then the deployment slide | "make run re-executes the recorded run offline and checks every number. The 8B runs on a CPU, air-gapped; the 70B runs on an endpoint you control, after it passes certification. Gleichlaut." |

Recording notes: keep the cursor still while speaking; no music under speech; end card with the repository URL. Upload
unlisted (YouTube or Vimeo) and put the URL in README.md and technical_report.md (`VIDEO_URL`).
