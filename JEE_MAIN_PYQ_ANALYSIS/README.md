# JEE Main PYQ Analysis & Question-Clustering System

A comprehensive, locally stored, and searchable JEE Main Previous Year Question (PYQ) analysis system built on **90 original examination papers** spanning **2021 to 2025** across all sessions and shifts for **Physics**, **Chemistry**, and **Mathematics**.

---

## 🌟 Key Features & Highlights

1. **Complete Database of 7,959 Questions:**
   - 90 official MathonGo papers fully ingested and parsed.
   - Structured JSONL and CSV records containing Question ID, Subject, Chapter, Topic, Problem-Solving Cluster, Options, Answers, Difficulty, and Source metadata.
2. **Comprehensive Problem-Solving Clusters across ALL 73 Chapters:**
   - **231 structured problem-solving archetypes** grouping questions by their underlying mathematical/physical method rather than superficial keywords.
   - Dedicated cluster directories for all chapters containing:
     - `index.html`: Archetype concept overview, formula sheet, and priority badge.
     - `questions.html`: All historical PYQs in that archetype with interactive answer toggles.
     - `cluster_analysis.html`: Deep-dive analysis on solution sequences and common examination pitfalls.
     - `answers.html`: Dedicated answer keys.
3. **Three-Bucket Strategic Preparation System (`09_PRIORITY_SYSTEM/`):**
   - **Bucket 1 (High Priority / Master First):** 25 high-yield chapters (Target ~48-52 Physics/Chem, ~28-32 Math).
   - **Bucket 2 (Expansion / Booster):** 28 comprehensive syllabus expansion chapters (~+65 Marks).
   - **Bucket 3 (Formula-Only / Restricted Zone):** 11 chapters focused exclusively on standard formulas and recurring archetypes to optimize preparation time.
   - **Bucket Conflict Analysis:** Flags chapters where historical PYQ frequency diverges from initial assumptions (e.g., Equilibrium & Waves).
4. **Master PCM Weightage Ranking (`00_HIGHEST_WEIGHTAGE_PCM.html` & `.pdf`):**
   - Ranked cross-subject table of all chapters by historical question count.
   - Subject-wise breakdowns (Physics, Chemistry by Physical/Organic/Inorganic, Mathematics).
   - 5-year progression tables (2021–2025), distinct shift counts, and horizontal bar charts.
5. **Interactive Practice Library (`05_PRACTICE_SETS/`):**
   - **526 interactive practice HTML files** covering every chapter and cluster.
   - Interactive JavaScript **[Show Answer]** toggles ensuring solutions are never spoiled prematurely.
   - Mixed PCM challenge sets for Bucket 1, Bucket 2, and Bucket 3.
6. **Zero-Error Validation Guarantee:**
   - Validated against strict integrity rules (`00_ADMIN/quality_control_report.html`) with **0 Errors**.

---

## 📁 Project Directory Structure

