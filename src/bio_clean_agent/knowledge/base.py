"""Base knowledge structures and interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceLevel(str, Enum):
    """Evidence quality levels (based on research hierarchy)."""

    SYSTEMATIC_REVIEW = "systematic_review"  # Highest quality
    RANDOMIZED_TRIAL = "randomized_trial"
    COHORT_STUDY = "cohort_study"
    CASE_CONTROL = "case_control"
    EXPERT_OPINION = "expert_opinion"
    BEST_PRACTICE = "best_practice"  # Industry standard


class ConfidenceLevel(str, Enum):
    """Confidence in recommendation."""

    HIGH = "high"  # Strong evidence, widely accepted
    MEDIUM = "medium"  # Good evidence, some debate
    LOW = "low"  # Limited evidence, use with caution


@dataclass
class Citation:
    """Scientific citation for knowledge."""

    source: str  # Journal, guideline, standard
    title: str
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None


@dataclass
class KnowledgeEntry:
    """A single piece of scientific/medical knowledge."""

    id: str
    category: str  # e.g., "vital_signs", "lab_values", "data_cleaning"
    topic: str  # e.g., "blood_pressure_normal_range"

    # Core content
    statement: str  # Clear statement of the knowledge
    rationale: str  # Why this is true/recommended

    # Evidence
    evidence_level: EvidenceLevel
    confidence: ConfidenceLevel
    citations: List[Citation] = field(default_factory=list)

    # Applicability
    conditions: List[str] = field(default_factory=list)  # When this applies
    contraindications: List[str] = field(default_factory=list)  # When NOT to use

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "topic": self.topic,
            "statement": self.statement,
            "rationale": self.rationale,
            "evidence_level": self.evidence_level.value,
            "confidence": self.confidence.value,
            "citations": [
                {
                    "source": c.source,
                    "title": c.title,
                    "year": c.year,
                    "doi": c.doi,
                    "url": c.url,
                }
                for c in self.citations
            ],
            "conditions": self.conditions,
            "contraindications": self.contraindications,
            "tags": self.tags,
        }


class KnowledgeBase:
    """
    Base class for domain knowledge repositories.

    Provides structured, evidence-based knowledge for:
    - Data validation ranges
    - Cleaning best practices
    - Statistical methods
    - Domain-specific rules
    """

    def __init__(self):
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._build_knowledge_base()

    def _build_knowledge_base(self) -> None:
        """
        Build the knowledge base.
        Override in subclasses to add domain-specific knowledge.
        """
        pass

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Add a knowledge entry."""
        self.entries[entry.id] = entry

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific knowledge entry."""
        return self.entries.get(entry_id)

    def search(
        self,
        category: Optional[str] = None,
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_confidence: Optional[ConfidenceLevel] = None,
    ) -> List[KnowledgeEntry]:
        """Search knowledge base."""
        results = list(self.entries.values())

        if category:
            results = [e for e in results if e.category == category]

        if topic:
            results = [e for e in results if topic.lower() in e.topic.lower()]

        if tags:
            results = [
                e for e in results if any(tag in e.tags for tag in tags)
            ]

        if min_confidence:
            confidence_order = [
                ConfidenceLevel.HIGH,
                ConfidenceLevel.MEDIUM,
                ConfidenceLevel.LOW,
            ]
            min_idx = confidence_order.index(min_confidence)
            results = [
                e
                for e in results
                if confidence_order.index(e.confidence) <= min_idx
            ]

        return results

    def get_recommendation(
        self,
        context: Dict[str, Any]
    ) -> Optional[KnowledgeEntry]:
        """
        Get best recommendation for a given context.

        Args:
            context: Situation context (e.g., {"data_type": "vital_signs", "field": "blood_pressure"})

        Returns:
            Most relevant high-confidence knowledge entry
        """
        # Search by category and tags
        category = context.get("category")
        tags = context.get("tags", [])

        candidates = self.search(
            category=category,
            tags=tags,
            min_confidence=ConfidenceLevel.MEDIUM,
        )

        if not candidates:
            return None

        # Return highest confidence entry
        candidates.sort(
            key=lambda e: [
                ConfidenceLevel.HIGH,
                ConfidenceLevel.MEDIUM,
                ConfidenceLevel.LOW,
            ].index(e.confidence)
        )

        return candidates[0]

    def validate_against_knowledge(
        self,
        field: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate a value against knowledge base.

        Returns:
            {
                "valid": bool,
                "issues": List[str],
                "recommendations": List[str],
                "evidence": List[KnowledgeEntry]
            }
        """
        result = {
            "valid": True,
            "issues": [],
            "recommendations": [],
            "evidence": [],
        }

        # Search for relevant knowledge
        relevant = self.search(tags=[field])

        for entry in relevant:
            # Check if conditions are met
            if entry.conditions and context:
                conditions_met = all(
                    context.get(cond) for cond in entry.conditions
                )
                if not conditions_met:
                    continue

            # Check contraindications
            if entry.contraindications and context:
                has_contraindication = any(
                    context.get(contra)
                    for contra in entry.contraindications
                )
                if has_contraindication:
                    result["valid"] = False
                    result["issues"].append(
                        f"Contraindication: {entry.statement}"
                    )
                    result["evidence"].append(entry)

        return result
