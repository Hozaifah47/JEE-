#!/usr/bin/env python3
"""
cluster_questions.py — JEE Main PYQ Analysis System
Clusters questions by problem-solving approach within each chapter.

Usage:
    python 07_SCRIPTS/cluster_questions.py
    python 07_SCRIPTS/cluster_questions.py --subject Physics
    python 07_SCRIPTS/cluster_questions.py --chapter Electrostatics
"""

import json
import csv
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parent.parent
ADMIN_DIR      = PROJECT_ROOT / "00_ADMIN"
DATABASE_DIR   = PROJECT_ROOT / "03_DATABASE"
LOG_DIR        = PROJECT_ROOT / "08_LOGS"

QUESTIONS_JSONL = DATABASE_DIR / "questions.jsonl"
QUESTIONS_CSV   = DATABASE_DIR / "questions.csv"
CLUSTERS_FILE   = DATABASE_DIR / "clusters.json"
TAXONOMY_FILE   = DATABASE_DIR / "chapter_taxonomy.json"
ANALYSIS_LOG    = LOG_DIR      / "analysis.log"
STATUS_FILE     = ADMIN_DIR    / "project_status.json"

QUESTION_CSV_HEADERS = [
    "question_id", "subject", "chapter", "topic", "concept", "cluster_id",
    "year", "date", "shift", "question_number", "question_type",
    "question_text", "correct_answer", "difficulty",
    "source_file", "source_page", "extraction_confidence", "review_required"
]

