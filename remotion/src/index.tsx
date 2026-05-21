import React from "react";
import { Composition } from "remotion";
import { PsychShort, PsychShortProps } from "./compositions/PsychShort";

// Defaults para preview no Remotion Studio
const SHORT_DEFAULT_PROPS: PsychShortProps = {
  videoId: 683,
  title: "Narcisismo Encoberto S01",
  audioUrl: "",
  groups: [
    { text: "Você conhece a Laís?", type: "GANCHO", startFrame: 30 },
    { text: "Trinta e dois anos. Professora.", type: "NORMAL", startFrame: 80 },
    { text: "CHORA", type: "IMPACTO", startFrame: 130 },
    { text: "por causa de um homem que sorri quando ela chora.", type: "CHORO", startFrame: 165 },
    { text: "Isso tem NOME.", type: "REVELACAO", startFrame: 270 },
    { text: "No vídeo completo eu mostro o sinal mais PERIGOSO.", type: "NORMAL", startFrame: 340 },
    { text: "SALVA agora para não perder. 💾🔔", type: "CTA", startFrame: 470 },
  ],
  images: [
    { url: "", startFrame: 30, character: "daniela" },
    { url: "", startFrame: 130, character: "marcos" },
    { url: "", startFrame: 270, character: "ana" },
    { url: "", startFrame: 400, character: "daniela" },
  ],
  seriesSlug: "narcisismo",
  epNumber: 1,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Short 9:16 — 58 segundos a 30fps = 1740 frames */}
      <Composition
        id="PsychShort"
        component={PsychShort}
        durationInFrames={1740}
        fps={30}
        width={576}
        height={1024}
        defaultProps={SHORT_DEFAULT_PROPS}
      />
    </>
  );
};

export default RemotionRoot;
