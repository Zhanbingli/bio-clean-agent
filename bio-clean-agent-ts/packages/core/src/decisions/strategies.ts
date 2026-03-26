/**
 * @file decisions/strategies.ts
 * @description Concrete {@link DecisionStrategy} implementations.
 *
 * Available strategies:
 * - {@link AutoApproveStrategy}   – immediately selects the default or first option
 * - {@link NotifyAndWaitStrategy} – stores the decision as pending, returns default
 *   while waiting; supports programmatic resolution via {@link NotifyAndWaitStrategy.resolve}
 * - {@link LLMAssistedStrategy}   – delegates analysis to a planner function,
 *   optionally auto-approving the recommendation
 *
 * Note: `InteractiveStrategy` (terminal-based) is intentionally omitted here;
 * it belongs in the CLI package.
 *
 * Ported from Python `decisions/strategies.py`.
 */

import type {
  DecisionContext,
  DecisionOption,
  DecisionStrategy,
} from "./manager.js";

// ---------------------------------------------------------------------------
// AutoApproveStrategy
// ---------------------------------------------------------------------------

/**
 * Strategy that resolves every decision automatically without human input.
 *
 * Selection priority:
 * 1. The option whose `id` matches {@link DecisionContext.defaultOption}.
 * 2. The first option in {@link DecisionContext.options}.
 * 3. A synthetic fallback option when the options array is empty.
 *
 * @example
 * ```ts
 * const manager = new DecisionManager(new AutoApproveStrategy());
 * ```
 */
export class AutoApproveStrategy implements DecisionStrategy {
  decide(context: DecisionContext): DecisionOption {
    if (context.options.length === 0) {
      // Synthetic fallback – should not normally occur in a well-formed context.
      return { id: "auto_approved", label: "Auto-approved (no options provided)" };
    }

    if (context.defaultOption !== undefined) {
      const defaultOpt = context.options.find(
        (o) => o.id === context.defaultOption
      );
      if (defaultOpt !== undefined) {
        return defaultOpt;
      }
    }

    // Fall back to the first available option.
    return context.options[0]!;
  }
}

// ---------------------------------------------------------------------------
// NotifyAndWaitStrategy
// ---------------------------------------------------------------------------

/**
 * A pending decision record stored by {@link NotifyAndWaitStrategy}.
 */
export interface PendingDecision {
  /** Unique identifier for this pending decision. */
  decisionId: string;
  /** The full decision context. */
  context: DecisionContext;
  /** ISO 8601 timestamp when the decision was registered. */
  createdAt: string;
  /** Resolved choice, set when {@link NotifyAndWaitStrategy.resolve} is called. */
  resolvedChoice?: DecisionOption;
}

/**
 * Strategy that registers decisions as pending and returns the default option
 * while waiting for an external resolver to call {@link resolve}.
 *
 * This strategy is designed for asynchronous workflows where a notification
 * is sent (e.g. via webhook or message queue) and the pipeline pauses until
 * an external actor resolves the decision.
 *
 * @remarks
 * In the current synchronous pipeline model the strategy cannot truly block.
 * It returns the default (or first) option immediately so the pipeline can
 * continue; the resolved choice stored via {@link resolve} can be inspected
 * after the fact for audit purposes.
 *
 * @example
 * ```ts
 * const strategy = new NotifyAndWaitStrategy(60);
 * const manager  = new DecisionManager(strategy);
 *
 * // Later, from a notification handler:
 * const pending = strategy.getPending("my-decision-id");
 * if (pending) strategy.resolve("my-decision-id", pending.context.options[0]!);
 * ```
 */
export class NotifyAndWaitStrategy implements DecisionStrategy {
  /** How long (seconds) to wait for resolution before timing out. */
  readonly timeoutSeconds: number;

  private readonly _pendingDecisions: Map<string, PendingDecision> = new Map();

  constructor(timeoutSeconds: number = 300) {
    this.timeoutSeconds = timeoutSeconds;
  }

  decide(context: DecisionContext): DecisionOption {
    const decisionId = crypto.randomUUID();

    const pending: PendingDecision = {
      decisionId,
      context,
      createdAt: new Date().toISOString(),
    };

    this._pendingDecisions.set(decisionId, pending);

    // Return the default (or first) option as the provisional choice.
    // The caller may later inspect or override this via resolve().
    const provisional = this._selectDefault(context);
    return provisional;
  }

