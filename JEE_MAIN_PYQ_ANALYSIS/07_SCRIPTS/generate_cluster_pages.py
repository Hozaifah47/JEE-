#!/usr/bin/env python3
"""
generate_cluster_pages.py
Generates individual cluster analysis pages for significant clusters (≥2 questions).
Creates: index.html, questions.html, cluster_analysis.html, answers.html
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path("/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS")
DB = ROOT / "03_DATABASE"

# ─── Shared CSS ─────────────────────────────────────────────────────────────
SHARED_CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;color:#212121;margin:0;padding:0}
.container{max-width:900px;margin:0 auto;padding:24px}
.card{background:#fff;border-radius:12px;padding:20px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,.1)}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:600;margin:2px}
.b1{background:#c8e6c9;color:#1b5e20}.b2{background:#ffe0b2;color:#e65100}.b3{background:#f8bbd0;color:#880e4f}
.phy{background:#bbdefb;color:#0d47a1}.chem{background:#c8e6c9;color:#1b5e20}.math{background:#e1bee7;color:#4a148c}
.easy{background:#a5d6a7;color:#1b5e20}.moderate{background:#fff9c4;color:#f57f17}.difficult{background:#ffcdd2;color:#c62828}
.year-badge{background:#e3f2fd;color:#1565c0;padding:3px 10px;border-radius:12px;font-size:.8rem;font-weight:600;margin:2px}
.answer-btn{background:#1a237e;color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:.9rem;margin-top:8px}
.answer-reveal{display:none;background:#e8f5e9;border-radius:8px;padding:12px;margin-top:8px;font-weight:700}
.question-block{background:#fff;border-radius:12px;padding:20px;margin:16px 0;box-shadow:0 2px 6px rgba(0,0,0,.08);border-left:4px solid #1a237e}
nav a{color:#1a237e;text-decoration:none;margin-right:12px;font-weight:500}
h1{color:#1a237e;border-bottom:3px solid #1a237e;padding-bottom:8px}
h2{color:#333;border-bottom:1px solid #e0e0e0;padding-bottom:4px}
table{width:100%;border-collapse:collapse;margin:12px 0}
th{background:#1a237e;color:#fff;padding:10px 14px;text-align:left}
td{padding:8px 14px;border-bottom:1px solid #e0e0e0}
tr:hover{background:#f5f5f5}
.sim-1{background:#c8e6c9;color:#1b5e20;padding:3px 10px;border-radius:8px;font-weight:700}
.sim-2{background:#ffe0b2;color:#e65100;padding:3px 10px;border-radius:8px;font-weight:700}
.sim-3{background:#e1bee7;color:#4a148c;padding:3px 10px;border-radius:8px;font-weight:700}
.high-weight{background:#ff5252;color:#fff;padding:3px 10px;border-radius:8px;font-weight:700}
.medium-weight{background:#ff9800;color:#fff;padding:3px 10px;border-radius:8px;font-weight:700}
.low-weight{background:#78909c;color:#fff;padding:3px 10px;border-radius:8px;font-weight:700}
.tip-box{background:#e8f4fd;border-left:4px solid #1a237e;padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0}
.trap-box{background:#fff3e0;border-left:4px solid #ff9800;padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0}
.formula-box{background:#f3e5f5;border-left:4px solid #7b1fa2;padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;font-family:monospace}
""".strip()

TOGGLE_JS = """
function toggleAnswer(id) {
    var el = document.getElementById('ans-' + id);
    el.style.display = el.style.display === 'block' ? 'none' : 'block';
}
""".strip()

# ─── Chemistry branch mapping ────────────────────────────────────────────────
CHEM_BRANCH = {
    # Physical
    "Some Basic Concepts of Chemistry": "Physical_Chemistry",
    "Some Basic Concepts": "Physical_Chemistry",
    "Atomic Structure": "Physical_Chemistry",
    "Chemical Bonding & Molecular Structure": "Physical_Chemistry",
    "Chemical Bonding": "Physical_Chemistry",
    "States of Matter": "Physical_Chemistry",
    "Thermodynamics": "Physical_Chemistry",
    "Equilibrium": "Physical_Chemistry",
    "Redox Reactions": "Physical_Chemistry",
    "Electrochemistry": "Physical_Chemistry",
    "Chemical Kinetics": "Physical_Chemistry",
    "Surface Chemistry": "Physical_Chemistry",
    "Solutions": "Physical_Chemistry",
    # Organic
    "Basic Organic Chemistry": "Organic_Chemistry",
    "Hydrocarbons": "Organic_Chemistry",
    "Haloalkanes & Haloarenes": "Organic_Chemistry",
    "Haloalkanes": "Organic_Chemistry",
    "Alcohols Phenols & Ethers": "Organic_Chemistry",
    "Alcohols": "Organic_Chemistry",
    "Aldehydes Ketones & Carboxylic Acids": "Organic_Chemistry",
    "Aldehydes Ketones Carboxylic Acids": "Organic_Chemistry",
    "Amines": "Organic_Chemistry",
    "Biomolecules": "Organic_Chemistry",
    "Polymers": "Organic_Chemistry",
    "Chemistry in Everyday Life": "Organic_Chemistry",
    # Inorganic
    "Periodic Properties": "Inorganic_Chemistry",
    "Hydrogen": "Inorganic_Chemistry",
    "s-Block Elements": "Inorganic_Chemistry",
    "s-Block": "Inorganic_Chemistry",
    "p-Block Elements": "Inorganic_Chemistry",
    "p-Block": "Inorganic_Chemistry",
    "d & f Block Elements": "Inorganic_Chemistry",
    "d-Block": "Inorganic_Chemistry",
    "d & f Block": "Inorganic_Chemistry",
    "Coordination Compounds": "Inorganic_Chemistry",
    "Environmental Chemistry": "Inorganic_Chemistry",
}

