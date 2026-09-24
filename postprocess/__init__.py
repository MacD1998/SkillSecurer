"""Post-processing: confronti fra run già eseguite (nessuna chiamata LLM).

`run_index`  → scopre le run in results/ e le raggruppa per dataset di input.
`comparison_report` → genera il report comparativo (HTML + JSON) su N run che
condividono lo stesso dataset.
"""
