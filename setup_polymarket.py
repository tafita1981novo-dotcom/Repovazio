#!/usr/bin/env python3
"""
GRAVIA SETUP — Gera credenciais Polymarket sem precisar do site
Roda 1x na sua maquina: python3 setup_polymarket.py
"""
import subprocess, sys

# Instala dependencia
subprocess.check_call([sys.executable,"-m","pip","install","py-clob-client","web3","--quiet"])

from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from eth_account import Account
from web3 import Web3

print("=" * 60)
print("GRAVIA SETUP — Polymarket API Key Generator")
print("Sem site, sem VPN, funciona do Brasil")
print("=" * 60)

print("""
ANTES DE COMECAR:
1. Instale MetaMask: https://metamask.io (funciona no Brasil)
2. Crie uma carteira NOVA e dedicada para o bot
3. Anote as 12 palavras seed em papel fisico
4. Va em: MetaMask > Account Details > Export Private Key
5. Cole abaixo quando pedido
""")

pk = input("Cole sua PRIVATE KEY MetaMask (0x...): ").strip()
if not pk.startswith("0x") or len(pk) != 66:
    print("Formato invalido. Deve comecar com 0x e ter 64 caracteres hex.")
    sys.exit(1)

# Mostra endereco da wallet
acct = Account.from_key(pk)
addr = acct.address
print(f"\nEndereco da wallet: {addr}")

# Verifica saldo USDC na Polygon
print("\nVerificando saldo na Polygon...")
USDC_ADDR = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"}
]
rpcs = ["https://polygon-rpc.com","https://rpc.ankr.com/polygon","https://rpc-mainnet.maticvigil.com"]
usdc_saldo = 0
matic_saldo = 0
for rpc in rpcs:
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout":5}))
        if not w3.is_connected(): continue
        matic_saldo = float(w3.from_wei(w3.eth.get_balance(addr), "ether"))
        usdc = w3.eth.contract(address=USDC_ADDR, abi=ERC20_ABI)
        usdc_saldo = usdc.functions.balanceOf(addr).call() / 1e6
        print(f"  MATIC: {matic_saldo:.4f} (precisa >0.01 para gas)")
        print(f"  USDC:  ${usdc_saldo:.2f} (recomendado $50+)")
        break
    except: continue

if usdc_saldo < 5:
    print("""
ATENCAO: USDC insuficiente.

Como obter USDC na Polygon:
  1. Binance.com/pt-BR -> compra USDC
  2. Saque -> rede Polygon -> seu endereco acima
  3. Aguarda 5 min -> roda este script novamente

MATIC para gas:
  1. Binance -> compra MATIC
  2. Saque -> rede Polygon -> mesmo endereco
  3. Precisa apenas 0.01 MATIC ($0.01)
""")
    continuar = input("Continuar mesmo assim para criar as chaves API? (s/n): ")
    if continuar.lower() != "s":
        sys.exit(0)

# Cria API Key via CLOB (sem site, sem VPN)
print("\nCriando API credentials no Polymarket...")
client = ClobClient(
    host="https://clob.polymarket.com",
    key=pk,
    chain_id=POLYGON
)
try:
    creds = client.create_api_key()
    print("\n" + "=" * 60)
    print("SUCESSO! Adicione estes 5 secrets no GitHub:")
    print("github.com/tafita81/Repovazio -> Settings -> Secrets -> Actions")
    print("=" * 60)
    print(f"\nPOLY_API_KEY      = {creds.api_key}")
    print(f"POLY_SECRET       = {creds.api_secret}")
    print(f"POLY_PASSPHRASE   = {creds.api_passphrase}")
    print(f"POLY_PRIVATE_KEY  = {pk}")
    print(f"POLY_TRADING_LIVE = true")
    print("=" * 60)
    print("\nApos adicionar os 5 secrets, o bot comeca a operar em ate 5 minutos.")
    print(f"Dashboard: https://tafita81.github.io/gravia-bot/")
except Exception as e:
    print(f"\nErro ao criar API key: {e}")
    if "400" in str(e):
        print("-> Wallet sem historico no Polymarket. Solucao:")
        print("   1. Acesse polymarket.com com VPN (1.1.1.1 WARP, gratis)")
        print("   2. Conecte sua wallet MetaMask")
        print("   3. Faca qualquer interacao (nao precisa depositar)")
        print("   4. Rode este script novamente")