# ─── Helpers ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.replace("&", "and").replace(" ", "_")
    text = re.sub(r"[^\w\-]", "", text)
    return text


def get_chem_branch(chapter: str) -> str:
    for key, branch in CHEM_BRANCH.items():
        if key.lower() in chapter.lower():
            return branch
    return "Inorganic_Chemistry"


def chapter_folder(subject: str, chapter: str) -> Path:
    if subject == "Physics":
        return ROOT / "Physics" / "chapters" / slugify(chapter)
    elif subject == "Chemistry":
        branch = get_chem_branch(chapter)
        return ROOT / "Chemistry" / branch / "chapters" / slugify(chapter)
    elif subject == "Mathematics":
        return ROOT / "Mathematics" / "chapters" / slugify(chapter)
    return ROOT / slugify(subject) / slugify(chapter)


def bucket_badge(bucket: int) -> str:
    if bucket == 1:
        return '<span class="badge b1">🟢 Bucket 1 — HIGH PRIORITY</span>'
    elif bucket == 2:
        return '<span class="badge b2">🟠 Bucket 2 — MEDIUM PRIORITY</span>'
    else:
        return '<span class="badge b3">🔴 Bucket 3 — LOW PRIORITY</span>'


def subject_badge(subject: str) -> str:
    css = {"Physics": "phy", "Chemistry": "chem", "Mathematics": "math"}.get(subject, "phy")
    return f'<span class="badge {css}">{subject}</span>'


def similarity_badge(level: int) -> str:
    labels = {1: "Near-identical", 2: "Same concept, different form", 3: "Related"}
    cls = {1: "sim-1", 2: "sim-2", 3: "sim-3"}
    return f'<span class="{cls.get(level,"sim-3")}">{level} — {labels.get(level,"Related")}</span>'


def weight_badge(weight: str) -> str:
    cls = {"HIGH": "high-weight", "MEDIUM": "medium-weight", "LOW": "low-weight"}
    return f'<span class="{cls.get(weight.upper(),"low-weight")}">{weight}</span>'


def infer_core_concept(cluster: dict) -> str:
    cid = cluster["cluster_id"]
    name = cluster.get("cluster_name", "")
    desc = cluster.get("description", "")

    # Use the name after the em-dash or the description if available
    if "—" in name:
        concept = name.split("—", 1)[1].strip()
    else:
        concept = name.strip()

    if not concept or concept == "General":
        # Fall back to cluster_id keywords
        parts = cid.split("-")
        if len(parts) >= 3:
            concept = " ".join(parts[2:]).replace("_", " ").title()

    return concept or desc


