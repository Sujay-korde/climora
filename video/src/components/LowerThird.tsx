import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface LowerThirdProps {
  category: string;
  title: string;
  metricLabel?: string;
  metricValue?: string;
  truthLayer?: "OBSERVED" | "DERIVED" | "MODELED" | "VERIFIED" | "BUILT";
  delayFrames?: number;
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  category,
  title,
  metricLabel,
  metricValue,
  truthLayer = "OBSERVED",
  delayFrames = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delayFrames,
    fps,
    config: { damping: 16, stiffness: 120 },
  });

  const opacity = interpolate(entrance, [0, 1], [0, 1]);
  const translateY = interpolate(entrance, [0, 1], [30, 0]);

  const truthColors = {
    OBSERVED: { bg: "rgba(16, 185, 129, 0.15)", border: "#10b981", text: "#34d399" },
    DERIVED: { bg: "rgba(6, 182, 212, 0.15)", border: "#06b6d4", text: "#38bdf8" },
    MODELED: { bg: "rgba(249, 115, 22, 0.15)", border: "#f97316", text: "#fb923c" },
    VERIFIED: { bg: "rgba(168, 85, 247, 0.15)", border: "#a855f7", text: "#c084fc" },
    BUILT: { bg: "rgba(59, 130, 246, 0.15)", border: "#3b82f6", text: "#60a5fa" },
  };

  const badge = truthColors[truthLayer] || truthColors.OBSERVED;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 100,
        opacity,
        transform: `translateY(${translateY}px)`,
        display: "flex",
        alignItems: "center",
        gap: 24,
        background: "rgba(18, 21, 30, 0.92)",
        backdropFilter: "blur(24px)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: 12,
        padding: "18px 28px",
        boxShadow: "0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(6, 182, 212, 0.15)",
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              fontFamily: "monospace",
              fontSize: 16,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "#f97316",
              fontWeight: 700,
            }}
          >
            {category}
          </span>
          <span
            style={{
              padding: "2px 10px",
              borderRadius: 6,
              background: badge.bg,
              border: `1px solid ${badge.border}`,
              color: badge.text,
              fontSize: 14,
              fontFamily: "monospace",
              fontWeight: 700,
              letterSpacing: "0.08em",
            }}
          >
            [{truthLayer}]
          </span>
        </div>
        <div
          style={{
            color: "#f8fafc",
            fontSize: 24,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            fontFamily: "sans-serif",
          }}
        >
          {title}
        </div>
      </div>

      {metricValue && (
        <div
          style={{
            borderLeft: "1px solid rgba(255, 255, 255, 0.15)",
            paddingLeft: 24,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <span
            style={{
              color: "#94a3b8",
              fontSize: 14,
              fontFamily: "monospace",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {metricLabel || "Metric"}
          </span>
          <span
            style={{
              color: "#38bdf8",
              fontSize: 28,
              fontWeight: 700,
              fontFamily: "monospace",
            }}
          >
            {metricValue}
          </span>
        </div>
      )}
    </div>
  );
};

