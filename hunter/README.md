# Hunter — Fatia 1 (nucleo de qualificacao)

Qualifica oportunidades de freela em duas camadas e gera a notificacao Telegram.
Esta fatia roda local, contra um JSON de entrada. Nao integra APIs de plataforma
nem envia Telegram ainda (isso e Fatia 2 e 3).

## Como funciona
- **Camada 1 (`filters.py`)** — cortes eliminatorios em Python puro (stack, prazo, rate).
  Roda primeiro e de graca. O que e cortado aqui nunca chama a Claude API.
- **Camada 2 (`scoring.py` + `claude_client.py`)** — scoring qualitativo via Claude,
  so para o que sobreviveu. Avalia clareza de escopo e a excecao BRL excepcional.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # preencher CLAUDE_API_KEY
```

## Rodar

Modo seguro (só mostra as notificações no terminal, não envia):
```bash
python -m src.main tests/fixtures/briefings.json --dry-run
```

Modo real (envia de verdade no Telegram — precisa das credenciais no .env):
```bash
python -m src.main tests/fixtures/briefings.json
```

## Testes
```bash
pytest --cov=src
```
Os testes mockam a Claude API — rodam de graca e deterministicos.