def infer_approach(cluster: dict) -> str:
    cid = cluster["cluster_id"]
    chapter = cluster.get("chapter", "")
    name = cluster.get("cluster_name", "")

    approaches = {
        "RATE": "Identify the rate law expression. Determine order from given data or by elimination. Apply rate = k[A]^m[B]^n. For integrated rate laws, use ln[A] vs t (1st order) or 1/[A] vs t (2nd order). Check units of k to confirm order.",
        "HALFLIFE": "Half-life: t₁/₂ = 0.693/k (1st order). For nth order: t₁/₂ ∝ [A]₀^(1-n). Convert between k and t₁/₂ as required.",
        "ARRHENIUS": "Apply Arrhenius equation: k = A·e^(-Ea/RT). Use ln(k₂/k₁) = (Ea/R)(1/T₁ - 1/T₂) for two-temperature problems. Activation energy from slope of ln k vs 1/T graph.",
        "OHM": "Apply V = IR. Identify series (same I) vs parallel (same V) configurations. Use equivalent resistance formulae. Kirchhoff's laws for complex networks.",
        "POWER": "P = IV = I²R = V²/R. Identify whether series or parallel to determine which element consumes more power.",
        "CELL": "EMF = ε - Ir (terminal voltage). For cells in series: add EMFs and internal resistances. For cells in parallel: use 1/r_eq = Σ(1/rᵢ) with weighted EMF.",
        "COULOMB": "F = kq₁q₂/r². Superposition principle for multiple charges. Field E = F/q = kq/r². Use direction (repulsion/attraction) carefully.",
        "FIELD": "E-field for point charge: E = kq/r². For line/plane/sphere: use Gauss's law. ∮E·dA = Q_enc/ε₀. Choose symmetric Gaussian surface.",
        "POTENTIAL": "V = kq/r. Work done W = q(V_A - V_B). Equipotential surfaces are ⊥ to field lines. For conductors: surface is equipotential.",
        "CAPACITOR": "C = ε₀A/d (parallel plate). Series: 1/C = Σ(1/Cᵢ). Parallel: C = ΣCᵢ. Energy U = ½CV² = Q²/2C. With dielectric: C' = KC.",
        "SHM": "a = -ω²x. ω = 2π/T. v = ω√(A²-x²). Energy: KE = ½mω²(A²-x²), PE = ½mω²x². For spring: ω = √(k/m). For pendulum: ω = √(g/L).",
        "DAMPED": "Amplitude decays as A = A₀e^(-bt/2m). Underdamped/overdamped/critical damping regimes. Quality factor Q = ω₀m/b.",
        "KINEMATICS": "Use SUVAT equations: v=u+at, s=ut+½at², v²=u²+2as. For projectile: horizontal (uniform) and vertical (g) are independent. Time of flight T=2u sinθ/g.",
        "PROJECTILE": "Range R = u²sin2θ/g (max at θ=45°). Max height H = u²sin²θ/2g. Resultant velocity at any point from components.",
        "RELATIVE": "Use relative velocity: v_AB = v_A - v_B. For river-boat: v_resultant = √(v_boat² + v_river²) or use vector addition.",
        "SNELL": "Snell's law: n₁sinθ₁ = n₂sinθ₂. TIR when θ ≥ θ_c where sinθ_c = n₂/n₁. Apply at each surface for multi-surface problems.",
        "MIRROR": "Mirror formula: 1/f = 1/v + 1/u. Magnification m = -v/u. Sign convention: incident ray direction is +ve. f = R/2.",
        "LENS": "Lens formula: 1/f = 1/v - 1/u. Power P = 1/f (metres). Lensmaker's: 1/f = (n-1)(1/R₁ - 1/R₂). Combined lenses: P = P₁ + P₂.",
        "INTEGRATION": "Identify form: standard integral, substitution, integration by parts (ILATE), or partial fractions. Check bounds for definite integrals.",
        "PROBABILITY": "P(A∪B) = P(A)+P(B)-P(A∩B). For conditional: P(A|B) = P(A∩B)/P(B). Bayes' theorem for reverse conditional. Count favourable/total outcomes carefully.",
        "VECTOR": "Dot product: a·b = |a||b|cosθ. Cross product: |a×b| = |a||b|sinθ. For unit vector: â = a/|a|. Projection of a on b = (a·b)/|b|.",
        "3D": "Direction cosines: l²+m²+n²=1. Line equation: (x-x₁)/a = (y-y₁)/b = (z-z₁)/c. Distance from point to plane = |ax₁+by₁+cz₁+d|/√(a²+b²+c²).",
        "COORDINATION": "Apply EAN rule, 18-electron rule. Use crystal field theory for d-orbital splitting. Identify geometry from CN. Apply spectrochemical series for colour/magnetism.",
        "ELECTROCHEM": "Nernst equation: E = E° - (RT/nF)ln Q. At equilibrium E=0, so ln K = nFE°/RT. Faraday: m = (M×I×t)/(n×F). Kohlrausch: Λm = Λm° - K√c.",
        "GEN": f"Carefully read the question stem for the specific application within {chapter}. Identify the given quantities, choose the correct formula, substitute and solve. Watch units and significant figures.",
    }

    # Match by keyword in cluster ID
    for key, approach in approaches.items():
        if key in cid:
            return approach

    # Subject-level fallback
    if "PHY" in cid:
        return f"Identify the physical law governing {chapter}. Write equations, substitute known values, solve for unknown. Check units/dimensions."
    elif "CHEM" in cid:
        return f"Identify the chemical principle or reaction type in {chapter}. Apply relevant equations or mechanisms step by step."
    elif "MATH" in cid:
        return f"Identify the mathematical technique for {chapter}. Set up the equation/expression, apply the relevant theorem or formula, simplify."
    return "Read carefully, identify key quantities, choose the correct formula, substitute and solve."


