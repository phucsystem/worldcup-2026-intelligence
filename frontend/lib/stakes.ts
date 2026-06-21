// Pure helpers mapping brief `intelligence` into the props the home-page
// stake widgets consume. Both degrade to empty when intelligence is absent.
import type { GroupScenario, Intelligence } from "@/lib/api";

/** Map upcoming `fixture_id` → its LLM-written stake clause. */
export function stakesByFixtureId(
  intelligence: Intelligence | null | undefined,
): Map<number, string> {
  const map = new Map<number, string>();
  for (const s of intelligence?.fixture_stakes ?? []) {
    if (typeof s.fixture_id === "number" && s.stake_text) {
      map.set(s.fixture_id, s.stake_text);
    }
  }
  return map;
}

/**
 * Group scenarios renderable as stake cards: only those carrying BOTH an LLM
 * narrative line and deterministic per-team rows (unmatched/hallucinated groups
 * are dropped upstream, but guard here too).
 */
export function scenariosForDisplay(
  intelligence: Intelligence | null | undefined,
): GroupScenario[] {
  return (intelligence?.group_scenarios ?? []).filter(
    (g) => !!g.line && Array.isArray(g.rows) && g.rows.length > 0,
  );
}
