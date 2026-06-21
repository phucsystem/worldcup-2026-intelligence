import { describe, it, expect } from "vitest";
import { liveMinute } from "./live";

const T0 = Date.UTC(2026, 5, 19, 20, 0, 0); // fixed "updated_at"
const iso = new Date(T0).toISOString();

describe("liveMinute", () => {
  it("does not bump within the first minute since sync", () => {
    const r = liveMinute(67, iso, "2H", T0 + 40_000);
    expect(r.minute).toBe(67);
    expect(r.frozen).toBe(false);
    expect(r.label).toBe("2nd half");
  });

  it("bumps by elapsed whole minutes since sync", () => {
    expect(liveMinute(67, iso, "2H", T0 + 60_000).minute).toBe(68);
    expect(liveMinute(67, iso, "2H", T0 + 150_000).minute).toBe(69);
  });

  it("freezes and relabels at half-time", () => {
    const r = liveMinute(45, iso, "HT", T0 + 300_000);
    expect(r.frozen).toBe(true);
    expect(r.label).toBe("Half-time");
    expect(r.minute).toBe(45); // no advance while frozen
  });

  it("lets stoppage time tick past the regulation boundary", () => {
    // 2H, 89' + 3 min → 92' (stoppage), not stuck at 90'
    expect(liveMinute(89, iso, "2H", T0 + 180_000).minute).toBe(92);
  });

  it("caps a runaway interpolation at the per-half ceiling", () => {
    // a wedged poll (60 min gap) must not show 149'
    expect(liveMinute(89, iso, "2H", T0 + 3_600_000).minute).toBe(100);
    expect(liveMinute(44, iso, "1H", T0 + 3_600_000).minute).toBe(50);
  });

  it("returns null minute when elapsed is unknown", () => {
    const r = liveMinute(null, iso, "1H", T0 + 60_000);
    expect(r.minute).toBeNull();
    expect(r.label).toBe("1st half");
  });

  it("does not interpolate without an updated_at anchor", () => {
    expect(liveMinute(50, null, "2H", T0 + 600_000).minute).toBe(50);
  });

  it("freezes on break and penalties", () => {
    expect(liveMinute(90, iso, "BT", T0).label).toBe("Break");
    expect(liveMinute(90, iso, "BT", T0).frozen).toBe(true);
    expect(liveMinute(90, iso, "P", T0).label).toBe("Penalties");
  });
});