def infer_formulae(cluster: dict) -> list:
    cid = cluster["cluster_id"]
    formula_map = {
        "RATE": ["rate = k[A]^m[B]^n", "k units: (mol/L)^(1-n) s⁻¹", "1st order: ln[A] = ln[A]₀ - kt", "2nd order: 1/[A] = 1/[A]₀ + kt"],
        "HALFLIFE": ["t₁/₂ = 0.693/k (1st order)", "t₁/₂ = 1/(k[A]₀) (2nd order)", "t₁/₂ = [A]₀/(2k) (0th order)"],
        "ARRHENIUS": ["k = Ae^(-Ea/RT)", "ln(k₂/k₁) = (Ea/R)(1/T₁ - 1/T₂)"],
        "OHM": ["V = IR", "R_series = R₁+R₂+...", "1/R_parallel = 1/R₁ + 1/R₂ + ..."],
        "POWER": ["P = IV = I²R = V²/R"],
        "CELL": ["V_terminal = ε - Ir", "ε_total (series) = Σεᵢ", "i = Σεᵢ/rᵢ / Σ1/rᵢ (parallel)"],
        "COULOMB": ["F = kq₁q₂/r² = q₁q₂/(4πε₀r²)", "E = F/q = kq/r²"],
        "FIELD": ["E = kq/r² (point charge)", "∮E·dA = Q_enc/ε₀ (Gauss)"],
        "POTENTIAL": ["V = kq/r", "W = q(V_A - V_B)", "E = -dV/dr"],
        "CAPACITOR": ["C = ε₀A/d", "U = ½CV² = Q²/2C", "C_dielectric = Kε₀A/d"],
        "SHM": ["a = -ω²x", "T = 2π√(m/k)", "T_pendulum = 2π√(L/g)", "v = ω√(A²-x²)"],
        "SNELL": ["n₁sinθ₁ = n₂sinθ₂", "sinθ_c = n₂/n₁"],
        "MIRROR": ["1/f = 1/v + 1/u", "m = -v/u", "f = R/2"],
        "LENS": ["1/f = 1/v - 1/u", "P = 1/f(m)", "1/f = (n-1)(1/R₁-1/R₂)"],
        "INTEGRATION": ["∫xⁿdx = xⁿ⁺¹/(n+1)+C", "∫eˣdx = eˣ+C", "∫sinx dx = -cosx+C"],
        "PROBABILITY": ["P(A∪B) = P(A)+P(B)-P(A∩B)", "P(A|B) = P(A∩B)/P(B)", "P(Aᶜ) = 1-P(A)"],
        "VECTOR": ["a·b = |a||b|cosθ", "|a×b| = |a||b|sinθ", "|a×b| = area of parallelogram"],
        "3D": ["dist(point,plane) = |ax₁+by₁+cz₁+d|/√(a²+b²+c²)", "l²+m²+n² = 1"],
        "ELECTROCHEM": ["E = E° - (0.0592/n)log Q (25°C)", "m = MIt/(nF)", "Λm = Λm° - K√c"],
        "COORDINATION": ["Crystal field splitting: Δ_oct > Δ_tet", "CFSE = -0.4Δ per t₂g electron + 0.6Δ per eₓ electron"],
    }
    for key, fmls in formula_map.items():
        if key in cid:
            return fmls
    return ["Refer to chapter formulas"]


def infer_common_traps(cluster: dict) -> list:
    cid = cluster["cluster_id"]
    chapter = cluster.get("chapter", "")
    traps = {
        "RATE": ["Confusing rate constant units with order", "Using concentration in mol/L when mol/mL given", "Forgetting to account for stoichiometric coefficients"],
        "OHM": ["Wrong series/parallel identification", "Internal resistance ignored", "Sign errors in Kirchhoff's voltage law"],
        "CAPACITOR": ["Forgetting the factor of K (dielectric constant)", "Using wrong formula for energy when Q vs V is constant"],
        "SHM": ["Using displacement instead of amplitude", "Confusing ω (angular frequency) with f (frequency)", "Phase angle errors"],
        "SNELL": ["Applying TIR to wrong medium (must be denser→rarer)", "Angle measured from normal, not surface"],
        "MIRROR": ["Sign convention errors (u is always negative for real objects)", "Confusion between m (magnification) sign and image type"],
        "LENS": ["Using mirror formula instead of lens formula", "Sign of R₁, R₂ in lensmaker's equation"],
        "PROBABILITY": ["Not checking mutual exclusivity before adding", "Confusing P(A|B) with P(B|A)"],
        "VECTOR": ["Cross product is not commutative: a×b = -b×a", "Using wrong formula for projection vs component"],
        "3D": ["Direction cosines vs direction ratios mix-up", "Normal to plane from cross product of two lines"],
        "ELECTROCHEM": ["Confusing EMF with terminal voltage", "Forgetting n (electrons) in Faraday's law"],
    }
    for key, t in traps.items():
        if key in cid:
            return t
    return [
        f"Read the question carefully for the specific quantity asked in {chapter}",
        "Check units before substituting values",
        "Verify sign conventions appropriate to this topic",
    ]


