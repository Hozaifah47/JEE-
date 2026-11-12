# 03_DATABASE — Database Structure & Reference

## Overview

The `03_DATABASE/` folder is the central data store for all extracted and processed JEE Main PYQ data. It is populated progressively by the pipeline scripts.

---

## Files

### `questions.jsonl`
One JSON object per line. Each line = one question. Schema:
```json
{
  "question_id":           "PHY-2024-0129-S1-Q001",
  "subject":               "Physics",
  "chapter":               "Electrostatics",
  "chapter_id":            "PHY-11",
  "topic":                 "Electric Field due to Continuous Charge Distribution",
  "concept":               "Gauss Law Application",
  "cluster_id":            "PHY-ELECTRO-C03",
  "year":                  2024,
  "date":                  "2024-01-29",
  "shift":                 1,
  "question_number":       5,
  "question_type":         "MCQ",
  "question_text":         "...",
  "options":               {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct_answer":        "B",
  "difficulty":            "moderate",
  "source_file":           "JEE-2024-0129-S1",
  "source_page":           3,
  "extraction_confidence": 0.92,
  "review_required":       false
}
```

### `questions.csv`
Flat CSV version of questions.jsonl. Excludes full option text. Good for quick filtering and Excel analysis.

Columns: `question_id, subject, chapter, topic, concept, cluster_id, year, date, shift, question_number, question_type, question_text, correct_answer, difficulty, source_file, source_page, extraction_confidence, review_required`

### `clusters.json`
Groups of questions with similar problem-solving approaches.
```json
{
  "clusters": [
    {
      "cluster_id":        "PHY-ELECTRO-C01",
      "subject":           "Physics",
      "chapter":           "Electrostatics",
      "cluster_name":      "Coulomb's Law — Two Point Charges",
      "description":       "Direct application of Coulomb's law to find force between point charges",
      "similarity_level":  1,
      "question_ids":      ["PHY-2021-0224-S1-Q12", "PHY-2022-0625-S2-Q08"],
      "frequency":         2,
      "years_appeared":    [2021, 2022],
      "predicted_weight":  "HIGH"
    }
  ]
}
```

### `concepts.json`
Master concept list auto-populated during classification.
```json
{
  "concepts": [
    {
      "concept_id":   "PHY-ELECTRO-CON-01",
      "name":         "Gauss Law",
      "chapter_id":   "PHY-11",
      "question_ids": [],
      "frequency":    0
    }
  ]
}
```

### `chapter_taxonomy.json`
Full JEE Main chapter taxonomy for all three subjects with keyword lists for classification. Used by `classify_questions.py` to match questions to chapters.

---

## Data Flow

```
01_RAW_PYQS/YYYY/*.pdf
        │
        ▼ ingest.py
00_ADMIN/source_inventory.csv + master_manifest.json
        │
        ▼ extract_questions.py
03_DATABASE/questions.jsonl  +  questions.csv
02_EXTRACTED_DATA/{Subject}/  +  00_ADMIN/question_inventory.csv
        │
        ▼ classify_questions.py
questions.jsonl  (chapter/topic/concept fields filled)
chapter_taxonomy.json  (question_count updated)
        │
        ▼ cluster_questions.py
clusters.json  (clusters created)
questions.jsonl  (cluster_id filled)
        │
        ▼ analyse_trends.py
04_MASTER_REPORTS/trends_data.json  +  per-chapter stats
        │
        ▼ generate_html.py
04_MASTER_REPORTS/index.html  +  subject/chapter/cluster HTML files
```

---

## ID Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| File ID | `JEE-YYYY-MMDD-SN` | `JEE-2024-0129-S1` |
| Question ID | `{SUBJ}-YYYY-MMDD-SN-Q###` | `PHY-2024-0129-S1-Q001` |
| Cluster ID | `{SUBJ}-{CHAPTERCODE}-C##` | `PHY-ELECTRO-C01` |
| Concept ID | `{SUBJ}-{CHAPTERCODE}-CON-##` | `PHY-ELECTRO-CON-01` |

Where SUBJ ∈ {PHY, CHEM, MATH} and SN ∈ {S1, S2}

---

## Notes

- `questions.jsonl` is append-safe: re-running extract_questions.py skips already-extracted papers (by source_file id).
- `review_required: true` marks questions needing manual verification (low confidence extraction or classification).
- Never edit jsonl/csv files manually while scripts are running.
