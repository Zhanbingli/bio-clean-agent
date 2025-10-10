"""Medical data handling modules for specialized data types."""

from .clinical_trials import ClinicalTrialHandler
from .ehr import EHRHandler
from .imaging import ImagingMetadataHandler

__all__ = ["ClinicalTrialHandler", "EHRHandler", "ImagingMetadataHandler"]
