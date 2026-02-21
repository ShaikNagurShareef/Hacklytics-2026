"""
Prompt templates for the Diagnostic Agent.

Includes modality-specific analysis prompts and the master report
generation prompt following ACR (American College of Radiology) guidelines.
"""

# =====================================================================
# Master image analysis prompt — sent to Gemini Vision
# =====================================================================

DIAGNOSTIC_SYSTEM_PROMPT = """\
You are **MEDORA Diagnostic AI**, an expert-level medical imaging analysis
assistant embedded in the MEDORA healthcare platform.

You operate under the following principles:
1. You NEVER make definitive diagnoses — you provide **preliminary AI-assisted
   observations** that must be verified by a board-certified radiologist or
   ophthalmologist.
2. You follow **ACR (American College of Radiology)** reporting standards.
3. You are systematic, thorough, and use precise medical terminology while
   remaining understandable.
4. You flag **critical findings** prominently for immediate attention.
5. You always include a professional disclaimer.

When no patient context is provided, note this in the report and make
observations based solely on the image.
"""


# =====================================================================
# Modality-specific analysis prompts
# =====================================================================

XRAY_ANALYSIS_PROMPT = """\
Analyse this X-ray image systematically. Follow the standard radiological
reading pattern for the body region:

**Chest X-ray reading order (if chest):**
1. **Trachea & mediastinum** — midline? widened?
2. **Heart** — size (cardiothoracic ratio), shape, silhouette
3. **Lungs** — opacities, infiltrates, masses, pneumothorax, effusions
4. **Diaphragm** — shape, free air underneath
5. **Bones** — ribs, clavicles, spine — fractures, lytic/blastic lesions
6. **Soft tissues** — subcutaneous emphysema, foreign bodies
7. **Lines & tubes** — position of any catheters, ET tube, pacemaker

**Extremity X-ray reading order (if extremity):**
1. **Alignment** — joint congruity, anatomical alignment
2. **Bone** — cortical breaks, periosteal reaction, density changes
3. **Cartilage/Joint space** — narrowing, osteophytes
4. **Soft tissue** — swelling, calcification, foreign bodies

Report any abnormalities with their anatomical location, size estimate,
and clinical significance.
"""

CT_ANALYSIS_PROMPT = """\
Analyse this CT scan image systematically. Evaluate:

1. **Target organ/region** — primary pathology assessment
2. **Window settings** — note whether this appears to be soft tissue,
   lung, or bone window
3. **Contrast** — note if contrast-enhanced (enhancement patterns)
4. **Systematic review:**
   - Parenchymal abnormalities (masses, nodules, consolidation)
   - Vascular structures (aneurysm, thrombosis, enhancement)
   - Lymphadenopathy
   - Effusions or free fluid
   - Osseous structures
   - Incidental findings
5. **Measurements** — estimate sizes of any significant lesions
6. **Comparison** — note if prior studies would be helpful

For brain CT specifically:
- Grey-white matter differentiation
- Midline shift
- Ventricle size (hydrocephalus)
- Hemorrhage (epidural, subdural, subarachnoid, intraparenchymal)
- Mass effect
- Skull fractures
"""

MRI_ANALYSIS_PROMPT = """\
Analyse this MRI image systematically. Evaluate:

1. **Sequence identification** — attempt to identify T1, T2, FLAIR,
   DWI, contrast-enhanced based on signal characteristics
2. **Signal abnormalities** — hyper/hypointense lesions relative to
   the sequence
3. **Systematic review by anatomy:**
   - Brain: cortex, white matter, basal ganglia, ventricles,
     posterior fossa, extra-axial spaces
   - Spine: cord signal, disc herniations, stenosis, alignment
   - Joint: ligaments, menisci, cartilage, bone marrow, effusion
4. **Enhancement patterns** — if contrast-enhanced
5. **Mass effect** — compression, displacement, herniation
6. **Measurements** — lesion sizes
7. **Differential diagnosis** — based on signal characteristics and
   morphology
"""