# ── Cluster Rules (per subject → chapter → clusters) ─────────────────────────
# Each cluster entry: (cluster_suffix, description, keyword_patterns)
CLUSTER_RULES = {
    "Physics": {
        "Electrostatics": [
            ("COULOMB",   "Coulomb's Law & Electric Force",           ["coulomb", "force between charge", "point charge", "distance between"]),
            ("EFIELD",    "Electric Field (Point/Line/Surface)",      ["electric field", "field due to", "charge distribution", "field intensity"]),
            ("GAUSS",     "Gauss's Law & Flux",                       ["gauss", "flux", "gaussian surface", "enclosed charge"]),
            ("POTENTIAL", "Electric Potential & Potential Energy",    ["potential", "work done", "potential energy", "equipotential"]),
            ("CAPACITOR", "Capacitors & Capacitance",                 ["capacitor", "capacitance", "dielectric", "parallel plate"]),
            ("DIPOLE",    "Electric Dipole",                          ["dipole", "dipole moment", "torque on dipole"]),
        ],
        "Current Electricity": [
            ("OHM",       "Ohm's Law & Resistance",                   ["resistance", "ohm", "resistivity", "conductivity"]),
            ("KIRCHHOFF", "Kirchhoff's Laws & Circuit Analysis",      ["kirchhoff", "KVL", "KCL", "loop", "junction"]),
            ("METER",     "Galvanometer, Ammeter & Voltmeter",        ["galvanometer", "ammeter", "voltmeter", "shunt", "meter bridge"]),
            ("POTENT",    "Potentiometer",                            ["potentiometer", "null point", "EMF comparison"]),
            ("WHEATSTONE","Wheatstone Bridge",                        ["wheatstone", "balanced bridge", "bridge circuit"]),
        ],
        "Kinematics": [
            ("1D",        "1D Motion (Uniform/Non-Uniform)",          ["1D", "one dimension", "speed", "velocity time", "distance time"]),
            ("2D",        "2D Motion & Projectile",                   ["projectile", "2D", "horizontal", "range", "angle of projection"]),
            ("RELATIVE",  "Relative Motion",                          ["relative", "rain", "river", "reference frame"]),
        ],
        "Oscillations": [
            ("SHM_BASIC", "SHM Basics — Displacement/Velocity/Acc.", ["amplitude", "phase", "SHM", "simple harmonic"]),
            ("SHM_ENERGY","SHM Energy",                               ["energy in SHM", "kinetic energy SHM", "potential energy SHM"]),
            ("PENDULUM",  "Pendulum",                                  ["pendulum", "time period", "simple pendulum", "compound pendulum"]),
            ("SPRING",    "Spring-Mass System",                       ["spring", "spring constant", "spring mass", "spring combination"]),
        ],
        "Ray Optics": [
            ("MIRROR",    "Spherical Mirrors",                        ["mirror", "concave", "convex", "focal length mirror", "mirror formula"]),
            ("REFRACTION","Refraction & Snell's Law",                 ["refraction", "snell", "refractive index", "critical angle", "TIR"]),
            ("LENS",      "Lenses & Lens Formula",                    ["lens", "convex lens", "concave lens", "lens formula", "power of lens"]),
            ("PRISM",     "Prism & Dispersion",                       ["prism", "deviation", "dispersion", "spectrum", "minimum deviation"]),
        ],
    },
    "Chemistry": {
        "Electrochemistry": [
            ("NERNST",    "Nernst Equation & Cell EMF",               ["nernst", "cell EMF", "electrode potential", "standard electrode"]),
            ("ELECTROLYSIS","Electrolysis & Faraday's Laws",          ["electrolysis", "faraday", "charge passed", "deposited", "plating"]),
            ("CONDUCTANCE","Conductance & Kohlrausch Law",            ["conductance", "kohlrausch", "molar conductance", "limiting"]),
        ],
        "Chemical Kinetics": [
            ("RATE",      "Rate of Reaction & Rate Law",              ["rate of reaction", "rate law", "rate constant", "order"]),
            ("ARRHENIUS", "Arrhenius Equation & Activation Energy",   ["arrhenius", "activation energy", "temperature dependence", "Ea"]),
            ("HALFLIFE",  "Half-Life Calculations",                   ["half life", "t1/2", "first order", "radioactive decay"]),
        ],
        "Coordination Compounds": [
            ("NOMENCLATURE","Nomenclature of Complexes",              ["nomenclature", "IUPAC name", "naming complex"]),
            ("ISOMERISM",  "Isomerism in Complexes",                  ["isomerism", "geometric isomer", "optical isomer", "linkage isomer"]),
            ("CFSE",       "Crystal Field Theory & CFSE",             ["CFSE", "crystal field", "d-orbital splitting", "strong field", "weak field"]),
            ("EAN",        "EAN Rule & Stability",                    ["EAN", "effective atomic number", "stability constant"]),
        ],
    },
    "Mathematics": {
        "Integration": [
            ("DEFINITE",  "Definite Integrals & Properties",          ["definite integral", "limits of integration", "property of integral"]),
            ("BYPARTS",   "Integration by Parts",                     ["by parts", "ILATE", "integration by parts"]),
            ("SUBST",     "Substitution Method",                      ["substitution", "let", "u-substitution"]),
            ("PARTIAL",   "Partial Fractions",                        ["partial fraction", "denominator factorize"]),
            ("AREA",      "Area Under Curve",                         ["area", "bounded", "region", "between curves"]),
        ],
        "Vectors": [
            ("DOTCROSS",  "Dot & Cross Product",                      ["dot product", "cross product", "scalar product", "vector product"]),
            ("TRIPLEPRODUCT","Triple Product",                        ["scalar triple", "vector triple", "coplanar"]),
            ("GEOMETRY",  "Vector Geometry Problems",                 ["position vector", "collinear", "midpoint", "section formula"]),
        ],
        "3D Geometry": [
            ("LINE3D",    "Line in 3D Space",                         ["direction cosines", "direction ratios", "line in 3D", "symmetric form"]),
            ("PLANE",     "Plane in 3D",                              ["equation of plane", "normal to plane", "distance from plane"]),
            ("DISTANGLE", "Distance & Angle",                         ["shortest distance", "angle between", "distance between lines"]),
        ],
        "Probability": [
            ("BASIC",     "Basic Probability",                        ["probability", "sample space", "event", "P(A)"]),
            ("BAYES",     "Conditional Probability & Bayes",          ["conditional", "Bayes", "P(A|B)", "posterior"]),
            ("DISTRIBUTION","Binomial & Other Distributions",         ["binomial distribution", "Bernoulli", "mean of distribution", "variance"]),
        ],
    }
}

