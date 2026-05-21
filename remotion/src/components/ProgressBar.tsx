import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

export const ProgressBar: React.FC<{ color?: string }> = ({ color = "#7C3AED" }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = frame / durationInFrames;
  const width = interpolate(progress, [0, 1], [0, 100]);

  return (
    <div style={{
      position: "absolute", top: 0, left: 0, right: 0, height: "4px",
      background: "rgba(255,255,255,0.1)",
      zIndex: 100,
    }}>
      <div style={{
        height: "100%", width: `${width}%`,
        background: `linear-gradient(90deg, #7C3AED, ${color === "#7C3AED" ? "#E11D48" : color})`,
        boxShadow: `0 0 8px ${color}88`,
        transition: "width 0.1s",
      }} />
    </div>
  );
};

// CTAEmojis — emojis flutuando no CTA
export const CTAEmojis: React.FC<{ startFrame: number }> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const emojis = ["💾", "🔔", "❤️", "💜", "✨"];

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {emojis.map((emoji, i) => {
        const t = frame - startFrame - i * 8;
        if (t < 0) return null;
        const y = interpolate(t, [0, 90], [0, -120], { extrapolateRight: "clamp" });
        const x = (i - 2) * 40;
        const opacity = interpolate(t, [0, 10, 70, 90], [0, 1, 1, 0], { extrapolateRight: "clamp" });
        const scale = interpolate(t, [0, 15, 90], [0.3, 1.3, 1], { extrapolateRight: "clamp" });
        return (
          <div key={i} style={{
            position: "absolute",
            bottom: "30%",
            left: "50%",
            transform: `translate(calc(-50% + ${x}px), ${y}px) scale(${scale})`,
            opacity, fontSize: "36px",
          }}>
            {emoji}
          </div>
        );
      })}
    </div>
  );
};

export default ProgressBar;
