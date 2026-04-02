/**
 * @file knowledge/knowledge.controller.ts
 * @description REST controller for the knowledge-base endpoints.
 *
 * Surfaces medical standards, evidence entries, and validation rules from
 * the `@bio-clean/core` knowledge base to API consumers.
 */

import { Controller, Get, Query } from '@nestjs/common';
import {
  MedicalStandards,
  EvidenceBase,
  type KnowledgeEntry,
} from '@bio-clean/core';

/** Slim representation of a single knowledge entry for API responses. */
export interface KnowledgeEntryDto {
  id: string;
  category: string;
  topic: string;
  statement: string;
  rationale: string;
  confidence: string;
  evidence_level: string;
  tags: string[];
}

/**
 * Exposes the knowledge base at `/knowledge/*`.
 */
@Controller('knowledge')
export class KnowledgeController {
  private readonly medicalStandards = new MedicalStandards();
  private readonly evidenceBase = new EvidenceBase();

  /**
   * Return all medical standards / reference ranges.
   *
   * ### Optional query parameters
   * - `tags` – comma-separated list; only entries matching at least one tag
   *   are returned (e.g. `?tags=vital_signs,blood_pressure`).
   * - `category` – filter by category string.
   *
   * @returns An array of {@link KnowledgeEntryDto}.
   */
  @Get('standards')
  getStandards(
    @Query('tags') tagsParam?: string,
    @Query('category') category?: string,
  ): KnowledgeEntryDto[] {
    const tags = tagsParam
      ? tagsParam.split(',').map((t) => t.trim()).filter(Boolean)
      : undefined;

    const raw: KnowledgeEntry[] = tags?.length
      ? this.medicalStandards.search({ tags, category })
      : this.medicalStandards.search({ category });

    return raw.map(this.toDto);
  }

  /**
   * Return evidence-base entries for data cleaning strategies.
   *
   * ### Optional query parameters
   * - `category` – filter by category (e.g. `missing_data`, `outlier_detection`).
   * - `tags` – comma-separated tag filter.
   *
   * @returns An array of {@link KnowledgeEntryDto}.
   */
  @Get('evidence')
  getEvidence(
    @Query('category') category?: string,
    @Query('tags') tagsParam?: string,
  ): KnowledgeEntryDto[] {
    const tags = tagsParam
      ? tagsParam.split(',').map((t) => t.trim()).filter(Boolean)
      : undefined;

    const raw: KnowledgeEntry[] = this.evidenceBase.search({ category, tags });

    return raw.map(this.toDto);
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private readonly toDto = (entry: KnowledgeEntry): KnowledgeEntryDto => ({
    id: entry.id,
    category: entry.category,
    topic: entry.topic,
    statement: entry.statement,
    rationale: entry.rationale,
    confidence: entry.confidence,
    evidence_level: entry.evidenceLevel,
    tags: entry.tags,
  });
}
