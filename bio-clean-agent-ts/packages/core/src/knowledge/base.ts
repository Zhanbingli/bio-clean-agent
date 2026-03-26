/**
 * Base knowledge structures and interfaces.
 *
 * Provides typed foundations for domain knowledge repositories including
 * evidence levels, confidence tiers, citations, and abstract base class
 * for all knowledge implementations.
 */

// ============================================================
// ENUMS
// ============================================================

/**
 * Evidence quality levels based on the research hierarchy pyramid.
 * Higher entries represent stronger, more reliable evidence.
 */
export enum EvidenceLevel {
  /** Highest quality: synthesises multiple randomized trials */
  SYSTEMATIC_REVIEW = "systematic_review",
  /** Individual randomized controlled trial */
  RANDOMIZED_TRIAL = "randomized_trial",
  /** Prospective or retrospective observational study */
  COHORT_STUDY = "cohort_study",
  /** Retrospective comparison of cases vs controls */
  CASE_CONTROL = "case_control",
  /** Consensus from domain specialists */
  EXPERT_OPINION = "expert_opinion",
  /** Widely-accepted industry or regulatory standard */
  BEST_PRACTICE = "best_practice",
}

/**
 * Confidence in a recommendation.
 * Reflects the strength of supporting evidence and degree of clinical consensus.
 */
export enum ConfidenceLevel {
  /** Strong evidence, widely accepted */
  HIGH = "high",
  /** Good evidence, some debate */
  MEDIUM = "medium",
  /** Limited evidence, use with caution */
  LOW = "low",
}

// ============================================================
// INTERFACES
// ============================================================

/**
 * A scientific citation supporting a knowledge entry.
 */
export interface Citation {
  /** Journal, guideline body, or regulatory standard issuing the source */
  source: string;
  /** Full title of the referenced publication or document */
  title: string;
  /** Year of publication */
  year?: number;
  /** Digital Object Identifier */
  doi?: string;
  /** Publicly accessible URL */
  url?: string;
}

/**
 * A single piece of scientific or medical knowledge.
 */
export interface KnowledgeEntry {
  /** Unique identifier for this entry */
  id: string;
  /** Broad domain grouping, e.g. "vital_signs", "lab_values", "data_cleaning" */
  category: string;
  /** Specific subject within the category, e.g. "blood_pressure_normal_range" */
  topic: string;

  /** Clear, declarative statement of the knowledge */
  statement: string;
  /** Explanation of why this knowledge is true or recommended */
  rationale: string;

  /** Quality level of supporting evidence */
  evidenceLevel: EvidenceLevel;
  /** Confidence in the recommendation */
  confidence: ConfidenceLevel;
  /** Peer-reviewed or authoritative sources supporting this entry */
  citations: Citation[];

  /** Preconditions under which this entry applies */
  conditions: string[];
  /** Situations in which this entry must NOT be applied */
  contraindications: string[];

  /** ISO timestamp of when the entry was last reviewed */
  lastUpdated: string;
  /** Free-text labels for cross-cutting search */
  tags: string[];
}

/**
 * Serializable plain-object representation of a KnowledgeEntry.
 * Useful for JSON transport and logging.
 */
export interface KnowledgeEntryDict {
  id: string;
  category: string;
  topic: string;
  statement: string;
  rationale: string;
  evidenceLevel: string;
  confidence: string;
  citations: Citation[];
  conditions: string[];
  contraindications: string[];
  tags: string[];
}

/**
 * Context object passed to {@link KnowledgeBase.getRecommendation} and
 * {@link KnowledgeBase.validateAgainstKnowledge}.
 */
export interface RecommendationContext {
  category?: string;
  tags?: string[];
  [key: string]: unknown;
}

/**
 * Return value of {@link KnowledgeBase.validateAgainstKnowledge}.
 */
export interface ValidationResult {
  valid: boolean;
  issues: string[];
  recommendations: string[];
  evidence: KnowledgeEntry[];
}

/**
 * Options accepted by {@link KnowledgeBase.search}.
 */
export interface SearchOptions {
  category?: string;
  topic?: string;
  tags?: string[];
  minConfidence?: ConfidenceLevel;
}

// ============================================================
// HELPER CONSTANTS
// ============================================================

/**
 * Canonical ordering of {@link ConfidenceLevel} values from highest to lowest.
 * Index 0 is the strongest confidence; used for ranking comparisons.
 */
export const CONFIDENCE_ORDER: ConfidenceLevel[] = [
  ConfidenceLevel.HIGH,
  ConfidenceLevel.MEDIUM,
  ConfidenceLevel.LOW,
];

/**
 * Canonical ordering of {@link EvidenceLevel} values from strongest to weakest.
 */
export const EVIDENCE_ORDER: EvidenceLevel[] = [
  EvidenceLevel.SYSTEMATIC_REVIEW,
  EvidenceLevel.RANDOMIZED_TRIAL,
  EvidenceLevel.COHORT_STUDY,
  EvidenceLevel.CASE_CONTROL,
  EvidenceLevel.BEST_PRACTICE,
  EvidenceLevel.EXPERT_OPINION,
];

// ============================================================
// FACTORY HELPER
// ============================================================

/**
 * Construct a {@link KnowledgeEntry} with all optional arrays defaulted to
 * empty and `lastUpdated` defaulted to the current ISO timestamp.
 */
export function createEntry(
  params: Omit<KnowledgeEntry, "citations" | "conditions" | "contraindications" | "lastUpdated" | "tags"> &
    Partial<Pick<KnowledgeEntry, "citations" | "conditions" | "contraindications" | "lastUpdated" | "tags">>
): KnowledgeEntry {
  return {
    citations: [],
    conditions: [],
    contraindications: [],
    lastUpdated: new Date().toISOString(),
    tags: [],
    ...params,
  };
}

