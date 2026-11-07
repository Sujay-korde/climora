import React from "react";
import { Video, staticFile, useCurrentFrame, interpolate } from "remotion";

interface DeviceFrameProps {
  videoSrc: string;
  urlBarText?: string;
}

export const DeviceFrame: React.FC<DeviceFrameProps> = ({
  videoSrc,
  urlBarText = "climora.app/explore/pune",
}) => {
  const frame = useCurrentFrame();
  const subtleScale = interpolate(frame, [0, 900], [0.98, 1.01], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "radial-gradient(circle at center, #111522 0%, #080a10 100%)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: 3200,
          height: 1860,
          borderRadius: 24,
          overflow: "hidden",
          border: "2px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 40px 120px rgba(0, 0, 0, 0.85), 0 0 40px rgba(6, 182, 212, 0.2)",
          background: "#0c0e14",
          display: "flex",
          flexDirection: "column",
          transform: `scale(${subtleScale})`,
        }}
      >
        {/* Browser Top Chrome */}
        <div
          style={{
            height: 64,
            background: "rgba(18, 21, 30, 0.98)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            padding: "0 28px",
            justifyContent: "space-between",
          }}
        >
          {/* Traffic Light Dots */}
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#ef4444" }} />
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#f59e0b" }} />
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#10b981" }} />
          </div>

          {/* URL Pill */}
          <div
            style={{
              width: 900,
              height: 38,
              borderRadius: 8,
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 10,
              color: "#94a3b8",
              fontFamily: "monospace",
              fontSize: 15,
            }}
          >
            <span style={{ color: "#10b981" }}>🔒</span>
            <span>https://{urlBarText}</span>
          </div>

          {/* Right badge */}
          <div
            style={{
              fontFamily: "monospace",
              fontSize: 13,
              color: "#06b6d4",
              background: "rgba(6, 182, 212, 0.1)",
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid rgba(6, 182, 212, 0.3)",
              fontWeight: 600,
            }}
          >
            PMC STATUTORY SYSTEM
          </div>
        </div>

        {/* Video Screen Body */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          <Video
            src={staticFile(videoSrc)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </div>
      </div>
    </div>
  );
};

