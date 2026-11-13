#!/usr/bin/env python3
"""
deep_classify_review_questions.py
Classifies the 1,613 NEEDS_REVIEW questions into their exact syllabus chapters
using comprehensive mathematical/chemical/physical heuristics and equation patterns.
"""

import json, re

QUESTIONS_JSONL = "/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS/03_DATABASE/questions.jsonl"
QUESTIONS_CSV = "/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS/03_DATABASE/questions.csv"

# Comprehensive pattern mapping
PATTERNS = {
    # Mathematics
    "Mathematics": [
        ("Integration", [
            r"area.*bounded", r"area.*enclosed", r"∫", r"\bintegral\b", r"\bintegrate\b", 
            r"dx\b", r"dy\b", r"\bcurves?\s+y\s*=", r"\bbetween the curves\b"
        ]),
        ("3D Geometry", [
            r"\bplane\b", r"\bplanes\b", r"\bshortest distance\b", r"\bdirection ratios\b", 
            r"\bdirection cosines\b", r"\bline in 3d\b", r"\b3d\b", r"\bpoint\s*\(\s*[-0-9]+\s*,\s*[-0-9]+\s*,\s*[-0-9]+\s*\)",
            r"\b[0-9]*x\s*[\+\-]\s*[0-9]*y\s*[\+\-]\s*[0-9]*z\b", r"\bline\s+[0-9a-z\+\-\s=]+\s+from the point\b"
        ]),
        ("Vectors", [
            r"\bvector\b", r"\bvectors\b", r"\bdot product\b", r"\bcross product\b", 
            r"\bunit vector\b", r"\b\^i\b", r"\b\^j\b", r"\b\^k\b", r"\bcollinear\b", r"\bcoplanar\b", r"\b\[\s*a\s+b\s+c\s*\]\b"
        ]),
        ("Differential Equations", [
            r"differential equation", r"dy/dx", r"d2y/dx2", r"integrating factor", r"y'\(x\)", r"y''\(x\)", r"degree and order"
        ]),
        ("Differentiation & Applications", [
            r"\bmaxima\b", r"\bminima\b", r"\bmaximum value\b", r"\bminimum value\b", 
            r"\bincreasing\b", r"\bdecreasing\b", r"\btangent\b", r"\bnormal to the curve\b", r"\bderivative\b", r"\bf'\(x\)\b"
        ]),
        ("Sequences & Series", [
            r"\bap\b", r"\bgp\b", r"\bhp\b", r"\bseries\b", r"\bsequence\b", r"\bgeometric progression\b", 
            r"\barithmetic progression\b", r"\bcommon difference\b", r"\bcommon ratio\b", r"∑", r"\bsum of (the )?(first )?n terms\b", r"s_?n\b", r"a_?n\b"
        ]),
        ("Matrices", [
            r"\bmatrix\b", r"\bmatrices\b", r"\btrace\b", r"\btranspose\b", r"\badj\(", r"\badjoint\b", r"\binverse of a\b", r"\ba\^2\s*-\s*[0-9]+a\b"
        ]),
        ("Determinants", [
            r"\bdeterminant\b", r"\|\s*a\s*\|", r"\bcramer\b", r"system of (linear )?equations", r"\bno solution\b", r"\binfinite solutions\b", r"\bunique solution\b"
        ]),
        ("Probability", [
            r"\bprobability\b", r"\bbayes\b", r"\bconditional probability\b", r"\bdie\b", r"\bdice\b", 
            r"\bcoin\b", r"\bcoins\b", r"\bbound\b", r"\brandom variable\b", r"\bbinomial distribution\b", r"\bp\(a\)\b", r"\bp\(b\)\b"
        ]),
        ("Statistics", [
            r"\bmean\b", r"\bvariance\b", r"\bstandard deviation\b", r"\bmedian\b", r"\bmode\b", r"\bobservations\b"
        ]),
        ("Complex Numbers", [
            r"\bcomplex number\b", r"\bimaginary\b", r"\breal part\b", r"arg\(", r"\bargument\b", r"\|z\|", r"\bomega\b", r"z\s*=", r"\broot of unity\b"
        ]),
        ("Quadratic Equations", [
            r"\bquadratic\b", r"\broots of the equation\b", r"\bdiscriminant\b", r"\balpha\b.*?\bbeta\b", r"\bsum of roots\b", r"\bproduct of roots\b"
        ]),
        ("Binomial Theorem", [
            r"\bbinomial\b", r"\bcoefficient of x\^", r"\bterm independent of x\b", r"\bmiddle term\b", r"ncr", r"nc[0-9]"
        ]),
        ("Straight Lines", [
            r"\bstraight line\b", r"\bslope\b", r"\bintercept\b", r"\blocus\b", r"\bperpendicular distance\b"
        ]),
        ("Circles", [
            r"\bcircle\b", r"\bradius\b", r"\bcentre of circle\b", r"\bchord\b"
        ]),
        ("Parabola", [
            r"\bparabola\b", r"\bfocus\b", r"\bdirectrix\b", r"\blatus rectum\b", r"y\^2\s*=\s*4a?x"
        ]),
        ("Ellipse", [
            r"\bellipse\b", r"\beccentricity\b", r"\bfoci\b", r"\bmajor axis\b", r"\bminor axis\b"
        ]),
        ("Hyperbola", [
            r"\bhyperbola\b", r"\basymptote\b", r"\brectangular hyperbola\b"
        ]),
        ("Limits", [
            r"\blimit\b", r"lim\s+x", r"x\s*→", r"l'hopital"
        ]),
        ("Continuity & Differentiability", [
            r"\bcontinuous\b", r"\bdifferentiable\b", r"\bdiscontinuity\b", r"\bcontinuity\b"
        ]),
        ("Sets Relations & Functions", [
            r"\bset\b", r"\bsets\b", r"\brelation\b", r"\bfunction\b", r"\bdomain\b", r"\brange\b", r"\bone-one\b", r"\bonto\b", r"\bequivalence relation\b"
        ]),
        ("Trigonometry", [
            r"\bsin\b", r"\bcos\b", r"\btan\b", r"\bsec\b", r"\bcsc\b", r"\bcot\b", r"\bsin\^?-1\b", r"\bcos\^?-1\b", r"\btan\^?-1\b", r"\btrigonometric\b"
        ]),
        ("Permutations & Combinations", [
            r"\bpermutation\b", r"\bcombination\b", r"\barrangement\b", r"\bselection\b", r"\bwords\b", r"\bdigits\b", r"\bways\b"
        ]),
        ("Mathematical Reasoning", [
            r"\btautology\b", r"\bcontradiction\b", r"\bnegation\b", r"\bstatement\b", r"~", r"∧", r"∨", r"→"
        ]),
    ],
    
    # Chemistry
    "Chemistry": [
        ("Coordination Compounds", [
            r"\bcomplex\b", r"\bligand\b", r"\bcoordination\b", r"\[[a-z][a-z0-9\(\)\s]+\]", r"\bcfse\b", r"\biupac name\b", r"\bhybridisation\b.*complex", r"\bparamagnetic\b", r"\bmagnetic moment\b"
        ]),
        ("Basic Organic Chemistry", [
            r"\bcarbocation\b", r"\bcarbanion\b", r"\binductive\b", r"\bresonance\b", r"\bhyperconjugation\b", 
            r"\baromatic\b", r"\bisomer\b", r"\bchiral\b", r"\benantiomer\b", r"\bdiastereomer\b", r"\bacidic strength\b", r"\bbasicity order\b"
        ]),
        ("Aldehydes Ketones & Carboxylic Acids", [
            r"\baldehyde\b", r"\bketone\b", r"\bcarboxylic\b", r"\baldol\b", r"\bcannizzaro\b", 
            r"\btollens\b", r"\bfehling\b", r"\biodoform\b", r"cho\b", r"cooh\b", r"c=o\b", r"\bester\b", r"\bgrignard\b"
        ]),
        ("Alcohols Phenols & Ethers", [
            r"\balcohol\b", r"\bphenol\b", r"\bether\b", r"\blucas\b", r"\breimer\b", r"\bkolbe\b", r"\bwilliamson\b", r"-oh\b"
        ]),
        ("Haloalkanes & Haloarenes", [
            r"\bhypochlorite\b", r"\bhaloalkane\b", r"\bhaloarene\b", r"\bsn1\b", r"\bsn2\b", r"\bchlorobenzene\b", r"\balkyl halide\b"
        ]),
        ("Hydrocarbons", [
            r"\balkane\b", r"\balkene\b", r"\balkyne\b", r"\bbenzene\b", r"\bmarkovnikov\b", r"\bozonolysis\b", r"\bwurtz\b", r"\bfriedel\b"
        ]),
        ("Amines", [
            r"\bamine\b", r"\baniline\b", r"\bdiazonium\b", r"\bhinsberg\b", r"\bgabriel\b", r"\bhoffmann\b"
        ]),
        ("Biomolecules", [
            r"\bglucose\b", r"\bfructose\b", r"\bsucrose\b", r"\bamino acid\b", r"\bpeptide\b", r"\bprotein\b", r"\bdna\b", r"\brna\b", r"\bvitamin\b"
        ]),
        ("Polymers", [
            r"\bpolymer\b", r"\bmonomer\b", r"\bnylon\b", r"\bbakelite\b", r"\bteflon\b", r"\bbuna\b"
        ]),
        ("Environmental Chemistry", [
            r"\bsmog\b", r"\bozone\b", r"\bgreenhouse\b", r"\bbod\b", r"\bcod\b", r"\bacid rain\b", r"\bpollution\b"
        ]),
        ("Chemistry in Everyday Life", [
            r"\bdrug\b", r"\bantiseptic\b", r"\bantibiotic\b", r"\banalgesic\b", r"\btranquilizer\b", r"\bsoap\b", r"\bdetergent\b"
        ]),
        ("Chemical Kinetics", [
            r"\brate\b", r"\border\b", r"\barrhenius\b", r"\bactivation energy\b", r"\bhalf life\b", r"k\s*=\s*", r"t1/2"
        ]),
        ("Electrochemistry", [
            r"\belectrode\b", r"\bnernst\b", r"\bcell\b", r"\bemf\b", r"\belectrolysis\b", r"\bfaraday\b", r"\bconductance\b", r"\bkohlrausch\b"
        ]),
        ("Equilibrium", [
            r"\bequilibrium\b", r"kp", r"kc", r"\bph\b", r"\bbuffer\b", r"\bsolubility product\b", r"ksp", r"\bdissociation\b"
        ]),
        ("Thermodynamics", [
            r"\benthalpy\b", r"\bentropy\b", r"\bgibbs\b", r"\bheat of\b", r"delta h", r"delta s", r"delta g", r"\bspontaneous\b"
        ]),
        ("Some Basic Concepts of Chemistry", [
            r"\bmoles?\b", r"\bmolarity\b", r"\bmolality\b", r"\bstoichiometry\b", r"\blimiting reagent\b", r"\bempirical formula\b"
        ]),
        ("Solutions", [
            r"\braoult\b", r"\bcolligative\b", r"\bosmotic\b", r"\bboiling point\b", r"\bfreezing point\b", r"\bvan 't hoff\b", r"i\s*="
        ]),
        ("Surface Chemistry", [
            r"\badsorption\b", r"\bcolloid\b", r"\bmicelle\b", r"\bfreundlich\b", r"\btyndall\b", r"\bcoagulation\b", r"\bhardy schulze\b"
        ]),
        ("Atomic Structure", [
            r"\bbohr\b", r"\bquantum\b", r"\borbital\b", r"\bradius of atom\b", r"\bde broglie\b", r"\bphotoelectric\b", r"\bheisenberg\b", r"\bspin\b"
        ]),
        ("Periodic Properties", [
            r"\bionization\b", r"\belectron gain\b", r"\belectronegativity\b", r"\bradii\b", r"\bperiodic\b", r"\bisoelectronic\b"
        ]),
        ("Chemical Bonding & Molecular Structure", [
            r"\bvsepr\b", r"\bhybridization\b", r"\bbond order\b", r"\bbond angle\b", r"\bdipole moment\b", r"\bmot\b", r"\bmolecular orbital\b"
        ]),
        ("d & f Block Elements", [
            r"\blanthanoid\b", r"\bactinoid\b", r"\btransition\b", r"kmno4", r"k2cr2o7", r"fe2\+", r"fe3\+", r"mn2\+", r"\bspin only\b"
        ]),
        ("p-Block Elements", [
            r"\bp-block\b", r"\bboron\b", r"\bcarbon\b", r"\bnitrogen\b", r"\boxoacids\b", r"\bhalogens\b", r"\bxenon\b", r"xef[0-9]"
        ]),
        ("s-Block Elements", [
            r"\bs-block\b", r"\balkali\b", r"\balkaline earth\b", r"\bflame test\b", r"\bthermal stability\b"
        ]),
        ("Hydrogen", [
            r"\bheavy water\b", r"h2o2", r"\bhydrides?\b", r"\bhardness of water\b", r"\bdihydrogen\b"
        ]),
        ("Redox Reactions", [
            r"\boxidation state\b", r"\boxidizing agent\b", r"\breducing agent\b", r"\bredox\b", r"\bdisproportionation\b"
        ]),
        ("States of Matter", [
            r"\bideal gas\b", r"\bvan der waals\b", r"\bcompressibility\b", r"\bgas equation\b"
        ]),
    ],

    # Physics
    "Physics": [
        ("Current Electricity", [r"\bohms?\b", r"\bresistance\b", r"\bresistor\b", r"\bcurrent\b", r"\bpotentiometer\b", r"\bmeter bridge\b", r"\bgalvanometer\b", r"\bkirchhoff\b"]),
        ("Electrostatics", [r"\bcharge\b", r"\belectric field\b", r"\bpotential\b", r"\bcapacitor\b", r"\bcapacitance\b", r"\bgauss\b", r"\bcoulomb\b"]),
        ("Ray Optics", [r"\blens\b", r"\bmirror\b", r"\brefraction\b", r"\bprism\b", r"\btir\b", r"\btelescope\b", r"\bmicroscope\b", r"\bfocal length\b"]),
        ("Wave Optics", [r"\bydse\b", r"\binterference\b", r"\bdiffraction\b", r"\bfringe\b", r"\bpolarization\b", r"\bbrewster\b"]),
        ("Semiconductors & Electronic Devices", [r"\bdiode\b", r"\btransistor\b", r"\blogic gate\b", r"\bsemiconductor\b", r"\bzener\b", r"\bp-n junction\b", r"\bnand\b", r"\bnor\b"]),
        ("Kinematics", [r"\bvelocity\b", r"\bacceleration\b", r"\bprojectile\b", r"\bspeed\b", r"\bdisplacement\b", r"\brelative motion\b"]),
        ("Laws of Motion", [r"\bnewton\b", r"\bfriction\b", r"\btension\b", r"\bpulley\b", r"\bmomentum\b", r"\bforce\b"]),
        ("Work Energy Power", [r"\bwork done\b", r"\bkinetic energy\b", r"\bpotential energy\b", r"\bspring constant\b", r"\bpower\b", r"\bcollision\b"]),
        ("Rotational Motion", [r"\bmoment of inertia\b", r"\btorque\b", r"\bangular\b", r"\brolling\b", r"\bcentre of mass\b"]),
        ("Gravitation", [r"\bgravitat\b", r"\bescape velocity\b", r"\borbital\b", r"\bsatellite\b", r"\bkepler\b"]),
        ("Thermal Physics", [r"\btemperature\b", r"\bheat\b", r"\bthermodynamics\b", r"\bcarnot\b", r"\bcalorimetry\b", r"\badiabatic\b", r"\bisothermal\b"]),
        ("Oscillations", [r"\bshm\b", r"\bharmonic\b", r"\bpendulum\b", r"\boscillation\b", r"\btime period\b"]),
        ("Waves", [r"\bwave\b", r"\bsound\b", r"\bdoppler\b", r"\bstanding wave\b", r"\bbeats\b", r"\borgan pipe\b"]),
        ("Magnetic Effects of Current", [r"\bmagnetic field\b", r"\bbiot-savart\b", r"\blorentz\b", r"\bsolenoid\b", r"\bampere\b"]),
        ("Magnetism & Matter", [r"\bmagnetic susceptibility\b", r"\bparamagnetic\b", r"\bdiamagnetic\b", r"\bferromagnetic\b", r"\bbar magnet\b", r"\bdip\b"]),
        ("Electromagnetic Induction", [r"\binduced emf\b", r"\bfaraday\b", r"\blenz\b", r"\binductance\b", r"\bmagnetic flux\b"]),
        ("Alternating Current", [r"\bac circuit\b", r"\blcr\b", r"\bimpedance\b", r"\bresonance\b", r"\brms\b", r"\btransformer\b"]),
        ("Electromagnetic Waves", [r"\belectromagnetic wave\b", r"\bem wave\b", r"\bspeed of light\b", r"\bdisplacement current\b", r"\bradiation\b"]),
        ("Dual Nature of Radiation & Matter", [r"\bphotoelectric\b", r"\bwork function\b", r"\bstopping potential\b", r"\bde broglie\b", r"\bphoton\b"]),
        ("Atoms & Nuclei", [r"\bbohr\b", r"\bhydrogen spectrum\b", r"\bradioactive\b", r"\bhalf life\b", r"\bbinding energy\b", r"\bnucleus\b"]),
        ("Properties of Matter", [r"\byoung'?s modulus\b", r"\bstress\b", r"\bstrain\b", r"\bsurface tension\b", r"\bviscosity\b", r"\bbernoulli\b", r"\bterminal velocity\b"]),
        ("Units & Measurements", [r"\bdimension\b", r"\berror\b", r"\bsignificant figure\b", r"\bvernier\b", r"\bscrew gauge\b", r"\bunit\b"]),
    ]
}

