# Clinical Trials Sample Data

## Overview

This directory contains synthetic clinical trial data for testing the Bio-Clean-Agent system.

## Files

### `sample_trial_basic.csv`
- **Description**: Basic clinical trial with common vital signs
- **Subjects**: 50 synthetic patients
- **Visits**: 3 visits per patient
- **Measurements**: Blood pressure, heart rate, temperature, weight

### `sample_trial_with_issues.csv`
- **Description**: Trial data with intentional quality issues for testing
- **Issues included**:
  - Missing values (~10%)
  - Duplicates (~5%)
  - Out-of-range values (~3%)
  - Inconsistent dates

### `multicenter_trial.csv`
- **Description**: Multi-center trial data
- **Centers**: 3 sites
- **Subjects**: 100 synthetic patients
- **Additional fields**: Site ID, enrollment date, randomization group

## Data Schema

### Common Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| patient_id | Integer | Unique patient identifier | 1001 |
| visit_number | Integer | Visit sequence | 1, 2, 3 |
| visit_date | Date | Visit date | 2024-01-15 |
| blood_pressure_systolic | Integer | Systolic BP (mmHg) | 120 |
| blood_pressure_diastolic | Integer | Diastolic BP (mmHg) | 80 |
| heart_rate | Integer | Heart rate (bpm) | 72 |
| temperature | Float | Body temperature (°C) | 36.8 |
| weight | Float | Weight (kg) | 75.5 |

## Usage Example

```python
from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler

handler = ClinicalTrialHandler()

# Load data
data = handler.load("data/clinical_trials/sample_trial_basic.csv")

# Assess quality
quality = handler.assess_quality(data)
print(f"Quality Score: {quality['score']:.2f}")

# Detect issues
issues = handler.detect_issues(data)
for issue in issues:
    print(f"- {issue}")
```

## Reference Ranges

All data generated using standard clinical reference ranges:

- **Blood Pressure**: 90-140 / 60-90 mmHg
- **Heart Rate**: 60-100 bpm
- **Temperature**: 36.1-37.2 °C
- **Weight**: 45-120 kg

## Privacy

**All data is 100% synthetic. No real patient data included.**
