// Decorative cinematic key-art for the daily-brief hero (stadium at night with
// floodlight beams, perspective pitch, and celebration confetti). Pure inline
// SVG so it always renders on-brand without any image asset or network fetch.
export default function BriefHeroArt() {
  return (
    <svg viewBox="0 0 1200 480" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bhSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0B2150" />
          <stop offset="55%" stopColor="#0A1B3D" />
          <stop offset="100%" stopColor="#060E22" />
        </linearGradient>
        <radialGradient id="bhGlow" cx="50%" cy="6%" r="70%">
          <stop offset="0%" stopColor="#2D6BF6" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#2D6BF6" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="bhPitch" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#123a2a" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#0a2018" stopOpacity="0.95" />
        </linearGradient>
        <linearGradient id="bhBeam" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#9FC0FF" stopOpacity="0.20" />
          <stop offset="100%" stopColor="#9FC0FF" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="1200" height="480" fill="url(#bhSky)" />
      <rect width="1200" height="480" fill="url(#bhGlow)" />
      <polygon points="120,0 220,0 340,300 60,300" fill="url(#bhBeam)" />
      <polygon points="980,0 1080,0 1140,300 860,300" fill="url(#bhBeam)" />
      <polygon points="520,0 600,0 700,260 470,260" fill="url(#bhBeam)" opacity="0.7" />
      <path d="M0,250 Q600,150 1200,250 L1200,300 Q600,210 0,300 Z" fill="#0c1d40" opacity="0.85" />
      <g fill="#16305c" opacity="0.6">
        <circle cx="150" cy="232" r="2.2" /><circle cx="230" cy="222" r="2.2" /><circle cx="320" cy="212" r="2.2" />
        <circle cx="430" cy="202" r="2.2" /><circle cx="560" cy="194" r="2.2" /><circle cx="690" cy="194" r="2.2" />
        <circle cx="820" cy="202" r="2.2" /><circle cx="930" cy="214" r="2.2" /><circle cx="1030" cy="226" r="2.2" />
      </g>
      <path d="M-40,480 L360,300 L840,300 L1240,480 Z" fill="url(#bhPitch)" />
      <path d="M-40,480 L360,300 L840,300 L1240,480 Z" fill="none" stroke="#2BD37E" strokeOpacity="0.12" strokeWidth="2" />
      <line x1="600" y1="300" x2="600" y2="480" stroke="#2BD37E" strokeOpacity="0.16" strokeWidth="2" />
      <ellipse cx="600" cy="392" rx="120" ry="34" fill="none" stroke="#2BD37E" strokeOpacity="0.16" strokeWidth="2" />
      <g fill="#2BD37E" opacity="0.05">
        <polygon points="-40,480 120,392 200,392 60,480" />
        <polygon points="300,480 380,392 460,392 420,480" />
        <polygon points="660,480 700,392 780,392 800,480" />
        <polygon points="1020,480 940,392 1020,392 1240,480" />
      </g>
      <g opacity="0.9">
        <rect x="180" y="70" width="7" height="11" rx="1.5" fill="#FCDD09" transform="rotate(18 183 75)" />
        <rect x="280" y="120" width="6" height="10" rx="1.5" fill="#2BD37E" transform="rotate(-22 283 125)" />
        <rect x="400" y="60" width="7" height="11" rx="1.5" fill="#4D8BFF" transform="rotate(30 403 65)" />
        <rect x="700" y="90" width="6" height="10" rx="1.5" fill="#FCDD09" transform="rotate(-14 703 95)" />
        <rect x="820" y="64" width="7" height="11" rx="1.5" fill="#2BD37E" transform="rotate(24 823 69)" />
        <rect x="930" y="128" width="6" height="10" rx="1.5" fill="#4D8BFF" transform="rotate(-30 933 133)" />
        <rect x="540" y="44" width="6" height="10" rx="1.5" fill="#FF5A5A" transform="rotate(12 543 49)" />
        <rect x="620" y="150" width="6" height="10" rx="1.5" fill="#FCDD09" transform="rotate(-20 623 155)" />
      </g>
    </svg>
  );
}
