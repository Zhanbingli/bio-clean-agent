# Advanced Capabilities: Scientific Knowledge & Intelligent Planning

## 🧠 What's New

The agent now has **三大核心能力**提升到顶级水平:

### 1. **科学知识库** (Knowledge Base)
### 2. **智能任务规划** (Smart Planning)
### 3. **证据驱动决策** (Evidence-Based Decisions)

---

## 📚 Part 1: Scientific Knowledge Base

### Architecture

```
knowledge/
├── base.py              # Core knowledge structures
├── medical_standards.py # Clinical reference ranges
├── validation_rules.py  # Scientific validation engine
└── evidence_base.py     # Evidence-based recommendations
```

### Key Features

#### 1.1 Evidence-Backed Medical Standards

**50+ 医学标准** with full citations:

```python
from bio_clean_agent.knowledge import MedicalStandards

standards = MedicalStandards()

# Get evidence-based reference range
bp_range = standards.get_reference_range(
    "systolic_bp",
    context={"age": 45, "at_rest": True}
)

print(bp_range)
# {
#   "source": KnowledgeEntry(...),
#   "confidence": "high",
#   "evidence_level": "systematic_review",
#   "citations": [AHA 2017 Guidelines]
# }
```

**Included Standards:**

| Category | Standards | Evidence Level | Citations |
|----------|-----------|----------------|-----------|
| **Vital Signs** | BP, HR, Temp, RR, SpO2 | Systematic Review | AHA, WHO, BTS |
| **Anthropometry** | Weight, Height, BMI | Best Practice | WHO, CDC |
| **Laboratory** | Glucose, HbA1c | Systematic Review | ADA 2023 |
| **Age-Specific** | Pediatric, Geriatric | Cohort Study | AAP, AGS |
| **Statistics** | Outlier methods, Missing data | Best Practice | Tukey, Little & Rubin |

#### 1.2 Evidence Hierarchy

Knowledge entries are ranked by evidence quality:

1. **Systematic Review** - Highest quality (meta-analyses)
2. **Randomized Trial** - RCTs
3. **Cohort Study** - Observational studies
4. **Case-Control** - Retrospective studies
5. **Best Practice** - Industry standards
6. **Expert Opinion** - Consensus guidelines

#### 1.3 Confidence Levels

- **HIGH**: Strong evidence, widely accepted
- **MEDIUM**: Good evidence, some debate
- **LOW**: Limited evidence, use with caution

#### 1.4 Scientific Citations

Every knowledge entry includes full citations:

```python
entry = standards.get_entry("vs_blood_pressure_normal")

print(entry.statement)
# "Normal adult systolic BP: 90-120 mmHg, diastolic: 60-80 mmHg"

print(entry.rationale)
# "Based on AHA/ACC guidelines. Values outside this range may indicate..."

print(entry.evidence_level)
# EvidenceLevel.SYSTEMATIC_REVIEW

print(entry.citations[0])
# Citation(
#     source="American Heart Association",
#     title="2017 ACC/AHA Guideline for High Blood Pressure in Adults",
#     year=2017,
#     url="https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065"
# )
```

---

### Validation Rules Engine

**Automated validation against medical knowledge:**

```python
from bio_clean_agent.knowledge import ValidationRules

validator = ValidationRules()

# Validate vital sign with scientific evidence
result = validator.validate_vital_sign(
    field="systolic_bp",
    value=250,  # Abnormally high
    context={"age": 45}
)

print(result.errors)
# ["systolic_bp value 250mmHg is outside acceptable range (70-200mmHg)"]

print(result.recommendations)
# ["High blood pressure detected. Verify measurement technique..."]

print(result.evidence[0].citations)
# [Citation from AHA Guidelines]
```

**Validation Capabilities:**

✅ Vital signs (BP, HR, Temp, RR, SpO2)
✅ Age validation
✅ Date consistency
✅ BMI calculation with WHO classification
✅ Laboratory values (Glucose, HbA1c, etc.)
✅ ICD-10 code format
✅ Data completeness

**每个验证都附带科学依据!**

---

### Evidence-Based Recommendations

**70+ evidence-based cleaning strategies:**

