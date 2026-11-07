import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const ArchitectureFlowchart: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodes = [
    {
      id: "01",
      title: "Earth Observation Ingestion",
      tech: "Landsat 8/9 TIRS · Sentinel-2 MSI",
      metric: "46.36°C Peak LST",
      truth: "OBSERVED",
      color: "#f97316",
    },
    {
      id: "02",
      title: "H3 Hexagonal Spatial Mesh",
      tech: "Uber H3 Resolution-9 Grid",
      metric: "3,181 Hex Cells (~0.0986 km²)",
      truth: "DERIVED",
      color: "#06b6d4",
    },
    {
      id: "03",
      title: "Deterministic Risk Synthesis",
      tech: "IPCC AR6 (Hazard × Exposure × Vuln)",
      metric: "Zero-Exposure Axiom (E=0 ⟹ R=0)",
      truth: "DERIVED",
      color: "#38bdf8",
    },
    {
      id: "04",
      title: "HiGHS Portfolio Optimization",
      tech: "Mixed-Integer Linear Programming",
      metric: "<200ms Exact Integer Solve",
      truth: "MODELED",
      color: "#10b981",
    },
    {
      id: "05",
      title: "Cedar Cryptographic ABAC",
      tech: "5 Personas · 7 Ratified Policies",
      metric: "SHA-256 Anti-Tamper Provenance",
      truth: "BUILT",
      color: "#a855f7",
    },
    {
      id: "06",
      title: "Empirical MRV Protocol",
      tech: "Difference-in-Differences (DiD)",
      metric: "Synthetic Matched Controls",
      truth: "PLANNED",
      color: "#ec4899",
    },
  ];

  // Global title spring
  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 100 },
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 40%, #101424 0%, #06080d 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "80px 120px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Decorative Tech Grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      {/* Hero Header */}
      <div
        style={{
          textAlign: "center",
          marginBottom: 70,
          transform: `scale(${interpolate(titleSpring, [0, 1], [0.92, 1])})`,
          opacity: titleSpring,
          zIndex: 10,
        }}
      >
        <div
          style={{
            fontFamily: "monospace",
            fontSize: 20,
            textTransform: "uppercase",
            letterSpacing: "0.2em",
            color: "#06b6d4",
            marginBottom: 12,
            fontWeight: 700,
          }}
        >
          End-to-End System Lineage & Pipeline Architecture
        </div>
        <h1
          style={{
            fontFamily: "sans-serif",
            fontSize: 64,
            fontWeight: 800,
            color: "#f8fafc",
            letterSpacing: "-0.03em",
            margin: 0,
          }}
        >
          From Satellite Radiances to Statutory Municipal Tenders
        </h1>
      </div>

      {/* 6 Flowchart Nodes (2 rows of 3) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 36,
          width: "100%",
          maxWidth: 3200,
          zIndex: 10,
        }}
      >
        {nodes.map((node, i) => {
          const nodeSpring = spring({
            frame: frame - (15 + i * 8),
            fps,
            config: { damping: 18, stiffness: 120 },
          });

          const opacity = interpolate(nodeSpring, [0, 1], [0, 1]);
          const translateY = interpolate(nodeSpring, [0, 1], [40, 0]);

          // Traveling light pulse effect
          const pulseProgress = ((frame * 2 + i * 40) % 200) / 200;

          return (
            <div
              key={node.id}
              style={{
                opacity,
                transform: `translateY(${translateY}px)`,
                background: "rgba(18, 21, 30, 0.85)",
                backdropFilter: "blur(20px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: 20,
                padding: "36px 36px",
                boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                height: 340,
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Traveling Light Pulse Indicator */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: `${pulseProgress * 100}%`,
                  width: 120,
                  height: 3,
                  background: `linear-gradient(90deg, transparent, ${node.color}, transparent)`,
                }}
              />

              {/* Node Top Header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: 22,
                    fontWeight: 800,
                    color: node.color,
                  }}
                >
                  STAGE {node.id}
                </span>
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: 14,
                    padding: "4px 10px",
                    borderRadius: 6,
                    background: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    color: "#cbd5e1",
                    fontWeight: 700,
                  }}
                >
                  [{node.truth}]
                </span>
              </div>

              {/* Node Title & Description */}
              <div>
                <h3
                  style={{
                    fontFamily: "sans-serif",
                    fontSize: 32,
                    fontWeight: 700,
                    color: "#f8fafc",
                    margin: "0 0 10px 0",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {node.title}
                </h3>
                <p
                  style={{
                    fontFamily: "sans-serif",
                    fontSize: 20,
                    color: "#94a3b8",
                    margin: 0,
                    lineHeight: 1.4,
                  }}
                >
                  {node.tech}
                </p>
              </div>

              {/* Node Metric Footer */}
              <div
                style={{
                  borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                  paddingTop: 18,
                  fontFamily: "monospace",
                  fontSize: 20,
                  color: node.color,
                  fontWeight: 700,
                }}
              >
                ● {node.metric}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

