import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const FailureSpiral: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 16, stiffness: 100 } });

  const failures = [
    {
      num: "01",
      title: "The Spatial Disconnect",
      subtitle: "Detection ≠ Capital Allocation",
      desc: "Satellites output raw raster pixels. Municipalities manage administrative wards. Square rasters obscure micro-urban heat corridors and distort boundary truth.",
      stat: "100+ Wards Gerrymandered",
    },
    {
      num: "02",
      title: "The Capital Dilemma",
      subtitle: "Blind Heuristic Greening",
      desc: "Municipal budgets face severe capital scarcity. Without mathematical optimization, saplings are dumped on highway medians based on political quotas rather than thermodynamic need.",
      stat: "Millions Lost to Guesswork",
    },
    {
      num: "03",
      title: "The Verification Vacuum",
      subtitle: "Zero Post-Deployment MRV",
      desc: "Civic greening drives report inputs (saplings procured) rather than outcomes (cooling delivered). Once planted, trees wither unmonitored with zero empirical measurement.",
      stat: "0% Post-Audit Accountability",
    },
  ];

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 35%, #180d12 0%, #080507 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px 140px",
        position: "relative",
      }}
    >
      {/* Title */}
      <div
        style={{
          textAlign: "center",
          marginBottom: 80,
          opacity: titleSpring,
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.94, 1])})`,
        }}
      >
        <span
          style={{
            fontFamily: "monospace",
            fontSize: 22,
            textTransform: "uppercase",
            letterSpacing: "0.2em",
            color: "#ef4444",
            fontWeight: 800,
          }}
        >
          The Conventional Adaptation Failure Spiral
        </span>
        <h1
          style={{
            fontFamily: "sans-serif",
            fontSize: 64,
            fontWeight: 800,
            color: "#f8fafc",
            margin: "12px 0 0 0",
            letterSpacing: "-0.03em",
          }}
        >
          Three Systemic Failures Draining Municipal Climate Funds
        </h1>
      </div>

      {/* 3 Failure Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 48,
          width: "100%",
          maxWidth: 3200,
        }}
      >
        {failures.map((f, i) => {
          const cardSpring = spring({
            frame: frame - (12 + i * 12),
            fps,
            config: { damping: 18, stiffness: 120 },
          });

          return (
            <div
              key={f.num}
              style={{
                opacity: cardSpring,
                transform: `translateY(${interpolate(cardSpring, [0, 1], [50, 0])}px)`,
                background: "rgba(25, 12, 16, 0.85)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(239, 68, 68, 0.25)",
                borderRadius: 24,
                padding: "48px 40px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                height: 480,
                boxShadow: "0 24px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(239, 68, 68, 0.15)",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 20 }}>
                  <span style={{ fontFamily: "monospace", fontSize: 24, fontWeight: 800, color: "#ef4444" }}>
                    CRISIS {f.num}
                  </span>
                  <span style={{ fontFamily: "monospace", fontSize: 16, color: "#f87171" }}>
                    {f.subtitle}
                  </span>
                </div>
                <h3 style={{ fontFamily: "sans-serif", fontSize: 36, fontWeight: 700, color: "#f8fafc", margin: "0 0 16px 0" }}>
                  {f.title}
                </h3>
                <p style={{ fontFamily: "sans-serif", fontSize: 22, color: "#cbd5e1", lineHeight: 1.5, margin: 0 }}>
                  {f.desc}
                </p>
              </div>

              <div
                style={{
                  borderTop: "1px solid rgba(239, 68, 68, 0.2)",
                  paddingTop: 20,
                  fontFamily: "monospace",
                  fontSize: 22,
                  color: "#f87171",
                  fontWeight: 700,
                }}
              >
                ⚠ {f.stat}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

