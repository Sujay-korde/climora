import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const ProblemBackdropIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat 1: The Heat Crisis (Frames 0 - 110: 0s - 3.6s)
  const opacityBeat1 = interpolate(frame, [0, 15, 95, 115], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateYBeat1 = interpolate(frame, [0, 20], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Beat 2: Introducing Climora (Frames 110 - 240: 3.6s - 8.0s)
  const opacityBeat2 = interpolate(frame, [115, 130, 220, 240], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateYBeat2 = interpolate(frame, [115, 135], [25, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Ambient pulsing heat aura
  const auraScale = interpolate(Math.sin(frame / 20), [-1, 1], [0.92, 1.08]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 50,
        backgroundColor: "#090a0f",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        fontFamily: "'Space Grotesk', Inter, sans-serif",
      }}
    >
      {/* Background Animated Heat Gradients */}
      <div
        style={{
          position: "absolute",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(239, 68, 68, 0.16) 0%, rgba(249, 115, 22, 0.08) 50%, transparent 75%)",
          filter: "blur(60px)",
          transform: `scale(${auraScale})`,
          top: "10%",
          left: "25%",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          opacity: 0.6,
          pointerEvents: "none",
        }}
      />

      {/* BEAT 1: The Urban Heat Crisis */}
      <div
        style={{
          position: "absolute",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          maxWidth: 1200,
          padding: "0 40px",
          opacity: opacityBeat1,
          transform: `translateY(${translateYBeat1}px)`,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 18px",
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.12em",
            color: "#f87171",
            textTransform: "uppercase",
            marginBottom: 28,
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", boxShadow: "0 0 10px #ef4444" }} />
          Global South Climate Vulnerability
        </div>

        <h1
          style={{
            fontSize: 64,
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            color: "#f8fafc",
            margin: "0 0 24px 0",
            textShadow: "0 10px 40px rgba(0,0,0,0.8)",
          }}
        >
          Cities Are Turning Into <span style={{ color: "#f97316" }}>Furnaces</span>.
        </h1>

        <p
          style={{
            fontSize: 22,
            lineHeight: 1.5,
            color: "#94a3b8",
            maxWidth: 880,
            margin: "0 0 36px 0",
          }}
        >
          In Pune, pre-monsoon surface temperatures breach <strong style={{ color: "#ef4444" }}>46.36°C</strong>.
          Yet municipal climate budgets are allocated using guesswork, ward politics, and unverified paper maps.
        </p>

        {/* Telemetry contrast pills */}
        <div style={{ display: "flex", gap: 20 }}>
          <div
            style={{
              padding: "16px 28px",
              background: "rgba(18, 21, 30, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: 14,
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em" }}>Earth Observation</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#38bdf8", marginTop: 4 }}>Petabytes of Thermal Data</div>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              color: "#64748b",
              fontSize: 20,
            }}
          >
            ≠
          </div>
          <div
            style={{
              padding: "16px 28px",
              background: "rgba(18, 21, 30, 0.8)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: 14,
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: 11, color: "#f87171", textTransform: "uppercase", letterSpacing: "0.08em" }}>Municipal Execution</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#fca5a5", marginTop: 4 }}>Zero Spatial Optimization</div>
          </div>
        </div>
      </div>

      {/* BEAT 2: Introducing Climora */}
      <div
        style={{
          position: "absolute",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          maxWidth: 1300,
          padding: "0 40px",
          opacity: opacityBeat2,
          transform: `translateY(${translateYBeat2}px)`,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 20px",
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.12em",
            color: "#10b981",
            textTransform: "uppercase",
            marginBottom: 24,
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 10px #10b981" }} />
          Novex 2026 Climate Tech Pitch
        </div>

        <h2
          style={{
            fontSize: 68,
            fontWeight: 800,
            letterSpacing: "-0.03em",
            color: "#f8fafc",
            margin: "0 0 16px 0",
            display: "flex",
            alignItems: "center",
            gap: 18,
          }}
        >
          <span>Meet</span>
          <span
            style={{
              background: "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            CLIMORA
          </span>
        </h2>

        <p
          style={{
            fontSize: 24,
            lineHeight: 1.4,
            color: "#cbd5e1",
            maxWidth: 900,
            margin: "0 0 40px 0",
          }}
        >
          The open decision layer transforming planetary Earth observations into statutory, bankable municipal capital expenditure.
        </p>

        {/* 3 Architecture Hero Pillars */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24, width: "100%", maxWidth: 1050 }}>
          <div
            style={{
              background: "rgba(18, 21, 30, 0.75)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: 16,
              padding: "24px 20px",
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 8 }}>🛰️</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.06em" }}>Stage 1: Observation</div>
            <div style={{ fontSize: 17, fontWeight: 600, color: "#f8fafc", marginTop: 4 }}>3,181 H3 Hexagonal Grid</div>
            <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>Landsat 8/9 LST + Sentinel 2 + WorldPop</div>
          </div>

          <div
            style={{
              background: "rgba(18, 21, 30, 0.75)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              borderRadius: 16,
              padding: "24px 20px",
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 8 }}>⚡</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#10b981", textTransform: "uppercase", letterSpacing: "0.06em" }}>Stage 2: Optimization</div>
            <div style={{ fontSize: 17, fontWeight: 600, color: "#f8fafc", marginTop: 4 }}>HiGHS MILP Solver</div>
            <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>₹1 Crore Cap · 28 Priority Cells Isolated</div>
          </div>

          <div
            style={{
              background: "rgba(18, 21, 30, 0.75)",
              border: "1px solid rgba(168, 85, 247, 0.3)",
              borderRadius: 16,
              padding: "24px 20px",
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 8 }}>🛡️</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#c084fc", textTransform: "uppercase", letterSpacing: "0.06em" }}>Stage 3: Governance</div>
            <div style={{ fontSize: 17, fontWeight: 600, color: "#f8fafc", marginTop: 4 }}>Cedar Policy Engine</div>
            <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>Cryptographic SHA-256 Audit Locking</div>
          </div>
        </div>
      </div>
    </div>
  );
};