ULTRASOUND_ANALYSIS_PROMPT = """\
Analyse this ultrasound image systematically. Evaluate:

1. **Organ identification** — target organ and orientation
2. **Echotexture** — homogeneous vs heterogeneous parenchyma
3. **Focal lesions** — cystic, solid, or mixed; echogenicity
4. **Doppler** — if colour/spectral Doppler is present, evaluate
   flow patterns and velocities
5. **Fluid collections** — free fluid, effusions, ascites
6. **Measurements** — organ size, lesion dimensions
7. **Adjacent structures** — lymph nodes, vessels, surrounding tissue
"""

OCT_ANALYSIS_PROMPT = """\
Analyse this Optical Coherence Tomography (OCT) image systematically.
Evaluate the retinal layers:

1. **Retinal layer integrity:**
   - Internal Limiting Membrane (ILM)
   - Nerve Fibre Layer (NFL) — thickness, defects
   - Ganglion Cell Layer (GCL)
   - Inner/Outer Plexiform Layers
   - Inner/Outer Nuclear Layers
   - Photoreceptor layer — IS/OS junction integrity
   - Retinal Pigment Epithelium (RPE) — irregularities, detachment
   - Bruch's membrane
2. **Macular assessment:**
   - Central foveal thickness
   - Macular oedema (CME, DME)
   - Epiretinal membrane
   - Macular hole (full/lamellar)
   - Vitreomacular traction
3. **Sub-retinal space:**
   - Sub-retinal fluid
   - Choroidal neovascularisation (CNV)
   - Pigment epithelial detachment (PED)
4. **RNFL analysis** — if RNFL thickness map available:
   - Quadrant analysis (superior, inferior, nasal, temporal)
   - Comparison to normative database
   - Glaucoma progression indicators
5. **Choroid** — thickness, polypoidal lesions
"""

FUNDOSCOPY_ANALYSIS_PROMPT = """\
Analyse this fundus photograph systematically. Evaluate:

1. **Optic disc:**
   - Colour, margins, cup-to-disc ratio
   - Papilloedema, pallor, neovascularisation
   - Disc haemorrhages
2. **Macula:**
   - Foveal reflex
   - Drusen (hard/soft)
   - Pigment changes, geographic atrophy
   - Macular oedema
   - Exudates (hard/soft)
3. **Vessels:**
   - Arteriolar calibre, AV nicking
   - Venous dilation, beading
   - Neovascularisation (NVD, NVE)
   - Emboli
4. **Retinal background:**
   - Haemorrhages (dot-blot, flame-shaped, pre-retinal)
   - Cotton-wool spots
   - Microaneurysms
   - Pigmentary changes
   - Retinal detachment signs
5. **Peripheral retina:**
   - Lattice degeneration
   - Tears, holes
   - Peripheral neovascularisation

Grade diabetic retinopathy if applicable (mild/moderate/severe NPDR, PDR).
Grade AMD if applicable (early/intermediate/advanced).
Grade hypertensive retinopathy if applicable (Keith-Wagener-Barker).
"""

MAMMOGRAPHY_ANALYSIS_PROMPT = """\
Analyse this mammographic image systematically using BI-RADS criteria.
Evaluate:

1. **Breast composition:**
   - ACR density category (A, B, C, D)
2. **Masses:**
   - Shape (round, oval, irregular)
   - Margins (circumscribed, obscured, microlobulated, indistinct, spiculated)
   - Density (fat-containing, low, equal, high)
3. **Calcifications:**
   - Morphology (round, amorphous, coarse heterogeneous, fine pleomorphic,
     fine linear/branching)
   - Distribution (diffuse, regional, grouped, linear, segmental)
4. **Architectural distortion**
5. **Asymmetries** (asymmetry, global, focal, developing)
6. **Associated features** — skin retraction, nipple retraction,
   axillary lymphadenopathy
7. **BI-RADS assessment category** (0-6)
"""

GENERIC_ANALYSIS_PROMPT = """\
Analyse this medical image systematically. Since the exact modality
could not be determined, provide a thorough general assessment:

1. **Identify the imaging modality** if possible (X-ray, CT, MRI,
   ultrasound, nuclear medicine, etc.)
2. **Identify the body region** and anatomical structures visible
3. **Systematic findings** — go through visible structures methodically
4. **Abnormalities** — describe any abnormal findings with location,
   size, and characteristics
5. **Normal findings** — confirm normal structures
6. **Impression** — summarise key findings
"""


