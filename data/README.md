# Sample Data for Bio-Clean-Agent

This directory contains anonymized sample data for testing and demonstration purposes.

## ⚠️ Privacy Notice

**ALL DATA IN THIS DIRECTORY IS COMPLETELY ANONYMIZED AND SYNTHETIC**

- No real patient information
- HIPAA compliant
- Safe for public distribution
- For demonstration purposes only

## 📁 Data Categories

### Clinical Trials (`clinical_trials/`)
Synthetic clinical trial data for testing data cleaning workflows.

- `sample_trial_basic.csv` - Basic trial with vital signs
- `sample_trial_with_issues.csv` - Trial data with quality issues (for testing)
- `multicenter_trial.csv` - Multi-center trial data

### EHR Data (`ehr/`)
Electronic Health Record sample data (fully anonymized).

- `sample_ehr_anonymized.csv` - Basic EHR data
- `ehr_with_phi_examples.csv` - Examples showing PHI masking

### Genomics Data (`genomics/`)
Sequencing data samples.

- `README.md` - Instructions for genomics data
- Note: Actual FASTQ files not included due to size

### Transcriptomics Data (`transcriptomics/`)
Gene expression data samples.

- `gene_expression_sample.csv` - Sample gene expression matrix

### Metabolomics Data (`metabolomics/`)
Metabolite measurement data.

- `metabolite_data_sample.csv` - Sample metabolomics data

### Imaging Metadata (`imaging/`)
Medical imaging metadata (DICOM tags).

- `dicom_metadata_sample.csv` - Sample DICOM metadata

## 🚀 Usage

### Using with CLI

```bash
bio-clean-agent process --input data/clinical_trials/sample_trial_basic.csv
```

### Using with Python API

```python
from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler

handler = ClinicalTrialHandler()
data = handler.load("data/clinical_trials/sample_trial_basic.csv")
quality = handler.assess_quality(data)
```

### Using with Web Interface

1. Start web server: `python start_web.py`
2. Upload files from `data/` directory
3. Select appropriate data type
4. Review cleaning results

## 📝 Data Generation

To generate additional synthetic data:

```python
# See examples/generate_sample_data.py
python examples/generate_sample_data.py
```

## 🔒 Security

- All sample data is synthetic
- No real PHI/PII included
- Safe for version control
- Public distribution approved
