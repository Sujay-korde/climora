import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const MathFormulation: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 16, stiffness: 100 } });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 40%, #0d1624 0%, #05080f 100%)",
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
          marginBottom: 70,
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
            color: "#06b6d4",
            fontWeight: 800,
          }}
        >
          Operations Research & Scientific Rigor
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
          Deterministic Risk Formulation & HiGHS Integer Programming
        </h1>
      </div>

      {/* 2 Main Math Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 60,
          width: "100%",
          maxWidth: 3200,
        }}
      >
        {/* Left: Zero Exposure & IPCC HEV */}
        <div
          style={{
            background: "rgba(18, 24, 38, 0.85)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            borderRadius: 24,
            padding: "54px 48px",
            boxShadow: "0 24px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(6, 182, 212, 0.15)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
              <span style={{ fontFamily: "monospace", fontSize: 20, color: "#06b6d4", fontWeight: 700 }}>
                AXIOM F-22.1 · RISK HARMONIZATION
              </span>
              <span style={{ fontFamily: "monospace", fontSize: 16, color: "#38bdf8", padding: "4px 10px", background: "rgba(6,182,212,0.15)", borderRadius: 6 }}>
                [DERIVED]
              </span>
            </div>
            <h3 style={{ fontFamily: "sans-serif", fontSize: 36, fontWeight: 700, color: "#f8fafc", margin: "0 0 20px 0" }}>
              The Zero-Exposure Axiom
            </h3>
            <div
              style={{
                background: "rgba(0, 0, 0, 0.4)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: 16,
                padding: "28px",
                fontFamily: "monospace",
                fontSize: 32,
                color: "#f97316",
                textAlign: "center",
                marginBottom: 24,
                fontWeight: 700,
              }}
            >
              E_i = 0 ⟹ R_i = 0
            </div>
            <p style={{ fontFamily: "sans-serif", fontSize: 22, color: "#cbd5e1", lineHeight: 1.5, margin: 0 }}>
              Where there is no human population exposed, composite climate risk equals zero. Eliminates phantom risk across uninhabited hills and industrial wastelands.
            </p>
          </div>
          <div style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)", paddingTop: 20, fontFamily: "monospace", fontSize: 20, color: "#94a3b8" }}>
            ● Composite Index: <span style={{ color: "#38bdf8" }}>R_i = H_i × E_i × V_i</span> (0 to 1 normalized)
          </div>
        </div>

        {/* Right: HiGHS MILP Formulation */}
        <div
          style={{
            background: "rgba(18, 24, 38, 0.85)",
            backdropFilter: "blur(20px)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: 24,
            padding: "54px 48px",
            boxShadow: "0 24px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(16, 185, 129, 0.15)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
              <span style={{ fontFamily: "monospace", fontSize: 20, color: "#10b981", fontWeight: 700 }}>
                OPERATIONS RESEARCH · HIGHS SOLVER
              </span>
              <span style={{ fontFamily: "monospace", fontSize: 16, color: "#34d399", padding: "4px 10px", background: "rgba(16,185,129,0.15)", borderRadius: 6 }}>
                [MODELED]
              </span>
            </div>
            <h3 style={{ fontFamily: "sans-serif", fontSize: 36, fontWeight: 700, color: "#f8fafc", margin: "0 0 20px 0" }}>
              Multi-Objective MILP Formulation
            </h3>
            <div
              style={{
                background: "rgba(0, 0, 0, 0.4)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: 16,
                padding: "24px",
                fontFamily: "monospace",
                fontSize: 26,
                color: "#10b981",
                textAlign: "center",
                marginBottom: 24,
                fontWeight: 700,
                lineHeight: 1.4,
              }}
            >
              max Σ (R_i · ΔT_i · Pop_i) - Cost_penalties<br />
              s.t. Σ Cost_i ≤ Budget_preset
            </div>
            <p style={{ fontFamily: "sans-serif", fontSize: 22, color: "#cbd5e1", lineHeight: 1.5, margin: 0 }}>
              Semi-continuous integer lot sizing, physical road capacity caps, and mobilization fixed costs ensure bankable tender feasibility.
            </p>
          </div>
          <div style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)", paddingTop: 20, fontFamily: "monospace", fontSize: 20, color: "#94a3b8" }}>
            ● Exact integer branch-and-cut solved in <span style={{ color: "#10b981" }}>&lt;200 ms</span>
          </div>
        </div>
      </div>
    </div>
  );
};