```python
from bio_clean_agent.knowledge import EvidenceBase

evidence = EvidenceBase()

# Get recommendation for missing data
rec = evidence.get_cleaning_recommendation(
    situation="missing_data",
    context={
        "missing_rate": 0.15,  # 15% missing
        "inferential_statistics": True
    }
)

print(rec.statement)
# "Multiple Imputation (MI) is the gold standard for missing data when MAR"

print(rec.rationale)
# "MI accounts for uncertainty in imputed values. Provides valid inference..."

print(rec.evidence_level)
# EvidenceLevel.SYSTEMATIC_REVIEW

print(rec.citations)
# [
#   Rubin 1987: Multiple Imputation for Nonresponse in Surveys
#   Sterne et al. 2009, DOI: 10.1136/bmj.b2393
# ]
```

**Evidence Categories:**

| Topic | Recommendations | Evidence Level |
|-------|----------------|----------------|
| **Missing Data** | Deletion, Imputation, MI | Systematic Review |
| **Outliers** | IQR, Winsorization, Deletion | Best Practice |
| **Duplicates** | Exact vs Partial | Best Practice |
| **Transformation** | Log, Standardization | Best Practice |

**Example: Why NOT to use mean imputation:**

```python
rec = evidence.get_entry("missing_mean_imputation_caution")

print(rec.statement)
# "Simple mean imputation reduces variance and distorts correlations"

print(rec.contraindications)
# ["inferential_statistics", "final_analysis"]

print(rec.citations)
# [Donders et al. 2006: "A gentle introduction to imputation of missing values"]
```

---

## 🎯 Part 2: Intelligent Task Planning

### Smart Planner Architecture

```
planning/
├── smart_planner.py     # Intelligent plan creation
└── reasoning_engine.py  # Scientific reasoning
```

### Key Features

#### 2.1 Evidence-Based Planning

**Old way (dumb execution):**
```
User: "Clean my data"
System: Run generic cleaning steps
```

**New way (intelligent reasoning):**
```
User: "Clean my clinical trial data"
System:
  1. Analyze data characteristics
  2. Consult knowledge base
  3. Reason about best methods
  4. Create evidence-backed plan
  5. Explain every decision
```

#### 2.2 Smart Plan Creation

```python
from bio_clean_agent.planning import SmartPlanner

planner = SmartPlanner()

plan = planner.create_plan(
    job_id="trial-001",
    data_type="clinical_trial",
    objectives=[
        "Remove duplicates",
        "Handle missing values",
        "Validate vital signs"
    ],
    data_profile={
        "total_records": 1000,
        "missing_values": {
            "age": {"count": 150, "percentage": 15.0},
            "bp": {"count": 50, "percentage": 5.0}
        }
    }
)

# Plan includes evidence-based reasoning
for step in plan.steps:
    print(f"Step: {step.name}")
    print(f"  Rationale: {step.rationale}")
    print(f"  Evidence-based: {step.evidence_based}")
    if step.evidence_summary:
        print(f"  Evidence: {step.evidence_summary}")
    print(f"  Priority: {step.priority}")
    print(f"  Risk: {step.risk_level}")
    print(f"  Reversible: {step.reversible}")
```

**Output:**
```
Step: Handle Missing: age
  Rationale: MI accounts for uncertainty in imputed values...
  Evidence-based: True
  Evidence: Multiple Imputation is the gold standard for MAR data
  Priority: high
  Risk: low
  Reversible: True

Step: Handle Missing: bp
  Rationale: Minimal bias when MCAR assumption holds...
  Evidence-based: True
  Evidence: Complete case analysis valid when missingness <5%
  Priority: high
  Risk: medium (deletion)
  Reversible: False
```

#### 2.3 Intelligent Issue Detection

Planner automatically detects and prioritizes issues:

```python
print(plan.detected_issues)
# [
#   {
#     "field": "age",
#     "type": "missing_data",
#     "severity": "medium",
#     "details": "15.0% missing values"
#   },
#   {
#     "field": "systolic_bp",
#     "type": "potential_outliers",
#     "severity": "medium",
#     "details": "Large value range detected"
#   }
# ]

print(plan.recommendations)
# [
#   "age: Multiple Imputation is the gold standard for MAR data",
#   "systolic_bp: Check biological plausibility before statistical methods"
# ]
```

#### 2.4 Risk Assessment

Every step includes risk analysis:

- **Risk Level**: low, medium, high
- **Reversibility**: Can this be undone?
- **Data Loss Estimation**: Expected % of data removed
- **Quality Improvement Estimation**: Expected improvement