```text
JEE_MAIN_PYQ_ANALYSIS/
│
├── README.md                                  # Comprehensive System Documentation
├── index.html                                 # Master Interactive Dashboard
├── 00_HIGHEST_WEIGHTAGE_PCM.html              # Master Weightage Ranking across PCM
├── 00_HIGHEST_WEIGHTAGE_PCM.pdf               # Printable Weightage Report
│
├── 00_ADMIN/                                  # Project Audit & Quality Control
│   ├── master_manifest.json                   # Ingested paper manifest
│   ├── source_inventory.csv                   # Paper registry with shift & page metadata
│   ├── question_inventory.csv                 # Complete question index
│   ├── project_status.json                    # Real-time state machine tracking
│   ├── quality_control_report.html            # Database validation report (0 Errors)
│   └── coverage_report.html                   # Year & shift coverage analysis
│
├── 01_RAW_PYQS/                               # 90 Original PYQ Papers (Preserved)
│   ├── 2021/                                  # 25 examination papers
│   ├── 2022/                                  # 12 examination papers
│   ├── 2023/                                  # 23 examination papers
│   ├── 2024/                                  # 20 examination papers
│   └── 2025/                                  # 10 examination papers
│
├── 02_EXTRACTED_DATA/                         # Plaintext Dumps by Subject
│   ├── Physics/
│   ├── Chemistry/
│   └── Mathematics/
│
├── 03_DATABASE/                               # Normalized Database Files
│   ├── questions.jsonl                        # 7,959 complete structured question records
│   ├── questions.csv                          # Searchable CSV database
│   ├── clusters.json                          # 231 problem-solving cluster archetypes
│   ├── chapter_taxonomy.json                  # Official 73-chapter PCM taxonomy
│   └── priority_metadata.json                 # Chapter-level priority scores and metrics
│
├── 04_MASTER_REPORTS/                         # Master Analytical Reports & Subject Suites
│   ├── overall_analysis.html & .pdf           # 5-Year cross-subject analytical synthesis
│   ├── Physics_report.html & .pdf             # Physics comprehensive examination report
│   ├── Chemistry_report.html & .pdf           # Chemistry comprehensive examination report
│   ├── Mathematics_report.html & .pdf         # Mathematics comprehensive examination report
│   ├── high_priority_clusters.html            # Top recurring question archetypes
│   ├── chapter_frequency.csv                  # Frequency metrics per chapter
│   └── cluster_frequency.csv                  # Frequency metrics per cluster
│
├── 05_PRACTICE_SETS/                          # 526 Interactive Practice HTML Files
│   ├── index.html                             # Practice Library Hub
│   ├── bucket_1_mixed_practice.html           # 30-Question Bucket 1 PCM Mock
│   ├── bucket_2_mixed_practice.html           # 30-Question Bucket 2 PCM Mock
│   ├── bucket_3_mixed_practice.html           # 20-Question Bucket 3 PCM Mock
│   ├── Physics/                               # Chapter & cluster tests with answer toggles
│   ├── Chemistry/                             # Chapter & cluster tests with answer toggles
│   └── Mathematics/                           # Chapter & cluster tests with answer toggles
│
├── 06_ASSETS/                                 # Styling & Static Assets
│   └── styles/main.css                        # Responsive typography & color themes
│
├── 07_SCRIPTS/                                # Automated Pipeline Toolchain
│   ├── ingest.py                              # Scans and registers raw PDF exam papers
│   ├── extract_questions.py                   # PyMuPDF text & question extraction
│   ├── classify_questions.py                  # Taxonomy keyword classification
│   ├── reclassify_unclassified.py             # Multi-pass regex classification
│   ├── cluster_questions.py                   # Cluster assignment logic
│   ├── recluster_all_chapters.py              # Semantic reclustering across all 73 chapters
│   ├── generate_all_cluster_pages.py          # Cluster HTML directory generator
│   ├── generate_practice_sets.py              # Practice library generator (526 files)
│   ├── analyse_trends.py                      # Multi-year trend & recurrence analytics
│   ├── build_priority_and_weightage.py        # Master dashboard and priority builder
│   └── validate_database.py                   # Database QC and schema validator
│
├── 08_LOGS/                                   # Traceable Processing Logs
│   ├── ingestion.log
│   ├── extraction.log
│   └── analysis.log
│
├── 09_PRIORITY_SYSTEM/                        # Three-Bucket Strategy Portal
│   ├── index.html                             # Priority Dashboard
│   ├── priority_dashboard.pdf                 # Printable Strategy Framework
│   ├── priority_comparison.html & .pdf        # Full Chapter Priority Matrix
│   ├── bucket_1_high_priority/                # High-yield chapter drill-downs
│   ├── bucket_2_expansion/                    # Expansion chapter drill-downs
│   └── bucket_3_restricted/                   # Formula-only chapter drill-downs
│
├── Physics/chapters/[Chapter]/                # 22 Physics Chapter Directories
│   └── clusters/[Cluster_ID]/                 # 4-file cluster suites (index, questions, analysis, answers)
│
├── Chemistry/[Branch]/[Chapter]/              # 27 Chemistry Chapter Directories (Physical/Organic/Inorganic)
│   └── clusters/[Cluster_ID]/                 # 4-file cluster suites (index, questions, analysis, answers)
│
└── Mathematics/chapters/[Chapter]/            # 24 Mathematics Chapter Directories
    └── clusters/[Cluster_ID]/                 # 4-file cluster suites (index, questions, analysis, answers)
```

