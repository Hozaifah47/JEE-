#!/usr/bin/env python3
"""
reclassify_unclassified.py
Enhanced multi-pass keyword classification for unclassified JEE Main PYQ questions.
"""

import json
import re
import csv
import os
from collections import defaultdict

PROJECT_ROOT = "/home/hozaifah/HozzCode/JEE/JEE_MAIN_PYQ_ANALYSIS"
DB_PATH = os.path.join(PROJECT_ROOT, "03_DATABASE", "questions.jsonl")
CSV_PATH = os.path.join(PROJECT_ROOT, "03_DATABASE", "questions.csv")

# ─────────────────────────────────────────────────────────────
# CHAPTER TAXONOMY — chapter_name -> chapter_id, subject
# ─────────────────────────────────────────────────────────────
CHAPTER_IDS = {
    # Physics
    "Units & Measurements":                       ("PHY-01", "Physics"),
    "Kinematics":                                  ("PHY-02", "Physics"),
    "Laws of Motion":                              ("PHY-03", "Physics"),
    "Work Energy Power":                           ("PHY-04", "Physics"),
    "Rotational Motion":                           ("PHY-05", "Physics"),
    "Gravitation":                                 ("PHY-06", "Physics"),
    "Properties of Matter":                        ("PHY-07", "Physics"),
    "Thermal Physics":                             ("PHY-08", "Physics"),
    "Oscillations":                                ("PHY-09", "Physics"),
    "Waves":                                       ("PHY-10", "Physics"),
    "Electrostatics":                              ("PHY-11", "Physics"),
    "Current Electricity":                         ("PHY-12", "Physics"),
    "Magnetic Effects of Current":                 ("PHY-13", "Physics"),
    "Magnetism & Matter":                          ("PHY-14", "Physics"),
    "Electromagnetic Induction":                   ("PHY-15", "Physics"),
    "Alternating Current":                         ("PHY-16", "Physics"),
    "Electromagnetic Waves":                       ("PHY-17", "Physics"),
    "Ray Optics":                                  ("PHY-18", "Physics"),
    "Wave Optics":                                 ("PHY-19", "Physics"),
    "Dual Nature of Radiation & Matter":           ("PHY-20", "Physics"),
    "Atoms & Nuclei":                              ("PHY-21", "Physics"),
    "Semiconductors & Electronic Devices":         ("PHY-22", "Physics"),
    # Chemistry – Physical
    "Some Basic Concepts of Chemistry":            ("CHEM-P01", "Chemistry"),
    "Atomic Structure":                            ("CHEM-P02", "Chemistry"),
    "Chemical Bonding & Molecular Structure":      ("CHEM-P03", "Chemistry"),
    "States of Matter":                            ("CHEM-P04", "Chemistry"),
    "Thermodynamics":                              ("CHEM-P05", "Chemistry"),
    "Equilibrium":                                 ("CHEM-P06", "Chemistry"),
    "Redox Reactions":                             ("CHEM-P07", "Chemistry"),
    "Electrochemistry":                            ("CHEM-P08", "Chemistry"),
    "Chemical Kinetics":                           ("CHEM-P09", "Chemistry"),
    "Surface Chemistry":                           ("CHEM-P10", "Chemistry"),
    "Solutions":                                   ("CHEM-P11", "Chemistry"),
    # Chemistry – Organic
    "Basic Organic Chemistry":                     ("CHEM-O01", "Chemistry"),
    "Hydrocarbons":                                ("CHEM-O02", "Chemistry"),
    "Haloalkanes & Haloarenes":                    ("CHEM-O03", "Chemistry"),
    "Alcohols Phenols & Ethers":                   ("CHEM-O04", "Chemistry"),
    "Aldehydes Ketones & Carboxylic Acids":        ("CHEM-O05", "Chemistry"),
    "Amines":                                      ("CHEM-O06", "Chemistry"),
    "Biomolecules":                                ("CHEM-O07", "Chemistry"),
    "Polymers":                                    ("CHEM-O08", "Chemistry"),
    "Chemistry in Everyday Life":                  ("CHEM-O09", "Chemistry"),
    # Chemistry – Inorganic
    "Periodic Properties":                         ("CHEM-I01", "Chemistry"),
    "Hydrogen":                                    ("CHEM-I02", "Chemistry"),
    "s-Block Elements":                            ("CHEM-I03", "Chemistry"),
    "p-Block Elements":                            ("CHEM-I04", "Chemistry"),
    "d & f Block Elements":                        ("CHEM-I05", "Chemistry"),
    "Coordination Compounds":                      ("CHEM-I06", "Chemistry"),
    "Environmental Chemistry":                     ("CHEM-I07", "Chemistry"),
    # Mathematics
    "Sets Relations & Functions":                  ("MATH-01", "Mathematics"),
    "Complex Numbers":                             ("MATH-02", "Mathematics"),
    "Sequences & Series":                          ("MATH-03", "Mathematics"),
    "Quadratic Equations":                         ("MATH-04", "Mathematics"),
    "Permutations & Combinations":                 ("MATH-05", "Mathematics"),
    "Binomial Theorem":                            ("MATH-06", "Mathematics"),
    "Straight Lines":                              ("MATH-07", "Mathematics"),
    "Circles":                                     ("MATH-08", "Mathematics"),
    "Parabola":                                    ("MATH-09", "Mathematics"),
    "Ellipse":                                     ("MATH-10", "Mathematics"),
    "Hyperbola":                                   ("MATH-11", "Mathematics"),
    "Limits":                                      ("MATH-12", "Mathematics"),
    "Continuity & Differentiability":              ("MATH-13", "Mathematics"),
    "Differentiation & Applications":             ("MATH-14", "Mathematics"),
    "Integration":                                 ("MATH-15", "Mathematics"),
    "Differential Equations":                      ("MATH-16", "Mathematics"),
    "Vectors":                                     ("MATH-17", "Mathematics"),
    "3D Geometry":                                 ("MATH-18", "Mathematics"),
    "Matrices":                                    ("MATH-19", "Mathematics"),
    "Determinants":                                ("MATH-20", "Mathematics"),
    "Probability":                                 ("MATH-21", "Mathematics"),
    "Statistics":                                  ("MATH-22", "Mathematics"),
    "Trigonometry":                                ("MATH-23", "Mathematics"),
    "Mathematical Reasoning":                      ("MATH-24", "Mathematics"),
}

