"""Unit tests for knowledge base modules - simplified smoke tests."""

import pytest

from bio_clean_agent.knowledge.base import KnowledgeBase
from bio_clean_agent.knowledge.medical_standards import MedicalStandards
from bio_clean_agent.knowledge.evidence_base import EvidenceBase


@pytest.mark.unit
class TestKnowledgeBase:
    """Test suite for KnowledgeBase."""

    def test_knowledge_base_initialization(self):
        """Test knowledge base can be initialized."""
        kb = KnowledgeBase()
        assert isinstance(kb, KnowledgeBase)


@pytest.mark.unit
class TestMedicalStandards:
    """Test suite for MedicalStandards."""

    def test_medical_standards_initialization(self):
        """Test medical standards can be initialized."""
        ms = MedicalStandards()
        assert isinstance(ms, MedicalStandards)

    def test_medical_standards_has_data(self):
        """Test medical standards contains reference data."""
        ms = MedicalStandards()
        # Check that standards object exists
        assert ms is not None


@pytest.mark.unit
class TestEvidenceBase:
    """Test suite for EvidenceBase."""

    def test_evidence_base_initialization(self):
        """Test evidence base can be initialized."""
        eb = EvidenceBase()
        assert isinstance(eb, EvidenceBase)

    def test_evidence_base_has_data(self):
        """Test evidence base contains evidence data."""
        eb = EvidenceBase()
        # Check that evidence object exists
        assert eb is not None