# =====================================================================
# Report formatting prompt
# =====================================================================

REPORT_GENERATION_PROMPT = """\
You are generating a **standard medical diagnostic imaging report** following
ACR (American College of Radiology) guidelines.

Given the AI image analysis below, format it into this EXACT structure:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## DIAGNOSTIC IMAGING REPORT

**Report ID:** [auto-generated]
**Date:** [current date]
**Modality:** [X-ray / CT / MRI / Ultrasound / OCT / Fundoscopy / etc.]
**Body Region:** [anatomical region]

---

### PATIENT INFORMATION
| Field | Value |
|-------|-------|
| Age | [if provided, else "Not provided"] |
| Gender | [if provided, else "Not provided"] |
| Referring Physician | [if provided, else "Not provided"] |

---

### CLINICAL INDICATION
[Why this study was ordered — from patient context or "Not provided"]

### TECHNIQUE
[Imaging parameters, contrast, views, sequences — inferred from image]

### COMPARISON
[Prior studies if mentioned, else "No prior studies available for comparison."]

---

### FINDINGS
[Systematic, detailed findings organised by anatomical structure.
Each finding on its own line with precise medical terminology.
Include measurements where estimable.
Note both normal AND abnormal findings.]

---

### IMPRESSION
[Numbered list of key findings, most significant first.
Include differential diagnosis where appropriate.]

### RECOMMENDATIONS
[Follow-up imaging, clinical correlation, referrals.
Include timeframe for follow-up if applicable.]

---

### ⚠️ CRITICAL FINDINGS
[If any critical/urgent findings exist, list them here with
recommended immediate action. If none, state "No critical findings."]

---

**Urgency Level:** [ROUTINE / SEMI-URGENT / URGENT / CRITICAL]

> 📋 *This report was generated by MEDORA Diagnostic AI and is NOT a
> substitute for interpretation by a board-certified radiologist or
> ophthalmologist. All findings must be clinically correlated and
> verified by a qualified medical professional.*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rules:
- Be systematic and thorough — do NOT skip anatomical structures.
- Use standard medical terminology with brief layperson explanations
  in parentheses where helpful.
- Always provide an impression section with numbered key findings.
- Grade severity using standard scales where applicable
  (BI-RADS for mammography, Keith-Wagener-Barker for hypertensive
  retinopathy, NPDR/PDR for diabetic retinopathy, etc.)
- Flag critical findings prominently.
- If the image quality is poor, note this under Technique.
"""


# =====================================================================
# Modality detection prompt (for LLM-based detection)
# =====================================================================

MODALITY_DETECTION_PROMPT = """\
Look at this medical image and determine:
1. The **imaging modality** (choose one): x-ray, ct, mri, ultrasound,
   oct, fundoscopy, mammography, fluoroscopy, pet, dexa, unknown
2. The **body region** (choose one): head, brain, neck, chest, abdomen,
   pelvis, cervical_spine, thoracic_spine, lumbar_spine, upper_extremity,
   lower_extremity, knee, shoulder, hand_wrist, hip, ankle_foot, eye,
   breast, cardiac, whole_body, unknown

Respond in EXACTLY this JSON format, nothing else:
{"modality": "...", "body_region": "..."}
"""


# =====================================================================
# Prompt selector
# =====================================================================

MODALITY_PROMPTS = {
    "x-ray": XRAY_ANALYSIS_PROMPT,
    "ct": CT_ANALYSIS_PROMPT,
    "mri": MRI_ANALYSIS_PROMPT,
    "ultrasound": ULTRASOUND_ANALYSIS_PROMPT,
    "oct": OCT_ANALYSIS_PROMPT,
    "fundoscopy": FUNDOSCOPY_ANALYSIS_PROMPT,
    "mammography": MAMMOGRAPHY_ANALYSIS_PROMPT,
}