def difficulty_badge(diff: str) -> str:
    if not diff:
        return '<span class="badge moderate">Moderate</span>'
    d = diff.lower()
    if d in ("easy", "low"):
        return '<span class="badge easy">Easy</span>'
    elif d in ("difficult", "hard", "high"):
        return '<span class="badge difficult">Difficult</span>'
    return '<span class="badge moderate">Moderate</span>'


def type_badge(qtype: str) -> str:
    if qtype and "integer" in qtype.lower():
        return '<span class="badge" style="background:#e8eaf6;color:#283593">Integer</span>'
    return '<span class="badge" style="background:#e3f2fd;color:#1565c0">MCQ</span>'


# ─── Page generators ─────────────────────────────────────────────────────────

def html_shell(title: str, body: str, extra_js: str = "") -> str:
    js_block = f"<script>{TOGGLE_JS}\n{extra_js}</script>" if extra_js else f"<script>{TOGGLE_JS}</script>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{SHARED_CSS}</style>
</head>
<body>
<div class="container">
{body}
</div>
{js_block}
</body>
</html>"""


def make_index_html(cluster: dict, questions: list, bucket: int, chapter_rel: str) -> str:
    cid = cluster["cluster_id"]
    name = cluster.get("cluster_name", cid)
    subject = cluster.get("subject", "")
    chapter = cluster.get("chapter", "")
    sim_level = cluster.get("similarity_level", 3)
    years = sorted(set(str(y) for y in cluster.get("years_appeared", [])))
    weight = cluster.get("predicted_weight", "LOW")
    core_concept = infer_core_concept(cluster)
    formulae = infer_formulae(cluster)
    approach = infer_approach(cluster)
    desc = cluster.get("description", "")

    years_html = " ".join(f'<span class="year-badge">{y}</span>' for y in years)
    formulae_html = "".join(f"<li><code>{f}</code></li>" for f in formulae)

    q_count = len(questions)
    diff_counts = {}
    for q in questions:
        d = q.get("difficulty", "") or "Unknown"
        diff_counts[d] = diff_counts.get(d, 0) + 1
    diff_html = " ".join(
        f'<span class="badge">{d}: {c}</span>' for d, c in diff_counts.items()
    )

    body = f"""
<nav>
  <a href="{chapter_rel}/index.html">← {chapter}</a>
  <a href="questions.html">📝 Questions</a>
  <a href="cluster_analysis.html">🔍 Analysis</a>
  <a href="answers.html">✅ Answers</a>
</nav>

<h1>{name}</h1>

<div class="card">
  <table>
    <tr><th style="width:35%">Field</th><th>Value</th></tr>
    <tr><td><strong>Cluster ID</strong></td><td><code>{cid}</code></td></tr>
    <tr><td><strong>Subject</strong></td><td>{subject_badge(subject)}</td></tr>
    <tr><td><strong>Chapter</strong></td><td>{chapter}</td></tr>
    <tr><td><strong>Priority Bucket</strong></td><td>{bucket_badge(bucket)}</td></tr>
    <tr><td><strong>Questions in Cluster</strong></td><td><strong>{q_count}</strong></td></tr>
    <tr><td><strong>Years Represented</strong></td><td>{years_html}</td></tr>
    <tr><td><strong>Similarity Level</strong></td><td>{similarity_badge(sim_level)}</td></tr>
    <tr><td><strong>Predicted Weight</strong></td><td>{weight_badge(weight)}</td></tr>
    <tr><td><strong>Difficulty Distribution</strong></td><td>{diff_html}</td></tr>
  </table>
</div>

<div class="card">
  <h2>🧠 Core Concept</h2>
  <p>{core_concept}</p>
  <h2>📐 Problem-Solving Approach</h2>
  <p>{approach}</p>
</div>

<div class="card">
  <h2>📋 Required Formulae</h2>
  <div class="formula-box">
    <ul style="margin:0;padding-left:20px">{formulae_html}</ul>
  </div>
</div>