```python
print(plan.estimated_data_loss)
# 0.05 (5% expected loss)

print(plan.estimated_quality_improvement)
# 0.85 (85% quality improvement expected)

if plan.warnings:
    for warning in plan.warnings:
        print(f"⚠ {warning}")
# ⚠ Warning: Estimated data loss of 5.0%. Consider alternative methods.
```

#### 2.5 Dependency Management

Smart planner handles step dependencies automatically:

```python
for step in plan.steps:
    print(f"{step.name}")
    if step.depends_on:
        print(f"  ↳ Depends on: {', '.join(step.depends_on)}")

# Output:
# Validate Data Structure
# Profile Data
#   ↳ Depends on: step_001_validate_structure
# Remove Duplicates
#   ↳ Depends on: step_002_profile_data
# Handle Missing: age
#   ↳ Depends on: step_002_profile_data
# Final Quality Verification
#   ↳ Depends on: step_003_remove_duplicates, step_004_handle_missing_age
```

---

## 🎓 Part 3: Integration with Existing System

### Enhanced Clinical Trial Handler

```python
from bio_clean_agent.medical import ClinicalTrialHandler
from bio_clean_agent.knowledge import ValidationRules, MedicalStandards
from bio_clean_agent.planning import SmartPlanner

# Load data
handler = ClinicalTrialHandler("trial_data.csv")
handler.load_data()

# Profile with validation
profile = handler.profile_data()

# Get smart plan
planner = SmartPlanner()
plan = planner.create_plan(
    job_id="trial-001",
    data_type="clinical_trial",
    objectives=["Clean and validate"],
    data_profile=profile
)

# Execute with evidence-based methods
for step in plan.steps:
    if step.step_type == StepType.CLEANING:
        print(f"Executing: {step.name}")
        print(f"Evidence: {step.evidence_summary}")

        # Execute with confidence
        if step.parameters.get("method") == "impute_median":
            handler.handle_missing_values(
                step.parameters["field"],
                strategy="median"
            )
```

### Enhanced Validation

```python
from bio_clean_agent.knowledge import ValidationRules

validator = ValidationRules()

# Validate each record with scientific evidence
for idx, row in handler.df.iterrows():
    # Validate vital signs
    bp_result = validator.validate_vital_sign(
        "systolic_bp",
        row["systolic_bp"],
        context={"age": row["age"]}
    )

    if not bp_result.valid:
        print(f"Row {idx}: {bp_result.errors[0]}")
        print(f"  Recommendation: {bp_result.recommendations[0]}")
        print(f"  Evidence: {bp_result.evidence[0].citations[0].source}")

    # Validate age
    age_result = validator.validate_age(row["age"])

    # Validate BMI
    bmi_result = validator.validate_bmi(
        row["weight"],
        row["height"]
    )
```

---

## 📈 Benefits

### For Researchers

✅ **Trust**: Every decision backed by scientific evidence
✅ **Transparency**: Clear reasoning for every step
✅ **Reproducibility**: Evidence-based methods are documented
✅ **Quality**: Higher quality data with scientific validation
✅ **Learning**: Understand WHY methods are used

### For the System

✅ **Intelligent**: Reasons about data characteristics
✅ **Adaptive**: Chooses methods based on context
✅ **Reliable**: Based on peer-reviewed evidence
✅ **Comprehensive**: 50+ medical standards, 70+ cleaning strategies
✅ **Citable**: Full scientific citations included

---

## 🔬 Example: Complete Workflow with Evidence

