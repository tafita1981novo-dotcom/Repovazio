import React from "react";
import { useCurrentFrame, spring, interpolate, useVideoConfig } from "remotion";

export const LowerThird: React.FC<{
  title?: string;
  subtitle?: string;
  startFrame?: number;
  episode?: string;
}> = ({ title = "psicologia.doc", subtitle = "@psidanielacoelho", startFrame = 0, episode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame: frame - startFrame,
    config: { damping: 16, stiffness: 200 },
  });

  const x = interpolate(progress, [0, 1], [-300, 0]);
  const opacity = interpolate(progress, [0, 0.3, 1], [0, 1, 1]);

  return (
    <div style={{
      position: "absolute",
      bottom: 80,
      left: 0, right: 0,
      display: "flex",
      justifyContent: "center",
      transform: `translateX(${x}px)`,
      opacity,
    }}>
      <div style={{
        background: "rgba(6,6,15,0.85)",
        backdropFilter: "blur(12px)",
        borderLeft: "4px solid #7C3AED",
        padding: "12px 24px",
        borderRadius: "0 12px 12px 0",
        display: "flex",
        alignItems: "center",
        gap: 12,
        minWidth: 200,
      }}>
        {/* ψ logo */}
        <div style={{
          width: 36, height: 36,
          background: "linear-gradient(135deg, #7C3AED, #E11D48)",
          borderRadius: "50%",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "20px", color: "#fff", fontFamily: "Georgia, serif",
          flexShrink: 0,
        }}>ψ</div>

        <div>
          <div style={{
            color: "#ffffff", fontSize: "18px", fontWeight: 700,
            fontFamily: "'DM Sans', sans-serif", letterSpacing: "0.05em",
          }}>
            {title}
          </div>
          <div style={{
            color: "#94a3b8", fontSize: "13px", fontWeight: 400,
            fontFamily: "'DM Sans', sans-serif",
          }}>
            {subtitle}
            {episode && <span style={{ color: "#7C3AED", marginLeft: 8 }}>{episode}</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LowerThird;
