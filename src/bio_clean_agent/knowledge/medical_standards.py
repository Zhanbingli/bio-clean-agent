"""Medical standards and reference ranges based on clinical guidelines."""

from .base import (
    Citation,
    ConfidenceLevel,
    EvidenceLevel,
    KnowledgeBase,
    KnowledgeEntry,
)


class MedicalStandards(KnowledgeBase):
    """
    Evidence-based medical standards for data validation.

    Sources:
    - WHO guidelines
    - American Heart Association (AHA)
    - Clinical Laboratory Standards Institute (CLSI)
    - FDA guidance documents
    """

    def _build_knowledge_base(self) -> None:
        """Build medical standards knowledge base."""

        # ========================================
        # VITAL SIGNS - Adult Reference Ranges
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="vs_blood_pressure_normal",
                category="vital_signs",
                topic="blood_pressure_normal_range",
                statement="Normal adult systolic blood pressure: 90-120 mmHg, diastolic: 60-80 mmHg",
                rationale="Based on AHA/ACC guidelines. Values outside this range may indicate hypertension, hypotension, or measurement error.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Heart Association",
                        title="2017 ACC/AHA Guideline for High Blood Pressure in Adults",
                        year=2017,
                        url="https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065",
                    )
                ],
                conditions=["age >= 18", "at_rest"],
                tags=["blood_pressure", "systolic_bp", "diastolic_bp", "vital_signs"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="vs_heart_rate_normal",
                category="vital_signs",
                topic="heart_rate_normal_range",
                statement="Normal adult resting heart rate: 60-100 bpm",
                rationale="Standard clinical reference range. Athletes may have lower rates (40-60 bpm). Values >100 indicate tachycardia, <60 bradycardia.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Heart Association",
                        title="Target Heart Rates Chart",
                        year=2021,
                        url="https://www.heart.org/en/healthy-living/fitness/fitness-basics/target-heart-rates",
                    )
                ],
                conditions=["age >= 18", "at_rest"],
                tags=["heart_rate", "pulse", "vital_signs"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="vs_temperature_normal",
                category="vital_signs",
                topic="body_temperature_normal",
                statement="Normal adult body temperature: 36.1-37.2°C (97.0-99.0°F)",
                rationale="Core body temperature reference range. Varies by measurement site (oral, rectal, axillary). Fever defined as >38.0°C (100.4°F).",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="WHO",
                        title="Temperature Measurement in Clinical Practice",
                        year=2018,
                    )
                ],
                tags=["temperature", "fever", "vital_signs"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="vs_respiratory_rate_normal",
                category="vital_signs",
                topic="respiratory_rate_normal",
                statement="Normal adult respiratory rate: 12-20 breaths/minute",
                rationale="Standard clinical reference. <12 indicates bradypnea, >20 tachypnea.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Thoracic Society",
                        title="Guidelines for Respiratory Rate Assessment",
                        year=2019,
                    )
                ],
                conditions=["age >= 18", "at_rest"],
                tags=["respiratory_rate", "breathing", "vital_signs"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="vs_oxygen_saturation_normal",
                category="vital_signs",
                topic="oxygen_saturation_normal",
                statement="Normal oxygen saturation (SpO2): 95-100%",
                rationale="Pulse oximetry reference range. Values <95% may indicate hypoxemia. <90% requires clinical intervention.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="British Thoracic Society",
                        title="Emergency Oxygen Guideline",
                        year=2017,
                    )
                ],
                tags=["oxygen_saturation", "spo2", "vital_signs"],
            )
        )

        # ========================================
        # ANTHROPOMETRIC MEASUREMENTS
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="anthro_weight_adult",
                category="anthropometry",
                topic="adult_weight_range",
                statement="Typical adult weight: 40-200 kg (88-440 lbs)",
                rationale="Practical range for data validation. Extreme values likely indicate measurement or data entry errors.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="CDC",
                        title="Anthropometric Reference Data",
                        year=2020,
                    )
                ],
                conditions=["age >= 18"],
                tags=["weight", "anthropometry"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="anthro_height_adult",
                category="anthropometry",
                topic="adult_height_range",
                statement="Typical adult height: 140-210 cm (4'7\"-6'11\")",
                rationale="Covers 99.9% of global adult population. Extreme outliers suggest data errors.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="WHO",
                        title="Global Height Distribution Data",
                        year=2019,
                    )
                ],
                conditions=["age >= 18"],
                tags=["height", "anthropometry"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="anthro_bmi_categories",
                category="anthropometry",
                topic="bmi_classification",
                statement="BMI categories: Underweight <18.5, Normal 18.5-24.9, Overweight 25-29.9, Obese ≥30",
                rationale="WHO international classification for adults. Used for health risk assessment.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="WHO",
                        title="BMI Classification",
                        year=2000,
                        url="https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
                    )
                ],
                conditions=["age >= 18"],
                contraindications=["pregnancy", "athlete", "bodybuilder"],
                tags=["bmi", "obesity", "anthropometry"],
            )
        )

        # ========================================
        # LAB VALUES - Common Tests
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="lab_glucose_fasting",
                category="laboratory",
                topic="fasting_glucose_normal",
                statement="Normal fasting glucose: 70-100 mg/dL (3.9-5.6 mmol/L)",
                rationale="American Diabetes Association criteria. 100-125 mg/dL indicates prediabetes, ≥126 mg/dL diabetes.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Diabetes Association",
                        title="Standards of Medical Care in Diabetes",
                        year=2023,
                        doi="10.2337/dc23-S002",
                    )
                ],
                conditions=["fasting >= 8_hours"],
                tags=["glucose", "diabetes", "laboratory"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="lab_hba1c_normal",
                category="laboratory",
                topic="hba1c_normal_range",
                statement="Normal HbA1c: <5.7%",
                rationale="Reflects average blood glucose over 2-3 months. 5.7-6.4% indicates prediabetes, ≥6.5% diabetes.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Diabetes Association",
                        title="Classification and Diagnosis of Diabetes",
                        year=2023,
                    )
                ],
                tags=["hba1c", "diabetes", "laboratory"],
            )
        )

        # ========================================
        # AGE-SPECIFIC CONSIDERATIONS
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="age_pediatric_ranges",
                category="age_specific",
                topic="pediatric_vital_signs",
                statement="Pediatric vital signs differ significantly from adults and vary by age",
                rationale="Children have higher heart rates, respiratory rates, and different BP ranges. Age-specific references must be used.",
                evidence_level=EvidenceLevel.SYSTEMATIC_REVIEW,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Academy of Pediatrics",
                        title="Pediatric Vital Sign Normal Ranges",
                        year=2020,
                    )
                ],
                conditions=["age < 18"],
                tags=["pediatric", "age_specific", "vital_signs"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="age_geriatric_considerations",
                category="age_specific",
                topic="geriatric_considerations",
                statement="Geriatric patients (≥65 years) may have different normal ranges and higher measurement variability",
                rationale="Physiological changes with aging affect vital signs and lab values. More lenient BP targets for elderly.",
                evidence_level=EvidenceLevel.COHORT_STUDY,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="American Geriatrics Society",
                        title="Clinical Guidelines for Older Adults",
                        year=2021,
                    )
                ],
                conditions=["age >= 65"],
                tags=["geriatric", "elderly", "age_specific"],
            )
        )

        # ========================================
        # DATA QUALITY - Statistical Considerations
        # ========================================

        self.add_entry(
            KnowledgeEntry(
                id="stat_outlier_detection_iqr",
                category="statistics",
                topic="outlier_detection_iqr_method",
                statement="IQR method: Outliers defined as values < Q1-1.5*IQR or > Q3+1.5*IQR",
                rationale="Robust non-parametric method for outlier detection. Less sensitive to extreme values than z-score.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.HIGH,
                citations=[
                    Citation(
                        source="Tukey, J.W.",
                        title="Exploratory Data Analysis",
                        year=1977,
                    )
                ],
                tags=["outliers", "statistics", "data_quality"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="stat_missing_data_threshold",
                category="statistics",
                topic="missing_data_deletion_threshold",
                statement="Variables with >20% missing data should be carefully evaluated before deletion",
                rationale="High missingness may indicate systematic issues. Multiple imputation preferred over deletion when possible.",
                evidence_level=EvidenceLevel.EXPERT_OPINION,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="Little & Rubin",
                        title="Statistical Analysis with Missing Data",
                        year=2019,
                    )
                ],
                tags=["missing_data", "statistics", "data_quality"],
            )
        )

        self.add_entry(
            KnowledgeEntry(
                id="clean_duplicate_resolution",
                category="data_cleaning",
                topic="duplicate_record_handling",
                statement="For duplicate records, keep the most complete record or the one with most recent timestamp",
                rationale="Preserves maximum information while removing redundancy. Timestamp priority assumes newer data is more accurate.",
                evidence_level=EvidenceLevel.BEST_PRACTICE,
                confidence=ConfidenceLevel.MEDIUM,
                citations=[
                    Citation(
                        source="FDA",
                        title="Data Integrity and Compliance Guidance",
                        year=2018,
                    )
                ],
                tags=["duplicates", "data_cleaning"],
            )
        )

    def get_reference_range(
        self,
        field: str,
        context: dict = None
    ) -> dict:
        """
        Get reference range for a clinical field.

        Args:
            field: Clinical parameter (e.g., "systolic_bp", "heart_rate")
            context: Patient context (age, conditions, etc.)

        Returns:
            {
                "min": float,
                "max": float,
                "unit": str,
                "confidence": str,
                "source": KnowledgeEntry
            }
        """
        # Search for relevant knowledge
        entries = self.search(tags=[field])

        if not entries:
            return None

        # Filter by context if provided
        if context:
            age = context.get("age")
            if age:
                # Apply age-specific filtering
                if age < 18:
                    entries = [
                        e for e in entries
                        if "pediatric" in e.tags or
                        any(c for c in e.conditions if "age >= 18" not in c)
                    ]
                elif age >= 65:
                    # Prefer geriatric-specific or include general
                    geriatric_entries = [
                        e for e in entries if "geriatric" in e.tags
                    ]
                    if geriatric_entries:
                        entries = geriatric_entries

        if not entries:
            return None

        # Return highest confidence entry
        entry = max(
            entries,
            key=lambda e: [
                ConfidenceLevel.HIGH,
                ConfidenceLevel.MEDIUM,
                ConfidenceLevel.LOW,
            ].index(e.confidence)
        )

        # Parse range from statement (simplified - in production use structured data)
        # For now, return the entry
        return {
            "source": entry,
            "confidence": entry.confidence.value,
            "evidence_level": entry.evidence_level.value,
        }