/**
 * Serialize a {@link KnowledgeEntry} to a plain JSON-compatible object.
 */
export function entryToDict(entry: KnowledgeEntry): KnowledgeEntryDict {
  return {
    id: entry.id,
    category: entry.category,
    topic: entry.topic,
    statement: entry.statement,
    rationale: entry.rationale,
    evidenceLevel: entry.evidenceLevel,
    confidence: entry.confidence,
    citations: entry.citations.map((c) => ({ ...c })),
    conditions: [...entry.conditions],
    contraindications: [...entry.contraindications],
    tags: [...entry.tags],
  };
}

// ============================================================
// ABSTRACT BASE CLASS
// ============================================================

/**
 * Abstract base class for domain knowledge repositories.
 *
 * Provides structured, evidence-based knowledge for:
 * - Data validation ranges
 * - Cleaning best practices
 * - Statistical methods
 * - Domain-specific rules
 *
 * Concrete subclasses must implement {@link buildKnowledgeBase} to populate
 * entries via {@link addEntry}.
 */
export abstract class KnowledgeBase {
  /** Internal store of all registered knowledge entries, keyed by entry ID. */
  protected readonly entries: Map<string, KnowledgeEntry> = new Map();

  constructor() {
    this.buildKnowledgeBase();
  }

  /**
   * Populate the knowledge base with domain-specific entries.
   * Called automatically during construction.
   * Subclasses must override this method and call {@link addEntry} for each entry.
   */
  protected abstract buildKnowledgeBase(): void;

  // ----------------------------------------------------------
  // Mutation
  // ----------------------------------------------------------

  /**
   * Register a knowledge entry.
   * Overwrites any existing entry with the same ID.
   */
  addEntry(entry: KnowledgeEntry): void {
    this.entries.set(entry.id, entry);
  }

  // ----------------------------------------------------------
  // Retrieval
  // ----------------------------------------------------------

  /**
   * Retrieve a specific knowledge entry by its unique ID.
   * Returns `undefined` if not found.
   */
  getEntry(entryId: string): KnowledgeEntry | undefined {
    return this.entries.get(entryId);
  }

  /**
   * Search the knowledge base with optional filters.
   *
   * All supplied filters are applied conjunctively (AND logic):
   * - `category` — exact match on `entry.category`
   * - `topic` — case-insensitive substring match on `entry.topic`
   * - `tags` — entry must contain at least one of the supplied tags
   * - `minConfidence` — entry confidence must be at least as strong as the supplied level
   */
  search(options: SearchOptions = {}): KnowledgeEntry[] {
    const { category, topic, tags, minConfidence } = options;
    let results = Array.from(this.entries.values());

    if (category !== undefined) {
      results = results.filter((e) => e.category === category);
    }

    if (topic !== undefined) {
      const lowerTopic = topic.toLowerCase();
      results = results.filter((e) => e.topic.toLowerCase().includes(lowerTopic));
    }

    if (tags !== undefined && tags.length > 0) {
      results = results.filter((e) => tags.some((tag) => e.tags.includes(tag)));
    }

    if (minConfidence !== undefined) {
      const minIdx = CONFIDENCE_ORDER.indexOf(minConfidence);
      results = results.filter(
        (e) => CONFIDENCE_ORDER.indexOf(e.confidence) <= minIdx
      );
    }

    return results;
  }

  /**
   * Get the best recommendation for a given context.
   *
   * Searches by `category` and `tags` from the context, filters to entries
   * with at least MEDIUM confidence, then returns the entry with the highest
   * confidence (ties broken by insertion order).
   *
   * @returns The most relevant high-confidence entry, or `undefined` if none found.
   */
  getRecommendation(context: RecommendationContext): KnowledgeEntry | undefined {
    const { category, tags = [] } = context;

    const candidates = this.search({
      category,
      tags: tags.length > 0 ? tags : undefined,
      minConfidence: ConfidenceLevel.MEDIUM,
    });

    if (candidates.length === 0) {
      return undefined;
    }

    return candidates.slice().sort(
      (a, b) =>
        CONFIDENCE_ORDER.indexOf(a.confidence) -
        CONFIDENCE_ORDER.indexOf(b.confidence)
    )[0];
  }

  /**
   * Validate a value against relevant entries in the knowledge base.
   *
   * Searches entries tagged with `field`, then checks each matching entry's
   * contraindications against the supplied context.
   *
   * @param field   The data field being validated (used as a tag search term).
   * @param value   The value to validate (currently used for extensibility).
   * @param context Optional context map checked against `conditions` and `contraindications`.
   */
  validateAgainstKnowledge(
    field: string,
    value: unknown,
    context?: Record<string, unknown>
  ): ValidationResult {
    const result: ValidationResult = {
      valid: true,
      issues: [],
      recommendations: [],
      evidence: [],
    };

    const relevant = this.search({ tags: [field] });

    for (const entry of relevant) {
      // Check conditions are met
      if (entry.conditions.length > 0 && context) {
        const conditionsMet = entry.conditions.every((cond) => Boolean(context[cond]));
        if (!conditionsMet) {
          continue;
        }
      }

      // Check contraindications
      if (entry.contraindications.length > 0 && context) {
        const hasContraindication = entry.contraindications.some((contra) =>
          Boolean(context[contra])
        );
        if (hasContraindication) {
          result.valid = false;
          result.issues.push(`Contraindication: ${entry.statement}`);
          result.evidence.push(entry);
        }
      }
    }

    // Suppress unused-variable lint for `value` — available for subclass override
    void value;

    return result;
  }
}
