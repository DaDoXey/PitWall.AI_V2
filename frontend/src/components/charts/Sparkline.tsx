// Mini-trend SVG hand-rolled (no Recharts): decorativo-informativo, si legge a
// colpo d'occhio. Coerente con PressureGauge/TyreHeatmap (già SVG) e leggero:
// non trascina il bundle Recharts sulla Dashboard.
import { useId } from "react";

export default function Sparkline({
  data,
  color,
  width = 96,
  height = 28,
  strokeWidth = 1.5,
  fill = true,
  className,
}: {
  data: number[];
  color: string;
  width?: number;
  height?: number;
  strokeWidth?: number;
  fill?: boolean;
  className?: string; // es. "w-full": scala orizzontalmente (viewBox + stroke non-scaling)
}) {
  const gid = useId();
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1; // serie piatta → linea centrata, niente /0
  const pad = strokeWidth + 0.5;

  const x = (i: number) => (i / (data.length - 1)) * (width - pad * 2) + pad;
  const y = (v: number) => height - pad - ((v - min) / span) * (height - pad * 2);

  const pts = data.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const line = `M ${pts.join(" L ")}`;
  const area = `${line} L ${x(data.length - 1).toFixed(1)},${(height - pad).toFixed(1)} L ${x(0).toFixed(1)},${(height - pad).toFixed(1)} Z`;
  const lastX = x(data.length - 1);
  const lastY = y(data[data.length - 1]);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={className}
      aria-hidden="true"
    >
      {fill && (
        <>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#${gid})`} />
        </>
      )}
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={lastX} cy={lastY} r={strokeWidth + 0.5} fill={color} />
    </svg>
  );
}