SUBJECT_CODES  = {"Physics": "PHY", "Chemistry": "CHEM", "Mathematics": "MATH"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def chapter_code(chapter_name: str) -> str:
    """Generate a short uppercase code from chapter name."""
    words = re.sub(r"[^A-Za-z ]", "", chapter_name).split()
    if len(words) >= 2:
        return "".join(w[:4].upper() for w in words[:2])
    return chapter_name[:8].upper().replace(" ", "")


def load_questions() -> list:
    questions = []
    if not QUESTIONS_JSONL.exists():
        return questions
    with open(QUESTIONS_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                questions.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return questions


def save_questions(questions: list):
    with open(QUESTIONS_JSONL, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    with open(QUESTIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QUESTION_CSV_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for q in questions:
            writer.writerow(q)


def match_cluster(text: str, rules: list) -> tuple:
    """
    Match question text against cluster rules.
    Returns (cluster_suffix, description) or (None, None).
    """
    text_lower = text.lower()
    best_suffix = None
    best_desc   = None
    best_score  = 0

    for suffix, description, keywords in rules:
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score   = score
            best_suffix  = suffix
            best_desc    = description
    return (best_suffix, best_desc) if best_score > 0 else (None, None)


def assign_similarity_level(q_ids: list) -> int:
    """Assign similarity level based on cluster size."""
    n = len(q_ids)
    if n >= 5:
        return 1   # Near-identical, very high frequency
    elif n >= 2:
        return 2   # Same concept, different presentation
    else:
        return 3   # Related, low frequency


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Cluster questions by problem-solving approach.")
    parser.add_argument("--subject",   help="Process only this subject.")
    parser.add_argument("--chapter",   help="Process only this chapter.")
    args = parser.parse_args()

    log("=" * 60)
    log("JEE Main PYQ — Cluster Questions")

    questions = load_questions()
    if not questions:
        log("No questions found. Run extract_questions.py first.", "WARN")
        sys.exit(0)

    log(f"Loaded {len(questions)} questions")

    # Group by subject → chapter
    by_chapter = defaultdict(list)
    for q in questions:
        subj = q.get("subject", "")
        chap = q.get("chapter", "")
        if args.subject and subj != args.subject:
            continue
        if args.chapter and chap != args.chapter:
            continue
        if chap:
            by_chapter[(subj, chap)].append(q)

    # Build clusters
    # cluster_map: cluster_id → {question_ids, years, etc.}
    cluster_map = {}
    fallback_counters = defaultdict(int)

    for (subject, chapter), qs in sorted(by_chapter.items()):
        subj_code = SUBJECT_CODES.get(subject, "UNK")
        chap_code = chapter_code(chapter)
        rules     = CLUSTER_RULES.get(subject, {}).get(chapter, [])

        # Map: (cluster_suffix) → list of question IDs
        cluster_buckets = defaultdict(list)

        for q in qs:
            q_text = q.get("question_text", "")
            q_id   = q["question_id"]

            if rules:
                suffix, desc = match_cluster(q_text, rules)
            else:
                suffix, desc = None, None

            if suffix:
                cluster_key = f"{subj_code}-{chap_code}-{suffix}"
                cluster_buckets[cluster_key].append((q_id, desc or chapter))
            else:
                # Generic cluster
                fallback_counters[(subject, chapter)] += 1
                n = fallback_counters[(subject, chapter)]
                cluster_key = f"{subj_code}-{chap_code}-GEN{n:02d}"
                cluster_buckets[cluster_key].append((q_id, f"{chapter} — General"))

        # Build cluster entries and assign cluster_id back to questions
        q_lookup = {q["question_id"]: q for q in qs}
        for c_id, q_entries in cluster_buckets.items():
            q_ids = [e[0] for e in q_entries]
            desc  = q_entries[0][1] if q_entries else chapter

            years_appeared = sorted({
                q_lookup[qid]["year"]
                for qid in q_ids
                if qid in q_lookup
            })
            sim_level = assign_similarity_level(q_ids)

            if c_id not in cluster_map:
                cluster_map[c_id] = {
                    "cluster_id":       c_id,
                    "subject":          subject,
                    "chapter":          chapter,
                    "cluster_name":     desc,
                    "description":      f"Questions clustering around: {desc}",
                    "similarity_level": sim_level,
                    "question_ids":     q_ids,
                    "frequency":        len(q_ids),
                    "years_appeared":   years_appeared,
                    "predicted_weight": "HIGH" if len(q_ids) >= 5 else "MEDIUM" if len(q_ids) >= 2 else "LOW",
                }
            else:
                cluster_map[c_id]["question_ids"].extend(q_ids)
                cluster_map[c_id]["frequency"]  = len(cluster_map[c_id]["question_ids"])
                cluster_map[c_id]["years_appeared"] = sorted(set(cluster_map[c_id]["years_appeared"] + years_appeared))

            # Assign cluster_id to each question
            for qid in q_ids:
                if qid in q_lookup:
                    q_lookup[qid]["cluster_id"] = c_id

    # Save clusters.json
    clusters_out = {"clusters": list(cluster_map.values())}
    with open(CLUSTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(clusters_out, f, indent=2)

    # Save updated questions
    save_questions(questions)

    # Update status
    with open(STATUS_FILE, encoding="utf-8") as f:
        status = json.load(f)
    clustered = sum(1 for q in questions if q.get("cluster_id"))
    status["questions_clustered"] = clustered
    status["last_action"]  = f"Clustered questions into {len(cluster_map)} clusters"
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print(f"{'CLUSTERING SUMMARY':^60}")
    print("=" * 60)
    print(f"  Total clusters created  : {len(cluster_map)}")
    print(f"  Questions with cluster  : {clustered}")
    print(f"  Chapters covered        : {len(by_chapter)}")
    print()
    print(f"  Top clusters by frequency:")
    for c in sorted(cluster_map.values(), key=lambda x: -x["frequency"])[:15]:
        print(f"    {c['cluster_id']:<30} {c['frequency']:>4} Qs  [{', '.join(str(y) for y in c['years_appeared'])}]")
    print("=" * 60)
    print("\nNext step: python 07_SCRIPTS/analyse_trends.py")


if __name__ == "__main__":
    main()
