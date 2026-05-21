import React from "react";
import { AbsoluteFill, Audio, useCurrentFrame, interpolate, spring, useVideoConfig, staticFile } from "remotion";
import { Background } from "../components/Background";
import { AnimatedTextGroup } from "../components/AnimatedText";
import { CharacterCard } from "../components/CharacterCard";
import { LowerThird } from "../components/LowerThird";
import { ProgressBar, CTAEmojis } from "../components/ProgressBar";

// Definição dos grupos semânticos
// Esses props vêm do script Python via --props JSON
export interface PsychShortProps {
  videoId: number;
  title: string;
  audioUrl: string;
  // Grupos de texto com timing
  groups: Array<{
    text: string;
    type: "GANCHO" | "IMPACTO" | "REVELACAO" | "CHORO" | "PAUSA" | "CTA" | "NORMAL";
    startFrame: number;
  }>;
  // Imagens com timing (1 por frase)
  images: Array<{
    url: string;
    startFrame: number;
    character: "daniela" | "sara" | "marcos" | "ana" | "julia";
  }>;
  seriesSlug?: string;
  epNumber?: number;
}

// Transição de imagem com parallax + ken burns avançado
const ImageScene: React.FC<{
  src: string;
  character: string;
  startFrame: number;
  endFrame: number;
  fps: number;
}> = ({ src, character, startFrame, endFrame, fps }) => {
  const frame = useCurrentFrame();
  if (frame < startFrame || frame > endFrame + 30) return null;
  
  const duration = endFrame - startFrame;
  const t = frame - startFrame;
  
  // Entrada suave
  const enterProgress = spring({ fps, frame: t, config: { damping: 18, stiffness: 150 } });
  // Saída suave
  const exitOpacity = interpolate(frame, [endFrame - 10, endFrame + 20], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  
  const opacity = enterProgress * exitOpacity;
  const scale = interpolate(t, [0, duration], [1.0, 1.08]); // Ken Burns
  const y = interpolate(t, [0, duration], [0, -8]); // Parallax sutil
  
  return (
    <div style={{
      position: "absolute", inset: 0, opacity,
      display: "flex", alignItems: "flex-end", justifyContent: "center",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `url(${src})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        transform: `scale(${scale}) translateY(${y}px)`,
      }} />
      {/* Gradiente escurecendo a base para o texto */}
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(to top, rgba(6,6,15,0.95) 0%, rgba(6,6,15,0.4) 40%, rgba(6,6,15,0.2) 100%)",
      }} />
    </div>
  );
};

// Detector do tipo de grupo atual
const getCurrentPalette = (groups: PsychShortProps["groups"], frame: number) => {
  let current = "NORMAL";
  for (const g of groups) {
    if (frame >= g.startFrame) current = g.type;
  }
  return current as any;
};

// CTA indicator - pulsing bell
const CTAIndicator: React.FC<{ startFrame: number }> = ({ startFrame }) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;
  if (t < 0) return null;
  
  const pulse = Math.sin(t / 15) * 0.15 + 1;
  const opacity = interpolate(t, [0, 15, 100], [0, 1, 1], { extrapolateRight: "clamp" });
  
  return (
    <div style={{
      position: "absolute", top: 28, right: 24,
      display: "flex", alignItems: "center", gap: 8,
      opacity,
    }}>
      <div style={{
        background: "rgba(245,158,11,0.2)",
        border: "2px solid #F59E0B",
        borderRadius: 24, padding: "6px 16px",
        display: "flex", alignItems: "center", gap: 6,
        transform: `scale(${pulse})`,
      }}>
        <span style={{ fontSize: "18px" }}>🔔</span>
        <span style={{
          color: "#F59E0B", fontSize: "14px", fontWeight: 700,
          fontFamily: "'DM Sans', sans-serif",
        }}>SALVA</span>
      </div>
    </div>
  );
};

export const PsychShort: React.FC<PsychShortProps> = ({
  videoId,
  title,
  audioUrl,
  groups,
  images,
  seriesSlug,
  epNumber,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  
  const currentPalette = getCurrentPalette(groups, frame) as any;
  const ctaGroup = groups.find(g => g.type === "CTA");
  const ctaStart = ctaGroup?.startFrame ?? durationInFrames - 90;
  
  // Imagem atual
  let currentImage = images[0];
  for (const img of images) {
    if (frame >= img.startFrame) currentImage = img;
  }

  // Intro: logo ψ anima nos primeiros 20 frames
  const introOpacity = interpolate(frame, [0, 15, 30], [0, 1, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#06060F", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Background animado */}
      <Background palette={currentPalette} />

      {/* Imagens com Ken Burns + parallax */}
      {images.map((img, i) => {
        const nextStart = images[i + 1]?.startFrame ?? durationInFrames;
        return (
          <ImageScene
            key={i}
            src={img.url}
            character={img.character}
            startFrame={img.startFrame}
            endFrame={nextStart}
            fps={fps}
          />
        );
      })}

      {/* Intro ψ logo */}
      {frame < 30 && (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
          opacity: introOpacity, zIndex: 50,
        }}>
          <div style={{
            fontSize: "120px", color: "#7C3AED",
            fontFamily: "Georgia, serif",
            textShadow: "0 0 60px #7C3AED88",
          }}>ψ</div>
        </div>
      )}

      {/* Grupos de texto animados */}
      <div style={{
        position: "absolute",
        bottom: "22%",
        left: 0, right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
        padding: "0 24px",
        zIndex: 10,
      }}>
        {groups.map((group, i) => {
          const groupEnd = groups[i + 1]?.startFrame ?? durationInFrames;
          const isVisible = frame >= group.startFrame && frame < groupEnd + 60;
          if (!isVisible) return null;
          return <AnimatedTextGroup key={i} group={group} />;
        })}
      </div>

      {/* Progress bar */}
      <ProgressBar color={currentPalette === "CTA" ? "#F59E0B" : "#7C3AED"} />

      {/* Lower third */}
      <LowerThird
        startFrame={30}
        subtitle="@psidanielacoelho"
        episode={seriesSlug ? `${seriesSlug.toUpperCase()} E${String(epNumber || 1).padStart(2, "0")}` : undefined}
      />

      {/* CTA indicator */}
      {ctaGroup && <CTAIndicator startFrame={ctaStart} />}

      {/* Emojis flutuantes no CTA */}
      {ctaGroup && <CTAEmojis startFrame={ctaStart} />}

      {/* Áudio */}
      {audioUrl && (
        <Audio src={audioUrl} />
      )}
    </AbsoluteFill>
  );
};

export default PsychShort;