---

## 🎯 Strategic Preparation Framework (The 3 Buckets)

### Bucket 1: High Priority (Master First)
*Target: ~48–52 Marks (Phy/Chem), ~28–32 Marks (Math)*
- **Physics:** Units & Measurements, Modern Physics (Dual Nature, Atoms, Nuclei), Semiconductors, EM Waves, Current Electricity, Electrostatics & Capacitors, Ray Optics.
- **Chemistry:** Periodic Table, Chemical Bonding, Coordination Compounds, d- & f-Block Elements, Basic Organic Chemistry (GOC & Isomerism), Biomolecules, Solutions, Chemical Kinetics, Electrochemistry.
- **Mathematics:** Vectors & 3D Geometry (Highest Priority, 3–4 questions target), Matrices, Determinants, Sequences & Series, Statistics, Quadratic Equations, Binomial Theorem.

### Bucket 2: Expansion / Booster Block
*Target: ~+65 Additional Marks*
- **Physics:** Thermal Physics / KTG, Magnetism & Matter, Magnetic Effects, EMI & AC, Wave Optics, Gravitation, Core Mechanics (Kinematics, NLM, Work Energy Power).
- **Chemistry:** Atomic Structure, Thermodynamics, Mole Concept & Redox, Hydrocarbons, Haloalkanes, Alcohols/Phenols, Aldehydes/Ketones, Amines, p-Block.
- **Mathematics:** Sets & Relations, Limits, Continuity & Differentiability, Straight Lines & Circles, Integration, Differential Equations, Probability.

### Bucket 3: Formula-Only / Restricted Zone
*Target: Rapid Coverage of Standard Formulae & Recurring Archetypes Only*
- **Physics:** Rotational Motion, Fluid Mechanics (Properties of Matter), SHM & Waves.
- **Chemistry:** Ionic Equilibrium (pH, Buffers, Ksp), States of Matter / Salt Analysis, Surface Chemistry.
- **Mathematics:** Complex Numbers, Permutations & Combinations, Conic Sections (Parabola, Ellipse, Hyperbola), Application of Derivatives (Max/Min), Trigonometry.

---

## 🛠️ Execution Toolchain Commands

All data processing scripts are self-contained and located in `07_SCRIPTS/`:

```bash
# 1. Ingest newly added papers from 01_RAW_PYQS/
python3 07_SCRIPTS/ingest.py

# 2. Extract questions from all registered PDFs
python3 07_SCRIPTS/extract_questions.py

# 3. Classify questions into chapters
python3 07_SCRIPTS/classify_questions.py
python3 07_SCRIPTS/reclassify_unclassified.py

# 4. Re-cluster all questions into syllabus archetypes
python3 07_SCRIPTS/recluster_all_chapters.py

# 5. Build individual cluster pages and practice sets
python3 07_SCRIPTS/generate_all_cluster_pages.py
python3 07_SCRIPTS/generate_practice_sets.py

# 6. Analyze multi-year trends & build weightage and priority dashboards
python3 07_SCRIPTS/analyse_trends.py
python3 07_SCRIPTS/build_priority_and_weightage.py

# 7. Validate database integrity
python3 07_SCRIPTS/validate_database.py
```

---

## 📊 Quick Links for Local Browsing

- **Master Dashboard:** [`index.html`](index.html)
- **PCM Weightage Report:** [`00_HIGHEST_WEIGHTAGE_PCM.html`](00_HIGHEST_WEIGHTAGE_PCM.html) / [`00_HIGHEST_WEIGHTAGE_PCM.pdf`](00_HIGHEST_WEIGHTAGE_PCM.pdf)
- **Priority System Portal:** [`09_PRIORITY_SYSTEM/index.html`](09_PRIORITY_SYSTEM/index.html)
- **Practice Hub:** [`05_PRACTICE_SETS/index.html`](05_PRACTICE_SETS/index.html)
- **Quality Control Audit:** [`00_ADMIN/quality_control_report.html`](00_ADMIN/quality_control_report.html)
