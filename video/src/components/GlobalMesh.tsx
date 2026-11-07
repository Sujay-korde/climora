import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const GlobalMesh: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 16, stiffness: 100 } });

  const cities = [
    { name: "Pune (PMC)", country: "India", cells: "3,181 H3 Cells", status: "VALIDATED BASELINE", active: true },
    { name: "Delhi (MCD)", country: "India", cells: "14,800 H3 Cells", status: "READY FOR INGESTION", active: false },
    { name: "Hyderabad (GHMC)", country: "India", cells: "6,500 H3 Cells", status: "READY FOR INGESTION", active: false },
    { name: "Cairo (CAPMAS)", country: "Egypt", cells: "22,400 H3 Cells", status: "READY FOR INGESTION", active: false },
    { name: "Jakarta (DKI)", country: "Indonesia", cells: "7,100 H3 Cells", status: "READY FOR INGESTION", active: false },
  ];

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "radial-gradient(circle at 50% 40%, #0d1e26 0%, #050a0e 100%)",
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
            color: "#10b981",
            fontWeight: 800,
          }}
        >
          City-Agnostic Spatial Intelligence
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
          Scalable to 100+ Vulnerable Metropolises Across the Global South
        </h1>
      </div>

      {/* Global Cities Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: 28,
          width: "100%",
          maxWidth: 3400,
        }}
      >
        {cities.map((c, i) => {
          const cardSpring = spring({
            frame: frame - (10 + i * 8),
            fps,
            config: { damping: 18, stiffness: 120 },
          });

          return (
            <div
              key={c.name}
              style={{
                opacity: cardSpring,
                transform: `translateY(${interpolate(cardSpring, [0, 1], [40, 0])}px)`,
                background: c.active ? "rgba(16, 185, 129, 0.12)" : "rgba(18, 24, 38, 0.8)",
                backdropFilter: "blur(20px)",
                border: c.active ? "2px solid #10b981" : "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: 20,
                padding: "36px 28px",
                boxShadow: c.active
                  ? "0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(16, 185, 129, 0.3)"
                  : "0 20px 40px rgba(0, 0, 0, 0.5)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                height: 380,
              }}
            >
              <div>
                <span
                  style={{
                    fontFamily: "monospace",
                    fontSize: 16,
                    color: c.active ? "#34d399" : "#94a3b8",
                    fontWeight: 700,
                  }}
                >
                  {c.country}
                </span>
                <h3
                  style={{
                    fontFamily: "sans-serif",
                    fontSize: 30,
                    fontWeight: 700,
                    color: "#f8fafc",
                    margin: "12px 0 16px 0",
                  }}
                >
                  {c.name}
                </h3>
                <div
                  style={{
                    fontFamily: "monospace",
                    fontSize: 20,
                    color: "#38bdf8",
                    marginBottom: 10,
                  }}
                >
                  {c.cells}
                </div>
              </div>

              <div
                style={{
                  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                  paddingTop: 16,
                  fontFamily: "monospace",
                  fontSize: 14,
                  fontWeight: 700,
                  color: c.active ? "#10b981" : "#94a3b8",
                  letterSpacing: "0.06em",
                }}
              >
                ● {c.status}
              </div>
            </div>
          );
        })}
      </div>

      {/* SLA Banner */}
      <div
        style={{
          marginTop: 60,
          background: "rgba(6, 182, 212, 0.1)",
          border: "1px solid rgba(6, 182, 212, 0.3)",
          borderRadius: 16,
          padding: "20px 48px",
          display: "flex",
          gap: 60,
          alignItems: "center",
          fontFamily: "monospace",
          fontSize: 22,
          color: "#f8fafc",
        }}
      >
        <div>⚡ <span style={{ color: "#38bdf8", fontWeight: 700 }}>48-Hour Deployment SLA</span> (Open Data Lake)</div>
        <div>🛰 <span style={{ color: "#38bdf8", fontWeight: 700 }}>No Ground Sensor Dependency</span> for Baseline</div>
        <div>🔒 <span style={{ color: "#38bdf8", fontWeight: 700 }}>Cedar Policy Engine</span> ABAC Security</div>
      </div>
    </div>
  );
};

