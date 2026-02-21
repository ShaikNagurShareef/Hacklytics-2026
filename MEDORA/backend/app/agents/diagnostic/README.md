# Diagnostic Imaging Agent — ACR Report Structure

Report layout and section order are defined by the **ACR Practice Parameter for Communication of Diagnostic Imaging Findings**. All report generation (prompts, schema, PDF) uses a single source of truth so the output is consistent and auditable.

## Single source of truth

- **`acr_report_structure.py`** — Canonical ACR section order, section titles, and references.  
  - `ACR_SECTIONS`: ordered list of (key, title, description).  
  - `ACR_SECTION_KEYS` / `ACR_SECTION_HEADERS`: keys and display headers.  
  - `ACR_CRITICAL_FINDINGS_DISCLAIMER`: text for critical-findings communication per ACR.

## References

- **ACR Practice Parameter for Communication of Diagnostic Imaging Findings**  
  Final report components: (1) Demographics, (2) Relevant Clinical Information, (3) Body of Report (detailed description of findings). Critical findings require timely communication to the referring physician and/or patient.

- **Standard report body** (RSNA / RadiologyInfo.org):  
  Indication → Comparison → Technique → Findings → Impression → Recommendations.

## How it’s used

| Component | Role |
|-----------|------|
| `acr_report_structure.py` | Defines section order and titles; referenced by prompts and tools. |
| `prompts.py` | `REPORT_GENERATION_PROMPT` is built from `ACR_SECTIONS` so the LLM outputs the same order. |
| `schemas.py` | `DiagnosticReport` fields are documented and ordered to match ACR sections. |
| `tools.py` | `format_critical_alert()` uses `ACR_CRITICAL_FINDINGS_DISCLAIMER`; PDF assumes report text follows ACR order. |

To change report structure (add/remove/rename sections), update `acr_report_structure.py` and any prompt instructions in `prompts._build_acr_report_prompt()` that map section keys to instructions.
