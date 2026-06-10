Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FlowIQ - Build iOS para App Store" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Vai para a pasta do projeto
Write-Host "`n[1/4] Entrando em D:\FlowIQ..." -ForegroundColor Yellow
Set-Location "D:\FlowIQ"

# 2. Baixa o icone correto do GitHub
Write-Host "`n[2/4] Baixando icone correto..." -ForegroundColor Yellow
$iconUrl = "https://raw.githubusercontent.com/tafita81/Repovazio/main/flowiq-ss/app_icon_correct.png"
$iconPath = "assets\icon.png"
Invoke-WebRequest -Uri $iconUrl -OutFile $iconPath -UseBasicParsing
Write-Host "Icone salvo em: $iconPath" -ForegroundColor Green

# 3. Build iOS no servidor EAS (~12 min)
Write-Host "`n[3/4] Iniciando EAS Build iOS..." -ForegroundColor Yellow
Write-Host "(isso vai rodar na nuvem, aguarde ~12 minutos)" -ForegroundColor Gray
eas build --platform ios --profile production

# 4. Submit para App Store Connect
Write-Host "`n[4/4] Submetendo para App Store Connect..." -ForegroundColor Yellow
eas submit --platform ios --latest

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  PRONTO! Verifique o ASC." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
