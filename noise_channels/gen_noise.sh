#!/bin/bash
# Gerador de 1 vídeo de 1h de ruído marrom
# Uso: ./gen_1h_dbn.sh
# Tempo estimado: ~20 minutos

CANAL="${1:-dbn}"
DURACAO="${2:-3600}"

case "$CANAL" in
  dbn)      COLOR="brown"; TITULO="Deep Brown Noise - ADHD Focus Sleep Fan 1 Hour Black Screen" ;;
  wnv)      COLOR="white"; TITULO="White Noise - Sleep Fast Study Baby 1 Hour Black Screen" ;;
  adhd)     COLOR="brown"; TITULO="ADHD Focus Brown Noise - Hyperfocus Sleep 1 Hour Black Screen" ;;
  tinnitus) COLOR="pink";  TITULO="Tinnitus Relief White Pink Noise - Sleep Ear Ringing 1 Hour" ;;
  bsn)      COLOR="white"; TITULO="Baby Sleep White Noise - Newborn Colic Relief 1 Hour Black Screen" ;;
  pink)     COLOR="pink";  TITULO="Pure Pink Noise - Deep Sleep Memory Science 1 Hour Black Screen" ;;
  *)        echo "Canal inválido: $CANAL"; exit 1 ;;
esac

OUTPUT="${CANAL}_${DURACAO}s.mp4"
echo "Gerando: $OUTPUT"
echo "Título: $TITULO"
echo "Ruído: $COLOR | Duração: ${DURACAO}s"

ffmpeg -y \
  -f lavfi -i "color=color=black:size=1920x1080:rate=30:duration=${DURACAO}" \
  -f lavfi -i "anoisesrc=color=${COLOR}:amplitude=0.15:sample_rate=44100:duration=${DURACAO}" \
  -c:v libx264 -preset ultrafast -crf 30 \
  -pix_fmt yuv420p -c:a aac -b:a 128k -ar 44100 \
  -t ${DURACAO} -movflags +faststart \
  "$OUTPUT"

SIZE=$(du -h "$OUTPUT" | cut -f1)
echo "✅ Gerado: $OUTPUT ($SIZE)"
echo "Próximo passo: fazer upload para YouTube com título:"
echo "  $TITULO"
