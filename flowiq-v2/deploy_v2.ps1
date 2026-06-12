# FlowIQ v2 — Deploy completo (assets premium + Build 3 + Submit)
# Rodar em D:\FlowIQ:  irm https://raw.githubusercontent.com/tafita81/Repovazio/main/flowiq-v2/deploy_v2.ps1 | iex
$ErrorActionPreference = "Stop"
Set-Location D:\FlowIQ
$RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main/flowiq-v2"

Write-Host "`n[1/5] Baixando assets premium..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path assets\audio, assets\backgrounds, src | Out-Null

$audio = @("sfx_tap","sfx_correct","sfx_wrong","sfx_combo","sfx_levelup","sfx_victory","music_menu_loop")
foreach ($a in $audio) { Invoke-WebRequest "$RAW/audio/$a.m4a" -OutFile "assets\audio\$a.m4a" }

$bgs = @("paywall_hero","onboarding_hero","bg_memory","bg_focus","bg_logic","bg_math","bg_speed","bg_iq")
foreach ($b in $bgs) {
  Invoke-WebRequest "$RAW/backgrounds/$b@3x.jpg" -OutFile "assets\backgrounds\$b@3x.jpg"
  Invoke-WebRequest "$RAW/backgrounds/$b@2x.jpg" -OutFile "assets\backgrounds\$b@2x.jpg"
  Copy-Item "assets\backgrounds\$b@2x.jpg" "assets\backgrounds\$b.jpg" -Force  # base fallback
}
Invoke-WebRequest "$RAW/src/SoundManager.ts" -OutFile "src\SoundManager.ts"
Invoke-WebRequest "$RAW/src/Theme.ts" -OutFile "src\Theme.ts"
Write-Host "  23 assets + 2 modulos OK" -ForegroundColor Green

Write-Host "`n[2/5] Icone correto..." -ForegroundColor Cyan
Invoke-WebRequest "https://raw.githubusercontent.com/tafita81/Repovazio/main/flowiq-icon-correct.png" -OutFile "assets\icon.png"

Write-Host "`n[3/5] Verificando app.json (buildNumber=3)..." -ForegroundColor Cyan
$app = Get-Content app.json -Raw | ConvertFrom-Json
if ($app.expo.ios.buildNumber -ne "3") {
  $app.expo.ios.buildNumber = "3"
  $app | ConvertTo-Json -Depth 20 | Set-Content app.json -Encoding UTF8
  Write-Host "  buildNumber -> 3" -ForegroundColor Yellow
} else { Write-Host "  buildNumber ja e 3" -ForegroundColor Green }

Write-Host "`n[4/5] EAS Build (producao iOS)..." -ForegroundColor Cyan
$env:EAS_SKIP_AUTO_FINGERPRINT = "1"
eas build --platform ios --profile production --non-interactive

Write-Host "`n[5/5] Submit para App Store..." -ForegroundColor Cyan
eas submit --platform ios --latest --non-interactive

Write-Host "`nDEPLOY COMPLETO! Build 3 chegara no ASC em ~10 min." -ForegroundColor Green
Write-Host "Proximo: ASC > Versao 1.0 > trocar Build 2 -> 3 > vincular IAPs > Enviar para revisao" -ForegroundColor Yellow
