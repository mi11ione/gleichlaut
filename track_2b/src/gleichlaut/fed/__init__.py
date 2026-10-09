"""Fedlex lane (Gleichschritt): federal statute amendments, DE paragraph changed -> FR/IT draft by Apertus 8B.

lane     fed_draft / arm_a / arm_b / live_slice: the research loop of research/gleich.py executed via ast, `ask` injected
score    replay scorer: research/score.py executed on the recorded runs; results.md reproduced; replay test
ingest   SPARQL + filestore AKN XML (cached, rate-limited; offline by default) -> consolidated versions, aligned leaves
mine     two consecutive versions -> change items (the build_fed.py filters, make_items.py item shape)

All of it is stdlib; `lane` and `score` use the frozen lock from gleichlaut.core, every module uses core's ast extractor."""