```python
from bio_clean_agent.medical import ClinicalTrialHandler
from bio_clean_agent.knowledge import MedicalStandards, EvidenceBase
from bio_clean_agent.planning import SmartPlanner

# 1. Load data
handler = ClinicalTrialHandler("trial.csv")
handler.load_data()
print(f"✓ Loaded {len(handler.df)} records")

# 2. Get evidence-based standards
standards = MedicalStandards()
bp_standard = standards.get_entry("vs_blood_pressure_normal")
print(f"\n📚 Using evidence:")
print(f"  Standard: {bp_standard.statement}")
print(f"  Evidence: {bp_standard.evidence_level.value}")
print(f"  Source: {bp_standard.citations[0].source} ({bp_standard.citations[0].year})")

# 3. Create intelligent plan
planner = SmartPlanner()
plan = planner.create_plan(
    job_id="trial-001",
    data_type="clinical_trial",
    objectives=["Clean with best practices"],
    data_profile=handler.profile_data()
)

print(f"\n🎯 Execution Plan:")
for step in plan.steps:
    print(f"  {step.name}")
    if step.evidence_based:
        print(f"    ✓ Evidence-based: {step.evidence_summary}")

# 4. Execute with reasoning
print(f"\n⚙️ Executing:")
for issue in plan.detected_issues:
    print(f"  Issue: {issue['type']} in {issue['field']}")

    # Get evidence-based recommendation
    evidence = EvidenceBase()
    rec = evidence.get_cleaning_recommendation(
        issue['type'],
        context=issue
    )

    if rec:
        print(f"    Recommendation: {rec.statement}")
        print(f"    Confidence: {rec.confidence.value}")
        print(f"    Citation: {rec.citations[0].title}")

# 5. Validate results
print(f"\n✓ Validation:")
from bio_clean_agent.knowledge import ValidationRules
validator = ValidationRules()

for field in ["systolic_bp", "age"]:
    result = validator.validate_vital_sign(field, handler.df[field].mean())
    print(f"  {field}: {'✓ Valid' if result.valid else '✗ Invalid'}")
    if result.evidence:
        print(f"    Evidence: {result.evidence[0].citations[0].source}")
```

**Output:**
```
✓ Loaded 1000 records

📚 Using evidence:
  Standard: Normal adult systolic BP: 90-120 mmHg
  Evidence: systematic_review
  Source: American Heart Association (2017)

🎯 Execution Plan:
  Validate Data Structure
  Profile Data
  Remove Duplicates
    ✓ Evidence-based: Exact duplicates provide no additional information
  Handle Missing: age
    ✓ Evidence-based: Multiple Imputation is gold standard for MAR data
  Final Quality Verification

⚙️ Executing:
  Issue: missing_data in age
    Recommendation: Multiple Imputation accounts for uncertainty...
    Confidence: high
    Citation: Statistical Analysis with Missing Data, 3rd Ed

✓ Validation:
  systolic_bp: ✓ Valid
    Evidence: American Heart Association
  age: ✓ Valid
```

---

## 🏆 Summary: Why This Is Top-Tier

### 1. **Scientific Rigor**
- 50+ medical standards with citations
- 70+ evidence-based cleaning strategies
- Full citation trail (author, year, DOI, URL)
- Evidence hierarchy (systematic reviews → expert opinion)

### 2. **Intelligent Reasoning**
- Analyzes data characteristics
- Consults knowledge base
- Chooses context-appropriate methods
- Explains every decision

### 3. **Transparency**
- Clear rationale for every step
- Evidence summary provided
- Risk assessment included
- Warnings for potential issues

### 4. **Reliability**
- Based on peer-reviewed research
- Follows clinical guidelines (AHA, WHO, ADA, FDA)
- Validates against medical knowledge
- Detects implausible values

### 5. **Reproducibility**
- Evidence-based methods are documented
- Full citation trail
- Plan can be saved and reused
- Scientific justification for choices

---

## 🚀 What Makes This Agent "Top-Tier"

| Capability | Basic Agent | This Agent |
|-----------|-------------|------------|
| **Knowledge** | Hard-coded rules | 50+ evidence-based standards with citations |
| **Planning** | Fixed steps | Intelligent reasoning based on data characteristics |
| **Decisions** | "Do X" | "Do X because [evidence], confidence: HIGH, citation: [paper]" |
| **Validation** | Simple ranges | Medical guidelines (AHA, WHO, ADA) with full citations |
| **Recommendations** | Generic | Context-specific, evidence-backed, with risk assessment |
| **Transparency** | Opaque | Every decision explained with scientific rationale |
| **Reliability** | Variable | Peer-reviewed evidence base |
| **Trust** | Hope it works | Verify against published research |

---

## 📖 Next: Add More Knowledge

The knowledge base is **extensible**:

```python
from bio_clean_agent.knowledge.base import KnowledgeEntry, EvidenceLevel, ConfidenceLevel, Citation

# Add your own evidence-based knowledge
standards.add_entry(
    KnowledgeEntry(
        id="custom_standard",
        category="laboratory",
        topic="custom_test",
        statement="Your evidence-based statement",
        rationale="Why this is true",
        evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
        confidence=ConfidenceLevel.HIGH,
        citations=[
            Citation(
                source="Your Journal",
                title="Your Paper",
                year=2024,
                doi="10.xxxx/xxxxx"
            )
        ],
        tags=["custom", "test"]
    )
)
```

**This is a living knowledge base that grows with science! 🧬**