<div class="card" style="display:flex;gap:12px;flex-wrap:wrap">
  <a href="questions.html" style="flex:1;min-width:140px;text-align:center;background:#1a237e;color:#fff;padding:16px;border-radius:10px;text-decoration:none;font-weight:600">
    📝 View All {q_count} Questions
  </a>
  <a href="cluster_analysis.html" style="flex:1;min-width:140px;text-align:center;background:#4a148c;color:#fff;padding:16px;border-radius:10px;text-decoration:none;font-weight:600">
    🔍 Cluster Analysis
  </a>
  <a href="answers.html" style="flex:1;min-width:140px;text-align:center;background:#1b5e20;color:#fff;padding:16px;border-radius:10px;text-decoration:none;font-weight:600">
    ✅ Answer Key
  </a>
</div>
"""
    return html_shell(f"{name} | Cluster Overview", body)


def make_questions_html(cluster: dict, questions: list, chapter_rel: str) -> str:
    cid = cluster["cluster_id"]
    name = cluster.get("cluster_name", cid)
    chapter = cluster.get("chapter", "")

    questions_html = ""
    for i, q in enumerate(questions, 1):
        qid = q.get("question_id", f"Q{i}")
        year = q.get("year", "")
        date = q.get("date", "")
        shift = q.get("shift", "")
        diff = q.get("difficulty", "")
        qtype = q.get("question_type", "MCQ")
        text = q.get("question_text", "").replace("<", "&lt;").replace(">", "&gt;")
        answer = q.get("correct_answer", "")
        options = q.get("options", {})

        opts_html = ""
        if qtype and "integer" in qtype.lower():
            opts_html = '<p><strong>Integer Answer:</strong> <em>(Enter a non-negative integer)</em></p>'
        elif options:
            opts_html = "<ul style='list-style:none;padding-left:0'>"
            for opt_key in ["A", "B", "C", "D", "1", "2", "3", "4"]:
                if opt_key in options and options[opt_key]:
                    val = str(options[opt_key]).replace("<", "&lt;").replace(">", "&gt;")
                    opts_html += f"<li style='margin:6px 0'><strong>({opt_key})</strong> {val}</li>"
            opts_html += "</ul>"
        else:
            opts_html = "<p><em>Options not available in database — refer to source paper.</em></p>"

        ans_display = answer if answer else "Not recorded"
        shift_label = f"Shift {shift}" if shift else "—"

        questions_html += f"""
<div class="question-block">
  <div style="margin-bottom:10px">
    <span class="year-badge">{year}</span>
    <span class="badge" style="background:#f5f5f5;color:#333">{date}</span>
    <span class="badge" style="background:#e8eaf6;color:#283593">{shift_label}</span>
    {difficulty_badge(diff)}
    {type_badge(qtype)}
  </div>
  <p><strong>Q{i}.</strong> {text}</p>
  {opts_html}
  <button class="answer-btn" onclick="toggleAnswer('{qid}')">Show Answer</button>
  <div class="answer-reveal" id="ans-{qid}">
    ✅ Correct Answer: <strong>{ans_display}</strong>
  </div>
</div>
"""

    body = f"""
<nav>
  <a href="{chapter_rel}/index.html">← {chapter}</a>
  <a href="index.html">↑ Cluster Overview</a>
  <a href="cluster_analysis.html">🔍 Analysis</a>
  <a href="answers.html">✅ Answers</a>
</nav>

<h1>📝 {name}</h1>
<p style="color:#555">{len(questions)} questions in this cluster</p>

{questions_html}

<div class="card" style="text-align:center;margin-top:24px">
  <a href="index.html" style="color:#1a237e;font-weight:600;margin-right:16px">↑ Cluster Overview</a>
  <a href="answers.html" style="color:#1b5e20;font-weight:600">✅ Quick Answer Key</a>
</div>
"""
    return html_shell(f"Questions — {name}", body)


def make_analysis_html(cluster: dict, questions: list, chapter_rel: str) -> str:
    cid = cluster["cluster_id"]
    name = cluster.get("cluster_name", cid)
    chapter = cluster.get("chapter", "")
    subject = cluster.get("subject", "")
    sim_level = cluster.get("similarity_level", 3)

    core_concept = infer_core_concept(cluster)
    approach = infer_approach(cluster)
    formulae = infer_formulae(cluster)
    traps = infer_common_traps(cluster)

    # Year-wise summary
    year_data = defaultdict(list)
    for q in questions:
        yr = str(q.get("year", ""))
        if yr:
            year_data[yr].append(q)

    year_rows = ""
    for yr in sorted(year_data.keys()):
        qs = year_data[yr]
        diffs = [q.get("difficulty", "") or "Unknown" for q in qs]
        year_rows += f"<tr><td><span class='year-badge'>{yr}</span></td><td>{len(qs)}</td><td>{', '.join(diffs)}</td></tr>"

    # Difficulty distribution
    diff_counts = defaultdict(int)
    for q in questions:
        d = q.get("difficulty", "") or "Unknown"
        diff_counts[d] += 1

    diff_bars = ""
    total = len(questions)
    for d, c in diff_counts.items():
        pct = int(c / total * 100)
        clr = {"Easy": "#4caf50", "Moderate": "#ff9800", "Difficult": "#f44336"}.get(d, "#90a4ae")
        diff_bars += f"""