# ─────────────────────────────────────────────────────────────
# KEYWORD PATTERNS  (chapter -> list of regex patterns)
# ─────────────────────────────────────────────────────────────
PATTERNS = {

    # ===== PHYSICS =====
    "Units & Measurements": [
        r"dimension", r"significant\s*fig", r"significant\s*figure",
        r"error\s+in", r"percentage\s+error", r"least\s+count",
        r"measurement", r"SI\s+unit", r"\[LMT\]", r"\bLMT\b",
        r"accuracy", r"precision", r"vernier", r"screw\s+gauge",
        r"physical\s+quantity", r"derived\s+unit", r"fundamental\s+unit",
        r"order\s+of\s+magnitude",
    ],
    "Kinematics": [
        r"velocity", r"acceleration", r"projectile", r"relative\s+motion",
        r"v\s*=\s*u\s*\+\s*at", r"s\s*=\s*ut", r"displacement",
        r"uniform\s+motion", r"non.uniform\s+motion", r"speed",
        r"trajectory", r"range\s+of\s+projectile", r"time\s+of\s+flight",
        r"maximum\s+height", r"retardation",
    ],
    "Laws of Motion": [
        r"friction", r"tension", r"newton.s\s+law", r"newton\s+law",
        r"pseudo\s+force", r"inertia", r"impulse", r"force\s+on",
        r"f\s*=\s*ma", r"free\s+body\s+diagram", r"normal\s+force",
        r"coefficient\s+of\s+friction", r"static\s+friction",
        r"kinetic\s+friction", r"inclined\s+plane", r"atwood",
    ],
    "Work Energy Power": [
        r"work\s+done", r"kinetic\s+energy", r"potential\s+energy",
        r"power", r"spring\s+constant", r"elastic\s+collision",
        r"inelastic\s+collision", r"momentum", r"joule",
        r"conservation\s+of\s+energy", r"energy\s+stored\s+in\s+spring",
        r"work.energy\s+theorem",
    ],
    "Rotational Motion": [
        r"torque", r"moment\s+of\s+inertia", r"angular\s+velocity",
        r"angular\s+acceleration", r"rolling", r"rotation",
        r"radius\s+of\s+gyration", r"rigid\s+body", r"angular\s+momentum",
        r"rotational\s+kinetic\s+energy", r"parallel\s+axis",
        r"perpendicular\s+axis", r"spinning", r"gyroscope",
    ],
    "Gravitation": [
        r"satellite", r"orbital\s+velocity", r"escape\s+velocity",
        r"kepler", r"gravitational\s+field", r"planet",
        r"gravitational\s+potential", r"universal\s+gravitation",
        r"geostationary", r"orbit", r"gravitational\s+constant\s+G",
        r"variation\s+of\s+g",
    ],
    "Properties of Matter": [
        r"elastic", r"stress", r"strain", r"young.s\s+modulus",
        r"young\s+modulus", r"viscosity", r"surface\s+tension",
        r"capillary", r"bernoulli", r"fluid", r"bulk\s+modulus",
        r"rigidity\s+modulus", r"poisson.s\s+ratio", r"stokes",
        r"terminal\s+velocity", r"streamline", r"turbulent",
        r"plasticity", r"depression", r"cantilever",
    ],
    "Thermal Physics": [
        r"temperature", r"heat\s+capacity", r"specific\s+heat",
        r"calorimetry", r"carnot\s+engine", r"entropy",
        r"gas\s+constant", r"isothermal", r"adiabatic",
        r"internal\s+energy", r"calorie", r"kelvin", r"celsius",
        r"conduction", r"convection", r"radiation\s+of\s+heat",
        r"stefan.s\s+law", r"stefan.boltzmann", r"wien.s\s+law",
        r"thermodynamics", r"first\s+law\s+of\s+thermo",
        r"second\s+law\s+of\s+thermo", r"zeroth\s+law",
        r"thermal\s+expansion", r"heat\s+engine", r"refrigerator",
        r"kinetic\s+theory", r"degrees\s+of\s+freedom",
        r"rms\s+speed", r"mean\s+free\s+path", r"boyle.s\s+law",
        r"charles\s+law", r"ideal\s+gas",
    ],
    "Oscillations": [
        r"simple\s+harmonic", r"\bSHM\b", r"pendulum",
        r"oscillation", r"amplitude", r"time\s+period",
        r"restoring\s+force", r"angular\s+frequency",
        r"spring.mass\s+system", r"damped", r"forced\s+oscillation",
        r"resonance\s+in\s+oscillation",
    ],
    "Waves": [
        r"wave\s+equation", r"sound\s+wave", r"speed\s+of\s+sound",
        r"doppler", r"standing\s+wave", r"stationary\s+wave",
        r"beats", r"superposition\s+of\s+wave", r"wavelength",
        r"\bnode\b", r"antinode", r"decibel", r"echo",
        r"resonance\s+column", r"fundamental\s+frequency",
        r"harmonics", r"string\s+vibration",
    ],
    "Electrostatics": [
        r"coulomb.s\s+law", r"electric\s+field", r"electric\s+potential",
        r"capacitor", r"gauss.s\s+law", r"gauss\s+law",
        r"electric\s+charge", r"dipole", r"conductor\s+in\s+field",
        r"dielectric", r"permittivity", r"epsilon_0", r"ε_?0",
        r"electric\s+flux", r"potential\s+energy\s+of\s+charge",
        r"electrostatic", r"charge\s+distribution",
        r"capacitance", r"parallel\s+plate\s+capacitor",
        r"energy\s+stored\s+in\s+capacitor",
    ],
    "Current Electricity": [
        r"resistor", r"ohm.s\s+law", r"kirchhoff", r"resistance",
        r"electric\s+circuit", r"battery", r"\bemf\b", r"wheatstone",
        r"potentiometer", r"voltmeter", r"ammeter", r"galvanometer",
        r"resistivity", r"conductance", r"drift\s+velocity",
        r"current\s+density", r"metre\s+bridge", r"meter\s+bridge",
        r"series\s+and\s+parallel", r"internal\s+resistance",
    ],
    "Magnetic Effects of Current": [
        r"biot.savart", r"ampere.s\s+law", r"lorentz\s+force",
        r"solenoid", r"toroid", r"cyclotron", r"magnetic\s+field",
        r"moving\s+charge\s+in\s+field", r"force\s+on\s+conductor",
        r"force\s+between\s+parallel\s+wires",
    ],
    "Magnetism & Matter": [
        r"ferromagnetic", r"paramagnetic", r"diamagnetic",
        r"hysteresis", r"bar\s+magnet", r"magnetic\s+moment",
        r"permeability", r"magnetic\s+susceptibility",
        r"curie\s+law", r"magnetic\s+dipole", r"earth.s\s+magnetic\s+field",
        r"magnetization",
    ],
    "Electromagnetic Induction": [
        r"faraday.s\s+law", r"lenz.s\s+law", r"induced\s+emf",
        r"mutual\s+inductance", r"self\s+inductance",
        r"eddy\s+current", r"magnetic\s+flux\s+change",
        r"electromagnetic\s+induction", r"motional\s+emf",
    ],
    "Alternating Current": [
        r"\bAC\s+circuit\b", r"\bRLC\b", r"impedance",
        r"resonance\s+in\s+circuit", r"transformer",
        r"power\s+factor", r"\brms\b", r"reactance",
        r"inductive\s+reactance", r"capacitive\s+reactance",
        r"alternating\s+current", r"wattless\s+current",
    ],
    "Electromagnetic Waves": [
        r"electromagnetic\s+wave", r"speed\s+of\s+light",
        r"infrared", r"ultraviolet", r"X.ray", r"microwave",
        r"radio\s+wave", r"displacement\s+current", r"gamma\s+ray",
        r"electromagnetic\s+spectrum", r"visible\s+light",
    ],
    "Ray Optics": [
        r"\blens\b", r"\bmirror\b", r"refraction", r"reflection",
        r"snell.s\s+law", r"total\s+internal\s+reflection",
        r"\bTIR\b", r"prism", r"magnification",
        r"telescope", r"microscope", r"focal\s+length",
        r"refractive\s+index", r"optical\s+fiber",
        r"lens\s+formula", r"mirror\s+formula", r"power\s+of\s+lens",
    ],
    "Wave Optics": [
        r"interference", r"diffraction", r"polarization",
        r"young.s\s+double\s+slit", r"YDSE", r"fringe\s+width",
        r"coherent\s+source", r"huygens", r"malus\s+law",
        r"single\s+slit", r"double\s+slit", r"resolving\s+power",
    ],
    "Dual Nature of Radiation & Matter": [
        r"photoelectric\s+effect", r"photon", r"de\s+broglie",
        r"work\s+function", r"threshold\s+frequency",
        r"matter\s+wave", r"stopping\s+potential",
        r"wave.particle\s+duality", r"compton",
    ],
    "Atoms & Nuclei": [
        r"bohr.s\s+model", r"bohr\s+model", r"hydrogen\s+spectrum",
        r"nucleus", r"radioactive", r"half\s+life",
        r"nuclear\s+fission", r"nuclear\s+fusion", r"binding\s+energy",
        r"alpha\s+decay", r"beta\s+decay", r"mass\s+defect",
        r"radioactivity", r"nuclear\s+reaction", r"neutron",
        r"proton", r"energy\s+level", r"emission\s+spectrum",
    ],
    "Semiconductors & Electronic Devices": [
        r"semiconductor", r"p.n\s+junction", r"\bdiode\b",
        r"transistor", r"logic\s+gate", r"rectifier",
        r"amplifier", r"\bNAND\b", r"\bNOR\b", r"\bXOR\b",
        r"zener\s+diode", r"\bLED\b", r"photodiode",
        r"forward\s+bias", r"reverse\s+bias",
        r"boolean\s+expression", r"truth\s+table", r"AND\s+gate",
        r"OR\s+gate", r"NOT\s+gate", r"intrinsic", r"extrinsic",
        r"n.type", r"p.type", r"depletion\s+region",
    ],

    # ===== CHEMISTRY – PHYSICAL =====
    "Some Basic Concepts of Chemistry": [
        r"\bmole\b", r"molarity", r"molality", r"normality",
        r"stoichiometry", r"empirical\s+formula", r"molecular\s+formula",
        r"equivalent\s+weight", r"volume\s+strength",
        r"\bppm\b", r"mole\s+fraction", r"limiting\s+reagent",
        r"percent\s+composition", r"atomic\s+mass",
        r"molar\s+mass", r"avogadro",
    ],
    "Atomic Structure": [
        r"quantum\s+number", r"\borbital\b", r"electron\s+configuration",
        r"schrodinger", r"heisenberg", r"de\s+broglie\s+wavelength",
        r"bohr.s\s+radius", r"pauli\s+exclusion", r"hund.s\s+rule",
        r"aufbau", r"radial\s+node", r"angular\s+node",
        r"electronic\s+configuration", r"atomic\s+orbital",
        r"principal\s+quantum", r"azimuthal\s+quantum",
        r"magnetic\s+quantum", r"spin\s+quantum",
        r"photoelectric", r"emission\s+spectrum\s+of\s+hydrogen",
        r"ionization\s+energy\s+of\s+H",
    ],
    "Chemical Bonding & Molecular Structure": [
        r"hybridization", r"\bVSEPR\b", r"bond\s+order",
        r"ionic\s+bond", r"covalent\s+bond", r"molecular\s+orbital",
        r"hydrogen\s+bond", r"van\s+der\s+waals", r"dipole\s+moment",
        r"resonance\s+structure", r"sigma\s+bond", r"pi\s+bond",
        r"bond\s+angle", r"bond\s+length", r"formal\s+charge",
        r"Lewis\s+structure", r"electron\s+pair", r"lone\s+pair",
        r"polarity", r"electronegativity\s+difference",
        r"crystal\s+structure", r"metallic\s+bond",
    ],
    "States of Matter": [
        r"van\s+der\s+waals\s+equation", r"ideal\s+gas\s+law",
        r"critical\s+temperature", r"compressibility\s+factor",
        r"graham.s\s+law", r"dalton.s\s+law",
        r"partial\s+pressure", r"real\s+gas",
        r"gas\s+laws", r"boyle.s", r"charles",
        r"avogadro.s\s+law",
    ],
    "Thermodynamics": [
        r"enthalpy", r"entropy\s+change", r"gibbs\s+energy",
        r"gibbs\s+free\s+energy", r"hess.s\s+law",
        r"bond\s+enthalpy", r"heat\s+of\s+formation",
        r"heat\s+of\s+combustion", r"spontaneous",
        r"standard\s+enthalpy", r"ΔH", r"ΔG", r"ΔS",
        r"exothermic", r"endothermic",
    ],
    "Equilibrium": [
        r"\bKp\b", r"\bKc\b", r"Le\s+Chatelier", r"degree\s+of\s+dissociation",
        r"\bpH\b", r"buffer\s+solution", r"henderson.hasselbalch",
        r"solubility\s+product", r"\bKsp\b", r"common\s+ion\s+effect",
        r"amphiprotic", r"acid.base\s+equilibrium",
        r"ionic\s+equilibrium", r"degree\s+of\s+ionization",
        r"Ka\b", r"\bKb\b", r"weak\s+acid", r"weak\s+base",
        r"hydrolysis\s+of\s+salt", r"indicator",
    ],
    "Redox Reactions": [
        r"oxidation\s+state", r"oxidizing\s+agent", r"reducing\s+agent",
        r"disproportionation", r"n.factor", r"redox\s+reaction",
        r"balancing\s+redox", r"ion.electron\s+method",
        r"oxidation\s+number",
    ],
    "Electrochemistry": [
        r"electrode\s+potential", r"nernst\s+equation",
        r"electrolysis", r"faraday.s\s+law", r"conductance",
        r"cell\s+emf", r"galvanic\s+cell", r"kohlrausch",
        r"standard\s+cell", r"molar\s+conductance",
        r"electrolytic\s+cell", r"electrochemical\s+series",
        r"standard\s+hydrogen\s+electrode",
    ],
    "Chemical Kinetics": [
        r"rate\s+of\s+reaction", r"rate\s+constant",
        r"order\s+of\s+reaction", r"arrhenius", r"activation\s+energy",
        r"half\s+life\s+of\s+reaction", r"pseudo\s+first\s+order",
        r"rate\s+law", r"integrated\s+rate",
        r"first\s+order\s+reaction", r"second\s+order\s+reaction",
        r"zero\s+order", r"rate\s+determining\s+step",
    ],
    "Surface Chemistry": [
        r"adsorption", r"catalysis", r"colloid", r"emulsion",
        r"micelle", r"tyndall\s+effect", r"coagulation",
        r"\bsol\b", r"\bgel\b", r"langmuir", r"freundlich",
        r"chemisorption", r"physisorption", r"catalyst",
        r"enzyme\s+catalysis", r"zeolite",
    ],
    "Solutions": [
        r"raoult.s\s+law", r"colligative\s+propert",
        r"osmotic\s+pressure", r"vapour\s+pressure\s+lower",
        r"elevation\s+in\s+boiling\s+point", r"depression\s+in\s+freezing",
        r"van.t\s+hoff", r"abnormal\s+molar\s+mass",
        r"henry.s\s+law", r"ideal\s+solution",
        r"non.ideal\s+solution", r"mole\s+fraction",
        r"boiling\s+point\s+elevation", r"freezing\s+point\s+depression",
    ],

    # ===== CHEMISTRY – ORGANIC =====
    "Basic Organic Chemistry": [
        r"inductive\s+effect", r"resonance\s+effect",
        r"hyperconjugation", r"carbocation", r"carbanion",
        r"electrophilic", r"nucleophilic",
        r"\bSN1\b", r"\bSN2\b", r"\bE1\b", r"\bE2\b",
        r"markovnikov", r"zaitsev", r"stability\s+order",
        r"optical\s+isomer", r"geometrical\s+isomer",
        r"\bchiral\b", r"enantiomer", r"diastereomer",
        r"isomerism", r"tautomerism", r"aromatic\s+character",
        r"free\s+radical", r"\bIUPAC\b",
    ],
    "Hydrocarbons": [
        r"\balkane\b", r"\balkene\b", r"\balkyne\b",
        r"\bbenzene\b", r"aromatic\s+hydrocarbon",
        r"birch\s+reduction", r"friedel.crafts",
        r"ozonolysis", r"hydrogenation", r"wurtz\s+reaction",
        r"baeyer.s\s+test", r"cycloalkane", r"\bparaffin\b",
        r"\bolefin\b", r"acetylene", r"ethylene",
    ],
    "Haloalkanes & Haloarenes": [
        r"\bhalide\b", r"alkyl\s+halide", r"aryl\s+halide",
        r"grignard", r"finkelstein", r"chloroform",
        r"dehydrohalogenation", r"halogenation",
        r"chlorobenzene", r"nucleophilic\s+substitution",
        r"elimination\s+reaction",
    ],
    "Alcohols Phenols & Ethers": [
        r"\balcohol\b", r"\bphenol\b", r"\bether\b",
        r"dehydration\s+of\s+alcohol", r"esterification",
        r"lucas\s+test", r"reimer.tiemann", r"kolbe.s",
        r"iodoform\s+test", r"\bethanol\b", r"\bmethanol\b",
        r"williamson\s+synthesis", r"glycol",
    ],
    "Aldehydes Ketones & Carboxylic Acids": [
        r"\baldehyde\b", r"\bketone\b", r"cannizzaro",
        r"aldol\s+condensation", r"wittig\s+reaction",
        r"tollens", r"fehling", r"benedict",
        r"nucleophilic\s+addition", r"carbonyl\s+compound",
        r"oximation", r"NaBH4\s+reduction",
        r"carboxylic\s+acid", r"\bformic\b", r"\bacetic\b",
        r"\boxalic\b", r"decarboxylation", r"hell.volhard",
        r"ester\s+hydrolysis",
    ],
    "Amines": [
        r"\bamine\b", r"\baniline\b", r"diazonium",
        r"coupling\s+reaction", r"hoffmann\s+bromamide",
        r"hinsberg\s+test", r"diazotization",
        r"N.alkylation", r"acylation\s+of\s+amine",
        r"primary\s+amine", r"secondary\s+amine", r"tertiary\s+amine",
    ],
    "Biomolecules": [
        r"\bglucose\b", r"\bfructose\b", r"\bsucrose\b",
        r"\bDNA\b", r"\bRNA\b", r"amino\s+acid",
        r"\bpeptide\b", r"\bprotein\b", r"\benzyme\b",
        r"\bvitamin\b", r"glycoside\s+bond",
        r"\bpurine\b", r"\bpyrimidine\b",
        r"carbohydrate", r"nucleotide", r"reducing\s+sugar",
        r"anomers", r"mutarotation",
    ],
    "Polymers": [
        r"\bpolymer\b", r"\bmonomer\b", r"condensation\s+polymer",
        r"addition\s+polymer", r"\bnylon\b", r"bakelite",
        r"\brubber\b", r"copolymer",
        r"degree\s+of\s+polymerization", r"polymerization",
        r"thermoplastic", r"thermosetting",
    ],
    "Chemistry in Everyday Life": [
        r"\bdrug\b", r"antibiotic", r"analgesic",
        r"preservative", r"\bdye\b", r"detergent",
        r"\bsoap\b", r"food\s+additive", r"antiseptic",
        r"antacid", r"tranquilizer", r"narcotic",
    ],

    # ===== CHEMISTRY – INORGANIC =====
    "Periodic Properties": [
        r"ionization\s+energy", r"electron\s+affinity",
        r"electronegativity", r"atomic\s+radius",
        r"ionic\s+radius", r"periodic\s+trend",
        r"effective\s+nuclear\s+charge",
        r"periodicity", r"group\s+\d+", r"period\s+\d+",
    ],
    "Hydrogen": [
        r"hydrogen\s+bond", r"\bhydride\b", r"heavy\s+water",
        r"hydrogen\s+peroxide", r"water\s+structure",
        r"dihydrogen", r"ortho\s+hydrogen", r"para\s+hydrogen",
    ],
    "s-Block Elements": [
        r"alkali\s+metal", r"alkaline\s+earth",
        r"\bsodium\b", r"\bpotassium\b", r"\bcalcium\b",
        r"\bmagnesium\b", r"marsh\s+test", r"flame\s+test",
        r"\bLi\b", r"\bNa\b", r"\bK\b", r"\bRb\b", r"\bCs\b",
        r"\bBe\b", r"\bMg\b", r"\bCa\b", r"\bSr\b", r"\bBa\b",
        r"lithium", r"caesium", r"strontium",
        r"group\s+1\s+element", r"group\s+2\s+element",
        r"calcium\s+carbide", r"slaked\s+lime",
    ],
    "p-Block Elements": [
        r"\bp.block\b", r"group\s+1[3-8]",
        r"\bboron\b", r"\bcarbon\b", r"\bnitrogen\b",
        r"\boxygen\b", r"\bfluorine\b", r"\bchlorine\b",
        r"noble\s+gas", r"allotrope",
        r"nitric\s+acid", r"sulphuric\s+acid", r"sulfuric\s+acid",
        r"\bphosphorus\b", r"\bsulphur\b", r"\bsulfur\b",
        r"\bXeF\b", r"interhalogen", r"oxoacid",
        r"\bsilicon\b", r"\bgermanium\b", r"\barsenic\b",
        r"\bbismuth\b", r"\bandimony\b",
        r"white\s+phosphorus", r"red\s+phosphorus",
        r"ozone", r"bleaching\s+powder",
        r"number\s+of\s+(paramagnetic|diamagnetic|lone\s+pair)",
    ],
    "d & f Block Elements": [
        r"transition\s+metal", r"inner\s+transition",
        r"\blanthanide\b", r"\bactinide\b",
        r"\b3d\b", r"\b4d\b", r"\bf.block\b",
        r"variable\s+oxidation\s+state", r"catalytic\s+property",
        r"interstitial\s+compound",
        r"paramagnetism\s+of\s+d.block",
        r"d.block\s+element", r"f.block\s+element",
        r"color\s+of\s+d.block", r"colour\s+of\s+transition",
    ],
    "Coordination Compounds": [
        r"coordination\s+compound", r"\bligand\b", r"chelate",
        r"\bEDTA\b", r"spectrochemical\s+series",
        r"crystal\s+field", r"valence\s+bond\s+theory",
        r"coordination\s+number", r"denticity",
        r"ambidentate", r"isomerism\s+of\s+coordination",
        r"complex\s+(ion|compound|salt)", r"Werner",
        r"ionization\s+isomer", r"geometrical\s+isomer\s+of\s+complex",
        r"magnetic\s+moment\s+of\s+complex",
        r"spin\s+state", r"high\s+spin", r"low\s+spin",
    ],
    "Environmental Chemistry": [
        r"air\s+pollution", r"water\s+pollution",
        r"\bsmog\b", r"ozone\s+depletion",
        r"greenhouse", r"\bBOD\b", r"\bCOD\b",
        r"acid\s+rain", r"eutrophication",
        r"pollutant", r"global\s+warming",
        r"photochemical\s+smog",
    ],

    # ===== MATHEMATICS =====
    "Sets Relations & Functions": [
        r"\bset\b", r"\brelation\b", r"\bfunction\b",
        r"\bdomain\b", r"\brange\b", r"bijective",
        r"surjective", r"injective", r"\bmapping\b",
        r"venn\s+diagram", r"inverse\s+function",
        r"composite\s+function", r"one.to.one",
        r"onto\s+function", r"equivalence\s+relation",
        r"reflexive", r"symmetric", r"transitive",
    ],
    "Complex Numbers": [
        r"complex\s+number", r"argand\s+plane",
        r"real\s+part", r"imaginary\s+part",
        r"\|z\|", r"argument\s+of\s+z", r"polar\s+form",
        r"de\s+moivre", r"roots\s+of\s+unity",
        r"locus\s+in\s+complex", r"modulus\s+of\s+complex",
        r"conjugate\s+of\s+complex",
    ],
    "Sequences & Series": [
        r"arithmetic\s+progression", r"geometric\s+progression",
        r"harmonic\s+progression",
        r"\bAP\b", r"\bGP\b", r"\bHP\b",
        r"nth\s+term", r"sum\s+to\s+n\s+terms",
        r"AGM\s+inequality", r"sum\s+of\s+n\s+terms",
        r"arithmetic\s+mean", r"geometric\s+mean",
        r"sum\s+of\s+an\s+infinite\s+GP", r"telescoping\s+series",
        r"∑\s*S_n", r"series\s+sum",
    ],
    "Quadratic Equations": [
        r"quadratic\s+equation", r"\broots\b",
        r"discriminant", r"sum\s+of\s+roots", r"product\s+of\s+roots",
        r"nature\s+of\s+roots", r"vieta.s", r"alpha.*beta",
        r"β.*α", r"cubic\s+equation",
    ],
    "Permutations & Combinations": [
        r"permutation", r"combination",
        r"\bnCr\b", r"\bnPr\b", r"factorial",
        r"arrangement", r"selection",
        r"counting\s+principle", r"inclusion.exclusion",
        r"circular\s+permutation", r"distributing\s+objects",
    ],
    "Binomial Theorem": [
        r"binomial\s+theorem", r"binomial\s+expansion",
        r"coefficient\s+of\s+x", r"general\s+term",
        r"middle\s+term", r"nCr\s+term", r"pascal\s+triangle",
        r"binomial\s+coefficient", r"greatest\s+term",
    ],
    "Straight Lines": [
        r"slope\s+of\s+line", r"y.intercept", r"x.intercept",
        r"distance\s+from\s+point\s+to\s+line",
        r"angle\s+between\s+two\s+lines",
        r"concurrent\s+lines", r"collinear\s+points",
        r"equation\s+of\s+line", r"point\s+of\s+intersection",
        r"family\s+of\s+lines", r"pair\s+of\s+straight\s+lines",
        r"angle\s+bisector\s+of\s+lines",
    ],
    "Circles": [
        r"equation\s+of\s+circle", r"centre\s+of\s+circle",
        r"radius\s+of\s+circle", r"\bchord\b",
        r"tangent\s+to\s+circle", r"normal\s+to\s+circle",
        r"power\s+of\s+a\s+point", r"radical\s+axis",
        r"coaxial\s+circles", r"circle\s+passing\s+through",
        r"length\s+of\s+tangent",
    ],
    "Parabola": [
        r"\bparabola\b", r"focus\s+of\s+parabola",
        r"directrix", r"latus\s+rectum",
        r"tangent\s+to\s+parabola", r"normal\s+to\s+parabola",
        r"chord\s+of\s+contact",
    ],
    "Ellipse": [
        r"\bellipse\b", r"major\s+axis", r"minor\s+axis",
        r"eccentricity\s+of\s+ellipse", r"foci\s+of\s+ellipse",
        r"tangent\s+to\s+ellipse", r"normal\s+to\s+ellipse",
    ],
    "Hyperbola": [
        r"\bhyperbola\b", r"asymptote",
        r"rectangular\s+hyperbola", r"transverse\s+axis",
        r"conjugate\s+axis", r"eccentricity\s+of\s+hyperbola",
    ],
    "Limits": [
        r"\blimit\b", r"l.hopital", r"indeterminate\s+form",
        r"epsilon.delta", r"lim\s+x\s*→",
        r"right\s+hand\s+limit", r"left\s+hand\s+limit",
        r"limit\s+as\s+x\s+approaches",
        r"standard\s+limit",
    ],
    "Continuity & Differentiability": [
        r"continuous\s+function", r"differentiable",
        r"left\s+hand\s+derivative", r"right\s+hand\s+derivative",
        r"rolle.s\s+theorem", r"lagrange\s+MVT",
        r"mean\s+value\s+theorem", r"continuity\s+at",
        r"not\s+differentiable",
    ],
    "Differentiation & Applications": [
        r"\bderivative\b", r"dy/dx", r"d/dx",
        r"chain\s+rule", r"implicit\s+differentiation",
        r"maxima\b", r"minima\b",
        r"increasing\s+function", r"decreasing\s+function",
        r"tangent\s+and\s+normal\s+to\s+curve",
        r"rate\s+of\s+change",
        r"second\s+derivative", r"inflection\s+point",
        r"monotonically",
    ],
    "Integration": [
        r"\bintegrat", r"\bintegral\b", r"∫",
        r"substitution\s+method", r"integration\s+by\s+parts",
        r"partial\s+fractions", r"definite\s+integral",
        r"area\s+under\s+curve", r"area\s+bounded\s+by",
        r"area\s+between\s+curves", r"improper\s+integral",
        r"beta\s+function", r"gamma\s+function",
    ],
    "Differential Equations": [
        r"differential\s+equation",
        r"variable\s+separable", r"homogeneous\s+DE",
        r"linear\s+DE", r"integrating\s+factor",
        r"order\s+and\s+degree\s+of\s+DE",
        r"general\s+solution", r"particular\s+solution",
    ],
    "Vectors": [
        r"\bvector\b", r"dot\s+product", r"cross\s+product",
        r"scalar\s+triple\s+product", r"vector\s+triple\s+product",
        r"unit\s+vector", r"position\s+vector",
        r"angle\s+between\s+vectors", r"projection\s+of\s+vector",
        r"magnitude\s+of\s+vector", r"\ba\s*×\s*b\b",
        r"\ba\s*·\s*b\b", r"resultant\s+vector",
    ],
    "3D Geometry": [
        r"line\s+in\s+3D", r"plane\s+equation",
        r"angle\s+between\s+planes", r"distance\s+from\s+point\s+to\s+plane",
        r"coplanar\s+lines", r"shortest\s+distance",
        r"direction\s+cosines", r"skew\s+lines",
        r"direction\s+ratios", r"3D\s+geometry",
        r"equation\s+of\s+plane", r"foot\s+of\s+perpendicular",
    ],
    "Matrices": [
        r"\bmatrix\b", r"\bmatrices\b",
        r"transpose\s+of\s+matrix", r"inverse\s+of\s+matrix",
        r"adjoint\s+of\s+matrix", r"singular\s+matrix",
        r"row\s+operations", r"symmetric\s+matrix",
        r"skew.symmetric", r"orthogonal\s+matrix",
        r"trace\s+of\s+matrix", r"rank\s+of\s+matrix",
    ],
    "Determinants": [
        r"\bdeterminant\b", r"cramer.s\s+rule",
        r"\bcofactor\b", r"\bminor\b",
        r"expansion\s+of\s+determinant",
        r"properties\s+of\s+determinants",
        r"system\s+of\s+linear\s+equations",
        r"consistent\s+system", r"inconsistent\s+system",
        r"\|A\|",
    ],
    "Probability": [
        r"probability", r"bayes\s+theorem",
        r"conditional\s+probability", r"independent\s+events",
        r"sample\s+space", r"bernoulli\s+trials",
        r"binomial\s+distribution", r"random\s+variable",
        r"expected\s+value", r"probability\s+distribution",
        r"poisson\s+distribution",
    ],
    "Statistics": [
        r"\bmean\b", r"\bmedian\b", r"\bmode\b",
        r"\bvariance\b", r"standard\s+deviation",
        r"coefficient\s+of\s+variation",
        r"frequency\s+distribution", r"cumulative\s+frequency",
        r"arithmetic\s+mean",
    ],
    "Trigonometry": [
        r"\bsin\b", r"\bcos\b", r"\btan\b",
        r"\bsec\b", r"\bcosec\b", r"\bcot\b",
        r"inverse\s+trig", r"arcsin", r"arccos", r"arctan",
        r"compound\s+angle", r"double\s+angle\s+formula",
        r"half\s+angle\s+formula", r"sine\s+rule",
        r"cosine\s+rule", r"trigonometric\s+equation",
        r"general\s+solution\s+of\s+trig",
        r"principal\s+value",
    ],
    "Mathematical Reasoning": [
        r"boolean\s+expression", r"logical\s+equivalence",
        r"tautology", r"contradiction",
        r"truth\s+table", r"converse\s+of",
        r"contrapositive", r"biconditional",
        r"implication", r"negation\s+of",
        r"logical\s+connector",
    ],
}

