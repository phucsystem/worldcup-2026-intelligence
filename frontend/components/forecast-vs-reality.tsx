import type { Forecast } from "@/lib/match";

const HOME_COLOR = "var(--accent-bright)";
const DRAW_COLOR = "var(--status-draw)";
const AWAY_COLOR = "#FF6B7A";

type Side = "home" | "draw" | "away";
type Tone = "ontrack" | "tightening" | "upset";

interface VerdictResult {
  label: string;
  tone: Tone;
  text: string;
}

interface Props {
  forecast: Forecast;
  homeScore: number | null;
  awayScore: number | null;
  elapsed: number | null;
  homeTeam: string;
  awayTeam: string;
}

function forecastPick(forecast: Forecast): { side: Side; pct: number } {
  const { home_pct, draw_pct, away_pct } = forecast;
  if (home_pct >= draw_pct && home_pct >= away_pct) return { side: "home", pct: home_pct };
  if (away_pct >= draw_pct) return { side: "away", pct: away_pct };
  return { side: "draw", pct: draw_pct };
}

function actualState(homeScore: number | null, awayScore: number | null): Side {
  const h = homeScore ?? 0;
  const a = awayScore ?? 0;
  if (h > a) return "home";
  if (a > h) return "away";
  return "draw";
}

function verdict(pick: Side, state: Side, elapsed: number | null): VerdictResult {
  const late = (elapsed ?? 0) >= 75;
  const timeTag = late ? " — with time running out" : "";

  if (pick === "draw") {
    if (state === "draw") {
      return { label: "On track", tone: "ontrack", text: "Match is level, as the draw forecast expected." };
    }
    return { label: "Breaking the forecast", tone: "upset", text: `A draw was forecast but a side is now leading${timeTag}.` };
  }

  if (pick === state) {
    const label = late ? "Holding on" : "On track";
    return { label, tone: "ontrack", text: `The favoured side is leading${timeTag}.` };
  }

  if (state === "draw") {
    return { label: "Tighter than forecast", tone: "tightening", text: `The favoured side is level${timeTag}.` };
  }

  return { label: "Upset in progress", tone: "upset", text: `The favoured side is trailing${timeTag}.` };
}

const TONE_STYLES: Record<Tone, { bg: string; color: string; border: string }> = {
  ontrack:    { bg: "rgba(43, 211, 126, 0.12)",  color: "var(--status-live)", border: "var(--status-live)" },
  tightening: { bg: "rgba(244, 183, 64, 0.12)",  color: "var(--status-draw)", border: "var(--status-draw)" },
  upset:      { bg: "rgba(255, 90, 90, 0.12)",   color: "var(--status-loss)", border: "var(--status-loss)" },
};

const TONE_ICONS: Record<Tone, string> = { ontrack: "✅", tightening: "⚖️", upset: "🚨" };

export default function ForecastVsReality({ forecast, homeScore, awayScore, elapsed, homeTeam, awayTeam }: Props) {
  const pick = forecastPick(forecast);
  const state = actualState(homeScore, awayScore);
  const v = verdict(pick.side, state, elapsed);
  const tone = TONE_STYLES[v.tone];

  const pickLabel =
    pick.side === "home" ? `${homeTeam} to win` :
    pick.side === "away" ? `${awayTeam} to win` :
    "Draw";

  const leaderLabel =
    state === "home" ? <><b>{homeTeam}</b> leading</> :
    state === "away" ? <><b>{awayTeam}</b> leading</> :
    <>Level — <b>no leader</b></>;

  const scoreline = `${homeTeam} ${homeScore ?? 0} – ${awayScore ?? 0} ${awayTeam}`;

  const { home_pct, draw_pct, away_pct } = forecast;

  return (
    <section className="forecast-card fvr-card" aria-label="Forecast vs Reality comparison">
      <div className="fvr-grid">
        {/* FORECAST column */}
        <div className="fvr-col">
          <div className="fvr-col-label">Forecast — pre-kickoff</div>
          <div className="fvr-pick">
            {pickLabel}{" "}
            <span style={{ color: "var(--accent-bright)" }}>{pick.pct}%</span>
          </div>
          <div className="fvr-pick-sub">Model call before first whistle</div>

          {/* 1X2 split bar */}
          <div className="fvr-split-bar" role="img" aria-label={`${homeTeam} ${home_pct}%, Draw ${draw_pct}%, ${awayTeam} ${away_pct}%`}>
            <div className="fvr-seg" style={{ width: `${home_pct}%`, background: HOME_COLOR }} />
            <div className="fvr-seg" style={{ width: `${draw_pct}%`, background: DRAW_COLOR }} />
            <div className="fvr-seg" style={{ width: `${away_pct}%`, background: AWAY_COLOR }} />
          </div>
          <div className="fvr-split-legend">
            <span><span className="fvr-swatch" style={{ background: HOME_COLOR }} />{homeTeam} {home_pct}%</span>
            <span><span className="fvr-swatch" style={{ background: DRAW_COLOR }} />Draw {draw_pct}%</span>
            <span><span className="fvr-swatch" style={{ background: AWAY_COLOR }} />{awayTeam} {away_pct}%</span>
          </div>
        </div>

        <div className="fvr-divider" aria-hidden="true" />

        {/* REALITY column */}
        <div className="fvr-col">
          <div className="fvr-col-label">
            <span className="fvr-live-pill">
              <span className="fvr-live-dot" />
              LIVE
            </span>
            {elapsed != null ? <span>{elapsed}&prime;</span> : null}
          </div>
          <div className="fvr-score-line">{scoreline}</div>
          <div className="fvr-leader">{leaderLabel}</div>
        </div>
      </div>

      {/* VERDICT bar */}
      <div
        className="fvr-verdict"
        style={{ background: tone.bg, color: tone.color, borderLeftColor: tone.border }}
        aria-live="polite"
      >
        <span className="fvr-verdict-icon" aria-hidden="true">{TONE_ICONS[v.tone]}</span>
        <span>
          <strong>{v.label}</strong>{" "}
          <span style={{ fontWeight: 500, opacity: 0.92 }}>{v.text}</span>
        </span>
      </div>
    </section>
  );
}