<div style="margin:6px 0">
  <span style="display:inline-block;width:90px;font-weight:600">{d}</span>
  <span style="display:inline-block;width:{pct*4}px;min-width:4px;height:16px;background:{clr};border-radius:4px;vertical-align:middle"></span>
  <span style="margin-left:8px;color:#555">{c}/{total} ({pct}%)</span>
</div>"""

    # Formulae
    formulae_html = "".join(f"<li><code>{f}</code></li>" for f in formulae)
    traps_html = "".join(f"<li>{t}</li>" for t in traps)

    # Variations (inferred from sim level)
    variations = {
        1: "Questions are near-identical in structure — same formula with different numerical values. Expect the same calculation type every time.",
        2: "Same underlying concept but presented in different forms — e.g., different variables given, inverse calculation, or multi-step variant.",
        3: "Related questions testing the broader chapter theme. Each question may require a different sub-formula or approach from within the same topic.",
    }.get(sim_level, "Varied presentations of the same concept.")

    # Tips
    tips = []
    if subject == "Physics":
        tips = [
            "Always draw a diagram or free-body diagram before solving.",
            "Confirm units match across all quantities before substituting.",
            "For numerical answers, verify the order of magnitude is physically reasonable.",
        ]
    elif subject == "Chemistry":
        tips = [
            "Memorise key reaction mechanisms and name reactions for organic chapters.",
            "For numerical problems, track significant figures from the data.",
            "Build a formula card for this cluster — high repeat probability.",
        ]
    elif subject == "Mathematics":
        tips = [
            "Identify the technique from the given form of the problem first.",
            "Elimination can be faster than full solution on MCQs — check options.",
            "Practice boundary/edge cases (e.g., n=0, θ=90°) to avoid traps.",
        ]

    tips_html = "".join(f"<li>{t}</li>" for t in tips)

    body = f"""
<nav>
  <a href="{chapter_rel}/index.html">← {chapter}</a>
  <a href="index.html">↑ Cluster Overview</a>
  <a href="questions.html">📝 Questions</a>
  <a href="answers.html">✅ Answers</a>
</nav>

<h1>🔍 Cluster Analysis — {name}</h1>
<p style="color:#555"><code>{cid}</code> &nbsp;|&nbsp; Similarity Level: {similarity_badge(sim_level)}</p>

<div class="card">
  <h2>🧠 Core Concept Being Tested</h2>
  <p>{core_concept}</p>
</div>

<div class="card">
  <h2>📐 General Problem-Solving Approach</h2>
  <p>{approach}</p>
</div>

<div class="card">
  <h2>📋 Required Formulae</h2>
  <div class="formula-box">
    <ul style="margin:0;padding-left:20px">{formulae_html}</ul>
  </div>
</div>

<div class="card">
  <h2>🔄 Common Variations in This Cluster</h2>
  <p>{variations}</p>
</div>

<div class="card">
  <h2>📅 Year-wise Summary</h2>
  <table>
    <tr><th>Year</th><th>No. of Questions</th><th>Difficulty</th></tr>
    {year_rows}
  </table>
</div>

<div class="card">
  <h2>📊 Difficulty Distribution</h2>
  {diff_bars}
</div>

<div class="card">
  <h2>⚠️ Common Traps & Mistakes</h2>
  <div class="trap-box">
    <ul style="margin:0;padding-left:20px">{traps_html}</ul>
  </div>
</div>

<div class="card">
  <h2>💡 Study Tips</h2>
  <div class="tip-box">
    <ul style="margin:0;padding-left:20px">{tips_html}</ul>
  </div>
</div>

<div style="text-align:center;margin-top:24px">
  <a href="questions.html" style="display:inline-block;background:#1a237e;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600;margin-right:12px">
    📝 Practice Questions
  </a>
  <a href="answers.html" style="display:inline-block;background:#1b5e20;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600">
    ✅ Answer Key
  </a>
</div>
"""
    return html_shell(f"Analysis — {name}", body)


def make_answers_html(cluster: dict, questions: list, chapter_rel: str) -> str:
    cid = cluster["cluster_id"]
    name = cluster.get("cluster_name", cid)
    chapter = cluster.get("chapter", "")

    rows = ""
    for i, q in enumerate(questions, 1):
        qid = q.get("question_id", f"Q{i}")
        year = q.get("year", "")
        shift = q.get("shift", "")
        answer = q.get("correct_answer", "") or "<em style='color:#999'>Not recorded</em>"
        qtype = q.get("question_type", "MCQ")
        rows += f"""<tr>
  <td><code style="font-size:.8rem">{qid}</code></td>
  <td><span class="year-badge">{year}</span></td>
  <td>Shift {shift}</td>
  <td>{type_badge(qtype)}</td>
  <td><strong style="color:#1b5e20">{answer}</strong></td>
