interface Props {
  height?: number;
  className?: string;
}

/**
 * WC26 Intelligence wordmark. Themed for the dark UI: white "WC", a soccer-ball
 * glyph, gradient-blue "26", and a tracked "INTELLIGENCE" subline. Scalable
 * vector — set height; width follows the 150×60 aspect ratio.
 */
export default function BrandLogo({ height = 36, className }: Props) {
  return (
    <svg
      viewBox="0 0 150 60"
      height={height}
      width={(height * 150) / 60}
      className={className}
      role="img"
      aria-label="WC26 Intelligence"
    >
      <defs>
        <linearGradient id="wc26-26" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#1E54E0" />
          <stop offset="1" stopColor="#4D8BFF" />
        </linearGradient>
      </defs>
      <g fontFamily="Inter, -apple-system, 'Segoe UI', Roboto, sans-serif">
        <text x="0" y="42" fontSize="42" fontWeight="800" letterSpacing="-2" fill="#FFFFFF">
          WC
        </text>
        <g transform="translate(72,27)">
          <circle r="14.5" fill="#FFFFFF" stroke="#0A1B3D" strokeWidth="1.4" />
          <polygon points="0,-7 6.66,-2.16 4.11,5.66 -4.11,5.66 -6.66,-2.16" fill="#0A1B3D" />
          <g stroke="#0A1B3D" strokeWidth="1.4" strokeLinecap="round">
            <line x1="0" y1="-7" x2="0" y2="-14.5" />
            <line x1="6.66" y1="-2.16" x2="13.8" y2="-4.48" />
            <line x1="4.11" y1="5.66" x2="8.52" y2="11.73" />
            <line x1="-4.11" y1="5.66" x2="-8.52" y2="11.73" />
            <line x1="-6.66" y1="-2.16" x2="-13.8" y2="-4.48" />
          </g>
        </g>
        <text x="90" y="42" fontSize="42" fontWeight="800" letterSpacing="-2" fill="url(#wc26-26)">
          26
        </text>
        <text x="1" y="55" fontSize="10" fontWeight="600" letterSpacing="4" fill="#A9B6D4">
          INTELLIGENCE
        </text>
      </g>
    </svg>
  );
}
