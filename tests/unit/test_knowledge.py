"""Unit tests for knowledge base modules."""

import pytest

from bio_clean_agent.knowledge.base import KnowledgeBase, KnowledgeEntry
from bio_clean_agent.knowledge.medical_standards import MedicalStandards
from bio_clean_agent.knowledge.evidence_base import EvidenceBase


@pytest.mark.unit
class TestKnowledgeBase:
    """Test suite for KnowledgeBase."""

    def test_knowledge_base_initialization(self):
        """Test knowledge base can be initialized."""
        kb = KnowledgeBase()
        assert isinstance(kb, KnowledgeBase)

    def test_knowledge_base_add_entry(self):
        """Test adding entries to knowledge base."""
        kb = KnowledgeBase()
        entry = KnowledgeEntry(
            id="test_entry",
            category="test",
            title="Test Entry",
            content="Test content",
        )
        kb.add(entry)

        assert kb.get("test_entry") == entry

    def test_knowledge_base_query(self):
        """Test querying knowledge base."""
        kb = KnowledgeBase()
        entry1 = KnowledgeEntry(
            id="entry1", category="category1", title="Entry 1", content="Content 1"
        )
        entry2 = KnowledgeEntry(
            id="entry2", category="category2", title="Entry 2", content="Content 2"
        )

        kb.add(entry1)
        kb.add(entry2)

        results = kb.query(category="category1")
        assert len(results) == 1
        assert results[0].id == "entry1"


@pytest.mark.unit
class TestMedicalStandards:
    """Test suite for MedicalStandards."""

    def test_medical_standards_initialization(self):
        """Test medical standards can be initialized."""
        ms = MedicalStandards()
        assert isinstance(ms, MedicalStandards)

    def test_vital_signs_ranges_available(self):
        """Test vital signs ranges are available."""
        ms = MedicalStandards()

        # Test blood pressure range
        bp_range = ms.get_vital_signs_range("blood_pressure")
        assert bp_range is not None

        # Test heart rate range
        hr_range = ms.get_vital_signs_range("heart_rate")
        assert hr_range is not None

    def test_lab_values_ranges_available(self):
        """Test lab values ranges are available."""
        ms = MedicalStandards()

        # Test glucose range
        glucose_range = ms.get_lab_value_range("glucose")
        assert glucose_range is not None

    def test_validate_vital_sign(self):
        """Test vital sign validation."""
        ms = MedicalStandards()

        # Valid blood pressure
        result = ms.validate_vital_sign("blood_pressure_systolic", 120)
        assert result.is_valid is True

        # Invalid blood pressure (too high)
        result = ms.validate_vital_sign("blood_pressure_systolic", 250)
        assert result.is_valid is False

    def test_age_specific_ranges(self):
        """Test age-specific reference ranges."""
        ms = MedicalStandards()

        # Pediatric ranges should differ from adult
        pediatric_hr = ms.get_vital_signs_range("heart_rate", age_group="pediatric")
        adult_hr = ms.get_vital_signs_range("heart_rate", age_group="adult")

        assert pediatric_hr is not None
        assert adult_hr is not None


@pytest.mark.unit
class TestEvidenceBase:
    """Test suite for EvidenceBase."""

    def test_evidence_base_initialization(self):
        """Test evidence base can be initialized."""
        eb = EvidenceBase()
        assert isinstance(eb, EvidenceBase)

    def test_get_strategy_for_missing_data(self):
        """Test getting strategies for missing data."""
        eb = EvidenceBase()

        strategies = eb.get_strategies("missing_data")
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_get_strategy_for_outliers(self):
        """Test getting strategies for outliers."""
        eb = EvidenceBase()

        strategies = eb.get_strategies("outliers")
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_strategies_have_evidence_level(self):
        """Test strategies include evidence level."""
        eb = EvidenceBase()

        strategies = eb.get_strategies("missing_data")
        for strategy in strategies:
            assert hasattr(strategy, "evidence_level")
            assert strategy.evidence_level in [
                "systematic_review",
                "randomized_trial",
                "cohort_study",
                "case_control",
                "best_practice",
                "expert_opinion",
            ]

    def test_get_best_strategy(self):
        """Test getting best strategy (highest evidence)."""
        eb = EvidenceBase()

        best = eb.get_best_strategy("missing_data")
        assert best is not None

        # Should have highest evidence level
        all_strategies = eb.get_strategies("missing_data")
        assert best.evidence_level <= min(s.evidence_level for s in all_strategies)

    def test_strategies_have_citations(self):
        """Test strategies include citations."""
        eb = EvidenceBase()

        strategies = eb.get_strategies("missing_data")
        for strategy in strategies:
            if hasattr(strategy, "citations"):
                assert isinstance(strategy.citations, list)