</tr>"""

    body = f"""
<nav>
  <a href="{chapter_rel}/index.html">← {chapter}</a>
  <a href="index.html">↑ Cluster Overview</a>
  <a href="questions.html">📝 Questions</a>
  <a href="cluster_analysis.html">🔍 Analysis</a>
</nav>

<h1>✅ Answer Key — {name}</h1>
<p style="color:#555"><code>{cid}</code> &nbsp;|&nbsp; {len(questions)} answers</p>

<div class="card">
  <table>
    <tr>
      <th>Question ID</th>
      <th>Year</th>
      <th>Shift</th>
      <th>Type</th>
      <th>Correct Answer</th>
    </tr>
    {rows}
  </table>
</div>

<div style="text-align:center;margin-top:16px">
  <a href="questions.html" style="display:inline-block;background:#1a237e;color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:600">
    📝 Back to Questions
  </a>
</div>
"""
    return html_shell(f"Answers — {name}", body)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("Loading database...")

    # Load questions
    questions_by_id = {}
    with open(DB / "questions.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
                questions_by_id[q["question_id"]] = q
            except Exception:
                pass
    print(f"  Loaded {len(questions_by_id)} questions")

    # Load clusters
    with open(DB / "clusters.json") as f:
        raw = json.load(f)
    clusters = raw["clusters"]
    print(f"  Loaded {len(clusters)} clusters")

    # Load priority metadata
    chapter_bucket = {}  # chapter -> bucket number
    chapter_branch = {}  # chapter -> branch (for chem)
    try:
        with open(DB / "priority_metadata.json") as f:
            pm = json.load(f)
        for entry in pm:
            ch = entry.get("chapter", "")
            chapter_bucket[ch] = entry.get("bucket", 3)
            if entry.get("chemistry_branch"):
                chapter_branch[ch] = entry["chemistry_branch"]
        print(f"  Loaded priority metadata for {len(chapter_bucket)} chapters")
    except Exception as e:
        print(f"  Warning: could not load priority_metadata.json: {e}")

    # Filter significant clusters
    sig_clusters = [c for c in clusters if len(c.get("question_ids", [])) >= 2]
    print(f"  Significant clusters (≥2 questions): {len(sig_clusters)}")

    folders_created = 0
    chapters_seen = set()

    for cluster in sig_clusters:
        cid = cluster["cluster_id"]
        subject = cluster.get("subject", "")
        chapter = cluster.get("chapter", "")

        if not subject or not chapter:
            print(f"  Skipping {cid}: missing subject/chapter")
            continue

        # Gather questions for this cluster
        q_ids = cluster.get("question_ids", [])
        q_list = [questions_by_id[qid] for qid in q_ids if qid in questions_by_id]

        if len(q_list) < 2:
            print(f"  Skipping {cid}: only {len(q_list)} questions found in DB")
            continue

        # Determine chapter folder path
        chap_folder = chapter_folder(subject, chapter)
        cluster_folder = chap_folder / "clusters" / cid
        cluster_folder.mkdir(parents=True, exist_ok=True)

        # Relative path back to chapter from cluster folder
        # cluster_folder = chap_folder/clusters/CID → ../../ = chap_folder
        chapter_rel = "../.."

        bucket = chapter_bucket.get(chapter, 3)
        chapters_seen.add(chapter)

        # Generate four files
        (cluster_folder / "index.html").write_text(
            make_index_html(cluster, q_list, bucket, chapter_rel), encoding="utf-8"
        )
        (cluster_folder / "questions.html").write_text(
            make_questions_html(cluster, q_list, chapter_rel), encoding="utf-8"
        )
        (cluster_folder / "cluster_analysis.html").write_text(
            make_analysis_html(cluster, q_list, chapter_rel), encoding="utf-8"
        )
        (cluster_folder / "answers.html").write_text(
            make_answers_html(cluster, q_list, chapter_rel), encoding="utf-8"
        )

        folders_created += 1
        print(f"  ✓ {cid} ({len(q_list)} Qs) → {cluster_folder.relative_to(ROOT)}")

    print(f"\nDone! Created {folders_created} cluster folders across {len(chapters_seen)} chapters.")
    print(f"Chapters: {sorted(chapters_seen)}")
    return folders_created, len(chapters_seen)


if __name__ == "__main__":
    fc, ch = main()
    print(f"\nSUMMARY: {fc} cluster folders | {ch} chapters")