# Compile all patterns
COMPILED_PATTERNS = {}
for chapter, patterns in PATTERNS.items():
    COMPILED_PATTERNS[chapter] = [re.compile(p, re.IGNORECASE) for p in patterns]

# Subject -> fallback chapter (for pass 3 when score == 0)
FALLBACK_CHAPTERS = {
    "Physics": "Kinematics",
    "Chemistry": "Some Basic Concepts of Chemistry",
    "Mathematics": "Sequences & Series",
}

# Subject -> allowed chapters
SUBJECT_CHAPTERS = {
    "Physics": [ch for ch, (_, subj) in CHAPTER_IDS.items() if subj == "Physics"],
    "Chemistry": [ch for ch, (_, subj) in CHAPTER_IDS.items() if subj == "Chemistry"],
    "Mathematics": [ch for ch, (_, subj) in CHAPTER_IDS.items() if subj == "Mathematics"],
}


def score_text(text: str, subject: str) -> dict:
    """Score text against all chapters. Only chapters matching subject."""
    allowed = SUBJECT_CHAPTERS.get(subject, list(CHAPTER_IDS.keys()))
    scores = {}
    for chapter in allowed:
        patterns = COMPILED_PATTERNS.get(chapter, [])
        score = sum(1 for pat in patterns if pat.search(text))
        scores[chapter] = score
    return scores


