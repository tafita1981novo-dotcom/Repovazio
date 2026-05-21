import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

const PALETTES = {
  IMPACTO:    { from: "#06060F", via: "#1a0a2e", accent: "#7C3AED" },
  REVELACAO:  { from: "#06060F", via: "#1a0820", accent: "#E11D48" },
  GANCHO:     { from: "#06060F", via: "#0a1020", accent: "#2563EB" },
  CHORO:      { from: "#06060F", via: "#1a1025", accent: "#8B5CF6" },
  NORMAL:     { from: "#06060F", via: "#0d0d20", accent: "#7C3AED" },
  CTA:        { from: "#06060F", via: "#1a1030", accent: "#F59E0B" },
};

const PsiParticle: React.FC<{ x: number; delay: number; size: number }> = ({ x, delay, size }) => {
  const frame = useCurrentFrame();
  const t = (frame + delay) % 120;
  const y = interpolate(t, [0, 120], [108, -10], { extrapolateRight: "clamp" });
  const opacity = interpolate(t, [0, 20, 90, 120], [0, 0.3, 0.3, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{
      position: "absolute", left: `${x}%`, top: `${y}%`,
      fontSize: size, color: "#7C3AED", opacity,
      fontFamily: "Georgia, serif", userSelect: "none",
    }}>ψ</div>
  );
};

export const Background: React.FC<{ palette?: keyof typeof PALETTES }> = ({ palette = "NORMAL" }) => {
  const frame = useCurrentFrame();
  const p = PALETTES[palette];
  const pulse = interpolate(Math.sin(frame / 30), [-1, 1], [0, 1]);
  const gradientPos = 40 + pulse * 20;

  return (
    <div style={{
      position: "absolute", width: "100%", height: "100%",
      background: `radial-gradient(ellipse at 50% ${gradientPos}%, ${p.via} 0%, ${p.from} 70%)`,
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", width: "100%", height: "100%",
        backgroundImage: `linear-gradient(rgba(124,58,237,0.04) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(124,58,237,0.04) 1px, transparent 1px)`,
        backgroundSize: "40px 40px",
      }} />
      <PsiParticle x={10} delay={0}   size="20px" />
      <PsiParticle x={25} delay={30}  size="14px" />
      <PsiParticle x={60} delay={15}  size="18px" />
      <PsiParticle x={75} delay={45}  size="16px" />
      <PsiParticle x={88} delay={20}  size="22px" />
      <PsiParticle x={40} delay={60}  size="12px" />
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, height: "3px",
        background: `linear-gradient(90deg, transparent, ${p.accent}, transparent)`,
      }} />
    </div>
  );
};

export default Background;
