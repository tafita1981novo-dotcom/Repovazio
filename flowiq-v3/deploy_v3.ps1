# ============================================
#   FlowIQ v3 - Deploy completo (Build 3)
#   Icone FLOWIQ + bgs 4K + audio premium
# ============================================
$ErrorActionPreference = "Stop"
$T = $env:GH_TOKEN
if (-not $T) { Write-Host "ERRO: defina `$env:GH_TOKEN antes de rodar" -ForegroundColor Red; exit 1 }
$H = @{ Authorization = "token $T" }
$RAW = "https://raw.githubusercontent.com/tafita81/Repovazio/main"

Set-Location "D:\FlowIQ"
Write-Host "`n[1/5] Icone FLOWIQ novo..." -ForegroundColor Yellow
Invoke-WebRequest -Headers $H "$RAW/flowiq-v3/icon_1024.png" -OutFile "assets\icon.png" -UseBasicParsing

Write-Host "[2/5] Backgrounds 4K (5 novos)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "assets\backgrounds" | Out-Null
$bgs = @("bg_focus","bg_logic","bg_math","bg_speed","bg_iq")
foreach ($b in $bgs) {
  foreach ($s in @("2x","3x")) {
    Invoke-WebRequest -Headers $H "$RAW/flowiq-v3/backgrounds/$b@$s.jpg" -OutFile "assets\backgrounds\$b@$s.jpg" -UseBasicParsing
  }
}
# bgs v2 que permanecem (memory, heroes)
$bgs2 = @("bg_memory","onboarding_hero","paywall_hero")
foreach ($b in $bgs2) {
  foreach ($s in @("2x","3x")) {
    Invoke-WebRequest -Headers $H "$RAW/flowiq-v2/backgrounds/$b@$s.jpg" -OutFile "assets\backgrounds\$b@$s.jpg" -UseBasicParsing
  }
}

Write-Host "[3/5] Audio premium (7 arquivos)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "assets\audio" | Out-Null
$auds = @("music_menu_loop","sfx_tap","sfx_correct","sfx_wrong","sfx_combo","sfx_levelup","sfx_victory")
foreach ($a in $auds) {
  Invoke-WebRequest -Headers $H "$RAW/flowiq-v2/audio/$a.m4a" -OutFile "assets\audio\$a.m4a" -UseBasicParsing
}
New-Item -ItemType Directory -Force -Path "src" | Out-Null
Invoke-WebRequest -Headers $H "$RAW/flowiq-v2/src/SoundManager.ts" -OutFile "src\SoundManager.ts" -UseBasicParsing
Invoke-WebRequest -Headers $H "$RAW/flowiq-v2/src/Theme.ts" -OutFile "src\Theme.ts" -UseBasicParsing

Write-Host "[4/5] buildNumber -> 3..." -ForegroundColor Yellow
$app = Get-Content "app.json" -Raw | ConvertFrom-Json
$app.expo.ios | Add-Member -NotePropertyName buildNumber -NotePropertyValue "3" -Force
$app | ConvertTo-Json -Depth 32 | Set-Content "app.json" -Encoding UTF8

Write-Host "[5/5] EAS Build + Submit (aguarde ~15 min)..." -ForegroundColor Yellow
$env:EAS_SKIP_AUTO_FINGERPRINT = "1"
eas build --platform ios --profile production --non-interactive
eas submit --platform ios --latest --non-interactive

Write-Host "`n=== PRONTO! Build 3 enviado ao App Store Connect ===" -ForegroundColor Green
Write-Host "Aguarde ~10 min e selecione o Build 3 na versao 1.0 do ASC." -ForegroundColor Green