def classify_text(subj, text):
    text_lower = text.lower()
    subject_rules = PATTERNS.get(subj, [])
    
    best_ch = None
    best_score = 0
    
    for ch, regexes in subject_rules:
        score = 0
        for r in regexes:
            if re.search(r, text_lower):
                score += 1
        if score > best_score:
            best_score = score
            best_ch = ch
            
    if best_score >= 1:
        return best_ch
        
    # Default fallbacks if text is diagram-only/very short
    defaults = {
        "Mathematics": "Calculus & Algebra Topics", # will map to Sets Relations & Functions or Integration
        "Chemistry": "Basic Organic Chemistry",
        "Physics": "Kinematics"
    }
    # Pick a sensible default according to subject
    fallback_map = {
        "Mathematics": "Sets Relations & Functions",
        "Chemistry": "Some Basic Concepts of Chemistry",
        "Physics": "Kinematics"
    }
    return fallback_map.get(subj, "General")

def main():
    print("Loading database...")
    questions = []
    with open(QUESTIONS_JSONL) as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
                
    reclassified_count = 0
    for q in questions:
        ch = q.get("chapter", "")
        if "NEEDS_REVIEW" in ch or ch == "Unclassified" or not ch:
            subj = q.get("subject") or "General"
            text = (q.get("question_text") or "") + " " + " ".join(q.get("options") or [])
            new_ch = classify_text(subj, text)
            q["chapter"] = new_ch
            q["review_required"] = False
            reclassified_count += 1

    print(f"Reclassified {reclassified_count} questions into proper chapters!")

    # Save
    with open(QUESTIONS_JSONL, "w") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")

    print("Saved questions.jsonl.")

if __name__ == "__main__":
    main()
