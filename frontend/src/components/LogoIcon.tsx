export default function LogoIcon() {
  return (
    <svg
      width="80"
      height="64"
      viewBox="0 0 80 64"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="DietMate67 logo"
      style={{ overflow: 'visible' }}
    >
      <defs>
        <style>{`
          @keyframes dm67-throwL {
            0%   { transform: translateY(0)     rotate(0deg);   }
            9%   { transform: translateY(-22px)  rotate(-20deg); }
            18%  { transform: translateY(6px)    rotate(6deg);   }
            25%  { transform: translateY(-3px)   rotate(-2deg);  }
            32%  { transform: translateY(0)      rotate(0deg);   }
            100% { transform: translateY(0)      rotate(0deg);   }
          }

          @keyframes dm67-throwR {
            0%,  48% { transform: translateY(0)     rotate(0deg);  }
            57%      { transform: translateY(-22px)  rotate(20deg); }
            66%      { transform: translateY(6px)    rotate(-6deg); }
            73%      { transform: translateY(-3px)   rotate(2deg);  }
            80%      { transform: translateY(0)      rotate(0deg);  }
            100%     { transform: translateY(0)      rotate(0deg);  }
          }

          @keyframes dm67-rainbow {
            0%   { fill: #ff0000; }
            14%  { fill: #ff8800; }
            28%  { fill: #ffee00; }
            42%  { fill: #00cc44; }
            57%  { fill: #0099ff; }
            71%  { fill: #6633ff; }
            85%  { fill: #ff00cc; }
            100% { fill: #ff0000; }
          }

          .dm67-L {
            animation: dm67-throwL 0.65s ease-in-out infinite;
            transform-origin: 16px 56px;
          }
          .dm67-R {
            animation: dm67-throwR 0.65s ease-in-out infinite;
            transform-origin: 64px 56px;
          }
          .dm67-six {
            animation: dm67-rainbow 1.4s linear infinite;
            font-family: Arial Black, Arial, sans-serif;
            font-weight: 900;
            font-size: 19px;
          }
          .dm67-seven {
            animation: dm67-rainbow 1.4s linear infinite 0.7s;
            font-family: Arial Black, Arial, sans-serif;
            font-weight: 900;
            font-size: 19px;
          }
        `}</style>
      </defs>

      {/* ── Left hand + "6" ── */}
      <g className="dm67-L">
        {/* Rainbow 6 above the hand */}
        <text x="16" y="29" textAnchor="middle" className="dm67-six">6</text>

        {/* Fingers */}
        <rect x="4"    y="37" width="4.5" height="13" rx="2.25" fill="#fcd9a0" />
        <rect x="9.5"  y="34" width="4.5" height="16" rx="2.25" fill="#fcd9a0" />
        <rect x="15"   y="35" width="4.5" height="15" rx="2.25" fill="#fcd9a0" />
        <rect x="20.5" y="37" width="4.5" height="13" rx="2.25" fill="#fcd9a0" />
        {/* Thumb */}
        <rect x="1"    y="44" width="4"   height="10" rx="2"    fill="#fcd9a0" transform="rotate(-18 1 44)" />
        {/* Palm */}
        <rect x="3"    y="48" width="23"  height="10" rx="5"    fill="#fcd9a0" />
      </g>

      {/* ── Right hand + "7" ── */}
      <g className="dm67-R">
        {/* Rainbow 7 above the hand */}
        <text x="64" y="29" textAnchor="middle" className="dm67-seven">7</text>

        {/* Fingers */}
        <rect x="52"   y="37" width="4.5" height="13" rx="2.25" fill="#fcd9a0" />
        <rect x="57.5" y="34" width="4.5" height="16" rx="2.25" fill="#fcd9a0" />
        <rect x="63"   y="35" width="4.5" height="15" rx="2.25" fill="#fcd9a0" />
        <rect x="68.5" y="37" width="4.5" height="13" rx="2.25" fill="#fcd9a0" />
        {/* Thumb */}
        <rect x="75"   y="44" width="4"   height="10" rx="2"    fill="#fcd9a0" transform="rotate(18 79 44)" />
        {/* Palm */}
        <rect x="54"   y="48" width="23"  height="10" rx="5"    fill="#fcd9a0" />
      </g>
    </svg>
  )
}