  /**
   * Resolve a pending decision with an explicit choice.
   *
   * @param decisionId - The UUID assigned when the decision was registered.
   * @param choice     - The chosen {@link DecisionOption}.
   * @returns `true` when the decision was found and resolved; `false` otherwise.
   */
  resolve(decisionId: string, choice: DecisionOption): boolean {
    const pending = this._pendingDecisions.get(decisionId);
    if (pending === undefined) {
      return false;
    }

    pending.resolvedChoice = choice;
    return true;
  }

  /**
   * Retrieve a pending decision by its ID.
   *
   * @param decisionId - The UUID of the pending decision.
   * @returns The {@link PendingDecision}, or `undefined` if not found.
   */
  getPending(decisionId: string): PendingDecision | undefined {
    return this._pendingDecisions.get(decisionId);
  }

  /**
   * Return all currently pending (unresolved) decisions.
   */
  listPending(): PendingDecision[] {
    return Array.from(this._pendingDecisions.values()).filter(
      (d) => d.resolvedChoice === undefined
    );
  }

  /**
   * Clear all stored pending decisions (resolved and unresolved).
   */
  clearAll(): void {
    this._pendingDecisions.clear();
  }

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  private _selectDefault(context: DecisionContext): DecisionOption {
    if (context.options.length === 0) {
      return { id: "pending", label: "Pending human decision" };
    }

    if (context.defaultOption !== undefined) {
      const found = context.options.find(
        (o) => o.id === context.defaultOption
      );
      if (found !== undefined) {
        return found;
      }
    }

    return context.options[0]!;
  }
}

// ---------------------------------------------------------------------------
// LLMAssistedStrategy
// ---------------------------------------------------------------------------

/**
 * Signature of the planner function injected into {@link LLMAssistedStrategy}.
 *
 * @param context - The decision context to analyse.
 * @returns The recommended {@link DecisionOption}, or `undefined` if the
 *   planner cannot produce a recommendation.
 */
export type PlannerFunction = (
  context: DecisionContext
) => DecisionOption | undefined;

/**
 * Strategy that delegates decision analysis to an LLM planner function.
 *
 * The planner receives the full {@link DecisionContext} and returns its
 * recommendation.  Depending on the {@link autoApprove} flag the strategy
 * either returns the recommendation immediately or waits for additional
 * confirmation (modelled here as returning the recommendation with a flag).
 *
 * When the planner returns `undefined` (cannot decide) the strategy falls
 * back to the default or first option, mirroring {@link AutoApproveStrategy}.
 *
 * @example
 * ```ts
 * const strategy = new LLMAssistedStrategy(
 *   async (ctx) => {
 *     const result = await callLLM(ctx.question, ctx.options);
 *     return result.recommendedOption;
 *   },
 *   true  // auto-approve the recommendation
 * );
 * const manager = new DecisionManager(strategy);
 * ```
 */
export class LLMAssistedStrategy implements DecisionStrategy {
  /**
   * When `true`, the LLM recommendation is applied without additional
   * confirmation.  When `false`, the recommendation is returned but
   * the caller is expected to surface it for human review.
   */
  readonly autoApprove: boolean;

  private readonly _planner: PlannerFunction;

  constructor(planner: PlannerFunction, autoApprove: boolean = false) {
    this._planner = planner;
    this.autoApprove = autoApprove;
  }

  decide(context: DecisionContext): DecisionOption {
    // Ask the planner for a recommendation.
    const recommendation = this._tryPlanner(context);

    if (recommendation !== undefined) {
      // If auto-approve is enabled, use the recommendation directly.
      // Otherwise, annotate it so callers know it is a recommendation.
      if (this.autoApprove) {
        return recommendation;
      }

      // Return the recommendation with an extra metadata flag to signal
      // that it still awaits human confirmation.
      return {
        ...recommendation,
        llm_recommended: true,
        requires_confirmation: true,
      };
    }

    // Fallback when the planner cannot produce a recommendation.
    return this._selectDefault(context);
  }

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  private _tryPlanner(
    context: DecisionContext
  ): DecisionOption | undefined {
    try {
      return this._planner(context);
    } catch {
      // Planner errors must not crash the pipeline.
      return undefined;
    }
  }

  private _selectDefault(context: DecisionContext): DecisionOption {
    if (context.options.length === 0) {
      return { id: "llm_fallback", label: "LLM fallback (no options provided)" };
    }

    if (context.defaultOption !== undefined) {
      const found = context.options.find(
        (o) => o.id === context.defaultOption
      );
      if (found !== undefined) {
        return found;
      }
    }

    return context.options[0]!;
  }
}