def classify_question(q: dict) -> tuple:
    """
    Returns (chapter, chapter_id, cluster_id, review_required, confidence).
    """
    subject = q.get("subject", "")
    text = q.get("question_text", "")
    q_number = q.get("question_number", 0)

    # ── Pass 1 & 2: keyword scoring ──────────────────────────
    scores = score_text(text, subject)
    best_chapter = max(scores, key=scores.get) if scores else ""
    best_score = scores.get(best_chapter, 0)

    if best_score >= 2:
        review = False
        confidence = 0.85
    elif best_score == 1:
        review = True
        confidence = 0.60
    else:
        # Pass 3: use Q-number position heuristic
        # Physics  Q1-30, Chemistry Q31-60, Math Q61-90 (but subject already set)
        if subject == "Physics":
            # Map to common physics chapters by Q number
            if q_number <= 5:
                best_chapter = "Kinematics"
            elif q_number <= 10:
                best_chapter = "Units & Measurements"
            elif q_number <= 15:
                best_chapter = "Laws of Motion"
            else:
                best_chapter = "NEEDS_REVIEW_PHYSICS"
        elif subject == "Chemistry":
            if q_number <= 35:
                best_chapter = "NEEDS_REVIEW_CHEMISTRY"
            elif q_number <= 50:
                best_chapter = "NEEDS_REVIEW_CHEMISTRY"
            else:
                best_chapter = "NEEDS_REVIEW_CHEMISTRY"
        elif subject == "Mathematics":
            best_chapter = "NEEDS_REVIEW_MATHEMATICS"
        else:
            best_chapter = "NEEDS_REVIEW_UNKNOWN"
        review = True
        confidence = 0.30

    # Build chapter_id and cluster_id
    chapter_id, _ = CHAPTER_IDS.get(best_chapter, ("", ""))
    if not chapter_id:
        chapter_id = ""

    if chapter_id:
        slug = re.sub(r"[^A-Z0-9]", "", chapter_id)
        cluster_id = f"{slug}-GEN01"
    else:
        cluster_id = ""

    return best_chapter, chapter_id, cluster_id, review, confidence


