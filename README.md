# 🌿 Folia

Controle pessoal de investimentos com integração ao Sulfur.io.

## Stack

- **Frontend:** Streamlit
- **Backend:** Python + SQLite
- **Dados:** Yahoo Finance (via yfinance) + API pública do Sulfur.io
- **Bot:** Telegram (consultor financeiro)

## Funcionalidades

- 📊 **Dashboard** — posição atual, distribuição por ativo, gráfico de pizza
- 🔬 **Backtest** — simulação histórica de carteiras com até 3 estratégias + benchmarks (S&P 500, Ibovespa, NASDAQ)
- 🧮 **Simulador** — juros compostos com aporte mensal
- 📋 **Histórico** — registro de todas as operações
- 📈 **Evolução** — gráfico de evolução temporal da carteira
- 🤖 **Bot Telegram** — consultor financeiro que lê a carteira e consulta Sulfur pra métricas de valuation

## Como rodar localmente

```bash
pip install streamlit pandas yfinance plotly python-telegram-bot requests
streamlit run app.py
```

App abre em `http://localhost:8501`.

## Como rodar o bot

```bash
python bot.py
```

Bot responde comandos no Telegram (`/start`, `/carteira`, `/analisar TICKER`, etc).

## Integração com Sulfur.io

O bot e o backtest consultam a API pública do Sulfur.io para métricas de valuation:
- Preço atual
- Variação %
- Máx/mín 52 semanas
- Setor
- Métricas de valuation (P/L, P/VP, ROE, etc) — quando disponíveis

Endpoint: `https://screener-production-4f58.up.railway.app/api/asset/{TICKER}`

## Estrutura

```
folia/
├── app.py                # App Streamlit principal
├── folia.db              # Banco SQLite (local, não comitado)
├── .gitignore
└── README.md
```

## Configuração

A senha do app é definida em `SENHA_APP` no topo de `app.py` (padrão: `vimiar2705`).

O token do bot do Telegram é definido em `TOKEN` no topo de `bot.py`.

## Deploy

Feito via [Streamlit Community Cloud](https://streamlit.io/cloud). Secrets ficam em `.streamlit/secrets.toml` (não comitado).

---

🌿 **Folia** — feito pra vc, pelo vc.
