import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const BrandClimax: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoSpring = spring({ frame, fps, config: { damping: 14, stiffness: 90 } });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 45%, #101726 0%, #060910 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px 140px",
        position: "relative",
      }}
    >
      {/* Center Hero Lockup */}
      <div
        style={{
          textAlign: "center",
          opacity: logoSpring,
          transform: `scale(${interpolate(logoSpring, [0, 1], [0.88, 1])})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            padding: "8px 24px",
            borderRadius: 100,
            background: "rgba(249, 115, 22, 0.12)",
            border: "1px solid rgba(249, 115, 22, 0.35)",
            color: "#fb923c",
            fontFamily: "monospace",
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: "0.1em",
            marginBottom: 28,
          }}
        >
          <span>★</span> NOVEX 2026 CLIMATE TECH EVALUATION
        </div>

        <h1
          style={{
            fontFamily: "sans-serif",
            fontSize: 140,
            fontWeight: 900,
            letterSpacing: "-0.04em",
            margin: "0 0 20px 0",
            background: "linear-gradient(135deg, #06b6d4 0%, #f97316 50%, #10b981 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            textShadow: "0 0 80px rgba(6, 182, 212, 0.3)",
          }}
        >
          CLIMORA
        </h1>

        <p
          style={{
            fontFamily: "sans-serif",
            fontSize: 38,
            color: "#f8fafc",
            fontWeight: 600,
            maxWidth: 1800,
            lineHeight: 1.3,
            margin: "0 0 50px 0",
            letterSpacing: "-0.01em",
          }}
        >
          Turning planetary observations into fundable urban heat interventions.
        </p>

        {/* Action Cards */}
        <div
          style={{
            display: "flex",
            gap: 40,
            alignItems: "center",
          }}
        >
          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: 16,
              padding: "24px 44px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span style={{ fontFamily: "monospace", fontSize: 16, color: "#94a3b8", textTransform: "uppercase" }}>
              Live Production Prototype
            </span>
            <span style={{ fontFamily: "monospace", fontSize: 32, fontWeight: 800, color: "#38bdf8" }}>
              climora.app
            </span>
          </div>

          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: 16,
              padding: "24px 44px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span style={{ fontFamily: "monospace", fontSize: 16, color: "#94a3b8", textTransform: "uppercase" }}>
              Canonical AOI Study
            </span>
            <span style={{ fontFamily: "monospace", fontSize: 32, fontWeight: 800, color: "#34d399" }}>
              Pune Municipal Corp (PMC)
            </span>
          </div>

          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: 16,
              padding: "24px 44px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span style={{ fontFamily: "monospace", fontSize: 16, color: "#94a3b8", textTransform: "uppercase" }}>
              Academic & Research Core
            </span>
            <span style={{ fontFamily: "monospace", fontSize: 32, fontWeight: 800, color: "#fb923c" }}>
              VIT Pune · CSE (AIML)
            </span>
          </div>
        </div>

        <div
          style={{
            marginTop: 60,
            fontFamily: "monospace",
            fontSize: 24,
            color: "#64748b",
            letterSpacing: "0.06em",
          }}
        >
          Don't guess where to cool our cities. Solve it.
        </div>
      </div>
    </div>
  );
};

