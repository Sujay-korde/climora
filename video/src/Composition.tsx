import React from "react";
import { Composition, Sequence, Audio, staticFile, interpolate, useCurrentFrame } from "remotion";
import { ProblemBackdropIntro } from "./components/ProblemBackdropIntro";
import { DeviceFrame } from "./components/DeviceFrame";
import { LowerThird } from "./components/LowerThird";
import { FailureSpiral } from "./components/FailureSpiral";
import { ArchitectureFlowchart } from "./components/ArchitectureFlowchart";
import { MathFormulation } from "./components/MathFormulation";
import { GlobalMesh } from "./components/GlobalMesh";
import { BrandClimax } from "./components/BrandClimax";

export const TOTAL_FRAMES = 7200; // 240.0s @ 30 FPS
export const FPS = 30;

const Scene01WithIntro: React.FC = () => {
  const frame = useCurrentFrame();
  // Fade in the live UI recording smoothly starting at frame 225 (7.5s)
  const uiOpacity = interpolate(frame, [220, 245], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* 0s to 8s: Sleek Problem Backdrop & Project Identity Intro Animation */}
      {frame < 250 && <ProblemBackdropIntro />}

      {/* 7.5s to 20s: Live Dashboard screen capture fading in */}
      <div style={{ position: "absolute", inset: 0, opacity: uiOpacity }}>
        <DeviceFrame videoSrc="scene_01.mp4" urlBarText="climora.app" />
        {frame >= 245 && (
          <LowerThird
            category="Problem Statement"
            title="Surface Heat Breach in Pune (PMC AOI)"
            metricLabel="Peak Summer LST"
            metricValue="46.36°C"
            truthLayer="OBSERVED"
            delayFrames={10}
          />
        )}
      </div>
    </div>
  );
};

export const ClimoraLaunchVideo: React.FC = () => {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#090a0f",
        color: "#f8fafc",
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* Master Soundtrack (VO + Ducked 110 BPM Ambient Bed + Aligned SFX) */}
      <Audio src={staticFile("climora_master_soundtrack.wav")} />

      {/* -------------------------------------------------------------
          SCENE 01 (00:00 - 00:20 | Frames 0 - 600): The Problem Backdrop & Project Identity
          ------------------------------------------------------------- */}
      <Sequence from={0} durationInFrames={600}>
        <Scene01WithIntro />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 02 (00:20 - 00:45 | Frames 600 - 1350): Institutional Failure
          ------------------------------------------------------------- */}
      <Sequence from={600} durationInFrames={750}>
        <FailureSpiral />
        <LowerThird
          category="Market Failure"
          title="The Conventional Adaptation Failure Spiral"
          metricLabel="Accountability Gap"
          metricValue="0% Post-Audit MRV"
          truthLayer="DERIVED"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 03 (00:45 - 01:10 | Frames 1350 - 2100): Architecture Hero
          ------------------------------------------------------------- */}
      <Sequence from={1350} durationInFrames={750}>
        <ArchitectureFlowchart />
        <LowerThird
          category="System Architecture"
          title="6-Stage Closed-Loop Lineage Mesh"
          metricLabel="Spatial Grid Unit"
          metricValue="3,181 H3 Res-9 Cells"
          truthLayer="BUILT"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 04 (01:10 - 01:30 | Frames 2100 - 2700): Operations Research
          ------------------------------------------------------------- */}
      <Sequence from={2100} durationInFrames={600}>
        <MathFormulation />
        <LowerThird
          category="Mathematical Rigor"
          title="Zero-Exposure Axiom & HiGHS Integer Solver"
          metricLabel="MILP Solve Latency"
          metricValue="<200 ms"
          truthLayer="MODELED"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 05 (01:30 - 02:00 | Frames 2700 - 3600): Geospatial Explorer
          ------------------------------------------------------------- */}
      <Sequence from={2700} durationInFrames={900}>
        <DeviceFrame videoSrc="scene_05.mp4" urlBarText="climora.app/explore/pune" />
        <LowerThird
          category="Geospatial Explorer"
          title="Inspecting Priority Hex 89608850003ffff"
          metricLabel="Cell Population"
          metricValue="4,757 Residents"
          truthLayer="DERIVED"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 06 (02:00 - 02:30 | Frames 3600 - 4500): Portfolio Optimizer
          ------------------------------------------------------------- */}
      <Sequence from={3600} durationInFrames={900}>
        <DeviceFrame videoSrc="scene_06.mp4" urlBarText="climora.app/optimizer" />
        <LowerThird
          category="Portfolio Optimizer"
          title="₹1 Crore Canonical Capital Benchmark"
          metricLabel="Citizens Sheltered"
          metricValue="118,941 (₹84/Person)"
          truthLayer="MODELED"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 07 (02:30 - 03:00 | Frames 4500 - 5400): Cedar Governance
          ------------------------------------------------------------- */}
      <Sequence from={4500} durationInFrames={900}>
        <DeviceFrame videoSrc="scene_07.mp4" urlBarText="climora.app/projects/canonical" />
        <LowerThird
          category="Cryptographic Trust"
          title="Cedar Policy Engine & Immutable Provenance"
          metricLabel="Dossier Integrity"
          metricValue="SHA-256 Ratified"
          truthLayer="BUILT"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 08 (03:00 - 03:25 | Frames 5400 - 6150): Tripartite MRV
          ------------------------------------------------------------- */}
      <Sequence from={5400} durationInFrames={750}>
        <DeviceFrame videoSrc="scene_08.mp4" urlBarText="climora.app/mrv" />
        <LowerThird
          category="Empirical MRV"
          title="Difference-in-Differences Audit Protocol"
          metricLabel="Single-Cell Noise Floor"
          metricValue="6.91°C MDE (Honest Limit)"
          truthLayer="VERIFIED"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 09 (03:25 - 03:45 | Frames 6150 - 6750): Global South Scaling
          ------------------------------------------------------------- */}
      <Sequence from={6150} durationInFrames={600}>
        <GlobalMesh />
        <LowerThird
          category="Market Scalability"
          title="Onboarding Metropolises Across the Global South"
          metricLabel="Deployment SLA"
          metricValue="48 Hours"
          truthLayer="BUILT"
          delayFrames={15}
        />
      </Sequence>

      {/* -------------------------------------------------------------
          SCENE 10 (03:45 - 04:00 | Frames 6750 - 7200): Grand Finale & CTA
          ------------------------------------------------------------- */}
      <Sequence from={6750} durationInFrames={450}>
        <BrandClimax />
      </Sequence>
    </div>
  );
};

export const RemotionVideo = () => {
  return (
    <Composition
      id="ClimoraLaunch"
      component={ClimoraLaunchVideo}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={3840}
      height={2160}
    />
  );
};