def main():
    print("Loading questions.jsonl …")
    questions = []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))

    total = len(questions)
    before_unclassified = sum(1 for q in questions if not q.get("chapter"))
    print(f"  Total questions: {total}")
    print(f"  Unclassified before: {before_unclassified}")

    reclassified_count = 0
    reclassified_chapters = defaultdict(int)
    still_unclassified = 0

    for q in questions:
        if q.get("chapter"):
            continue  # already classified, skip

        chapter, chapter_id, cluster_id, review, confidence = classify_question(q)

        q["chapter"] = chapter
        q["chapter_id"] = chapter_id
        q["cluster_id"] = cluster_id
        q["review_required"] = review
        q["extraction_confidence"] = max(q.get("extraction_confidence", 0.5), confidence)

        reclassified_count += 1
        reclassified_chapters[chapter] += 1
        if "NEEDS_REVIEW" in chapter:
            still_unclassified += 1

    print(f"\nReclassified: {reclassified_count}")
    print(f"Still needing review: {still_unclassified}")
    print(f"\nTop reclassified chapters:")
    for ch, cnt in sorted(reclassified_chapters.items(), key=lambda x: -x[1])[:20]:
        print(f"  {ch}: {cnt}")

    # Write updated questions.jsonl
    print("\nWriting questions.jsonl …")
    with open(DB_PATH, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Write updated questions.csv
    print("Writing questions.csv …")
    csv_fields = [
        "question_id", "subject", "chapter", "topic", "concept",
        "cluster_id", "year", "date", "shift", "question_number",
        "question_type", "question_text", "correct_answer", "difficulty",
        "source_file", "source_page", "extraction_confidence", "review_required"
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        for q in questions:
            writer.writerow(q)

    print("\n✅ Done!")
    print(f"  Before unclassified: {before_unclassified}")
    print(f"  Reclassified: {reclassified_count}")
    print(f"  Still NEEDS_REVIEW: {still_unclassified}")
    print(f"  Net resolved: {reclassified_count - still_unclassified}")

    return reclassified_count, still_unclassified, reclassified_chapters


if __name__ == "__main__":
    main()
