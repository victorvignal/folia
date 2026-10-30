"""Web app de controle de investimentos para o Victor.
Stack: Streamlit + SQLite + yfinance.
Funcionalidades: registro de operacoes, dashboard com cotacao automatica, simulador.
"""
import os
import streamlit as st
import sqlite3
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px

# ============================================================================
# CONFIG
# ============================================================================
# Banco Supabase (compartilhado entre app local, app online e bot)
SUPABASE_URL = "https://rayjujplldxfckwjcmdq.supabase.co"
# lê credenciais do secrets do streamlit (online) ou fallback hardcoded (local)
try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

SENHA_APP = "vimiar2705"  # mude depois se quiser
TITULO_APP = "Folia — Investimentos"

st.set_page_config(
    page_title=TITULO_APP,
    page_icon="💰",
    layout="wide",
)

# tema escuro customizado — estilo XP Investimentos
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    /* ===== BASE ===== */
    .stApp {
        background: linear-gradient(180deg, #0a1628 0%, #0d1b2e 100%);
        color: #e8eef7;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #ffffff !important;
    }
    h1 { font-size: 28px !important; }
    h2 { font-size: 22px !important; }
    h3 { font-size: 18px !important; }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #061224 100%);
        border-right: 1px solid #1e2a44;
    }
    [data-testid="stSidebarNav"] { padding-top: 1rem; }
    [data-testid="stSidebar"] h1 {
        font-size: 18px !important;
        padding: 0 1rem;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] label {
        color: #8fa3c7 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }

    /* ===== MÉTRICAS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #142844 0%, #0f2038 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #1e3a5f;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,50,120,0.4);
        border-color: #2962ff;
    }
    [data-testid="stMetric"] label {
        color: #8fa3c7 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }

    /* ===== CARDS (st.container, st.dataframe) ===== */
    [data-testid="stDataFrame"] {
        background: #142844;
        border-radius: 12px;
        border: 1px solid #1e3a5f;
        padding: 8px;
    }

    /* ===== BOTÕES ===== */
    .stButton > button {
        background: linear-gradient(135deg, #2962ff 0%, #1e4fcc 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.15s ease;
        box-shadow: 0 1px 3px rgba(41, 98, 255, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(41, 98, 255, 0.5);
        background: linear-gradient(135deg, #4080ff 0%, #2962ff 100%);
    }
    .stButton > button:active { transform: translateY(0); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2962ff 0%, #1e4fcc 100%);
    }
    .stButton > button[kind="secondary"] {
        background: transparent;
        color: #8fa3c7;
        border: 1px solid #1e3a5f;
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #142844;
        color: #ffffff;
        border-color: #2962ff;
    }

    /* ===== INPUTS ===== */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background: #0f2038 !important;
        color: #e8eef7 !important;
        border: 1px solid #1e3a5f !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #2962ff !important;
        box-shadow: 0 0 0 3px rgba(41, 98, 255, 0.15) !important;
    }
    label {
        color: #8fa3c7 !important;
        font-weight: 500 !important;
    }

    /* ===== DIVIDER ===== */
    hr {
        border-color: #1e3a5f !important;
        margin: 1.5rem 0 !important;
    }

    /* ===== CAPTION ===== */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #8fa3c7 !important;
        font-size: 13px !important;
    }

    /* ===== INFO/WARNING/ERROR ===== */
    .stAlert {
        border-radius: 8px;
        border-left-width: 4px;
    }

    /* ===== RADIO BUTTONS (sidebar nav) ===== */
    .stRadio label {
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        transition: background 0.15s ease;
    }
    .stRadio label:hover {
        background: #142844;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# BANCO DE DADOS
# ============================================================================
# BANCO DE DADOS — Supabase (REST API)
# ============================================================================
def init_db():
    """No Supabase as tabelas são criadas via SQL Editor. Não faz nada aqui."""
    pass


def listar_operacoes():
    """Lista todas as operações ordenadas por data DESC, id DESC."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/operacoes?order=data.desc,id.desc",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    if r.status_code != 200:
        return pd.DataFrame()
    data = r.json()
    return pd.DataFrame(data)


def inserir_operacao(data, tipo, ticker, nome, quantidade, preco_unitario, observacao=""):
    """Insere operação. Retorna True se sucesso."""
    payload = {
        "data": data,
        "tipo": tipo,
        "ticker": ticker.upper().strip(),
        "nome": nome,
        "quantidade": quantidade,
        "preco_unitario": preco_unitario,
        "observacao": observacao,
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/operacoes",
        headers=SUPABASE_HEADERS,
        json=payload,
        timeout=10,
    )
    if r.status_code in (200, 201):
        # garante ticker na tabela ativos
        try:
            requests.post(
                f"{SUPABASE_URL}/rest/v1/ativos",
                headers=SUPABASE_HEADERS,
                json={"ticker": ticker.upper().strip(), "nome": nome, "moeda": None},
                timeout=5,
            )
        except Exception:
            pass
        return True
    return False


def deletar_operacao(op_id):
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/operacoes?id=eq.{op_id}",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    return r.status_code in (200, 204)


def deletar_todas_operacoes():
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/operacoes?id=gt.0",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    return r.status_code in (200, 204)


# ===== WATCHLIST =====
def adicionar_watchlist(ticker):
    """Adiciona ticker à watchlist. Retorna True se adicionou, False se já existia."""
    payload = {
        "ticker": ticker.upper().strip(),
        "adicionado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    # usa Prefer resolution=merge-duplicates pra retornar o existente ao invés de erro
    headers_dup = dict(SUPABASE_HEADERS)
    headers_dup["Prefer"] = "resolution=merge-duplicates,return=minimal"
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/watchlist",
        headers=headers_dup,
        json=payload,
        timeout=10,
    )
    return r.status_code in (200, 201)


def remover_watchlist(ticker):
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/watchlist?ticker=eq.{ticker.upper().strip()}",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    return r.status_code in (200, 204)


def listar_watchlist():
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/watchlist?order=adicionado_em.desc&select=ticker,adicionado_em",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    if r.status_code != 200:
        return pd.DataFrame()
    return pd.DataFrame(r.json())


def limpar_watchlist():
    r = requests.delete(
        f"{SUPABASE_URL}/rest/v1/watchlist?id=gt.0",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    return r.status_code in (200, 204)


def listar_tickers_ativos():
    """Retorna tickers únicos que têm operações."""
    # usa SELECT DISTINCT
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/operacoes?select=ticker,nome&order=ticker",
        headers=SUPABASE_HEADERS,
        timeout=10,
    )
    if r.status_code != 200:
        return pd.DataFrame()
    df = pd.DataFrame(r.json())
    if df.empty:
        return df
    # dedup por ticker mantendo primeiro nome
    df = df.drop_duplicates(subset=["ticker"], keep="first")
    return df.reset_index(drop=True)


# ============================================================================
# COTAÇÕES
# ============================================================================
@st.cache_data(ttl=3600)  # cache de 15 min
def cotacao_yahoo(ticker):
    """Pega cotação atual via Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        preco = float(hist["Close"].iloc[-1])
        moeda = t.info.get("currency", "USD")
        return {"preco": preco, "moeda": moeda}
    except Exception:
        return None


@st.cache_data(ttl=3600)
def cotacao_rapida(ticker):
    """Cotação completa pra tela de mercado: preço, variação, 52w high/low, nome, moeda."""
    # Yahoo precisa de .SA pra tickers brasileiros (PETR4 → PETR4.SA)
    ticker_yahoo = ticker
    if any(c.isdigit() for c in ticker) and not ticker.startswith("^"):
        # ticker brasileiro: termina em número, sem .SA nem ^
        if not ticker.endswith(".SA"):
            ticker_yahoo = ticker + ".SA"
    try:
        t = yf.Ticker(ticker_yahoo)
        hist = t.history(period="1y")
        if hist.empty or len(hist) < 2:
            return None
        preco = float(hist["Close"].iloc[-1])
        preco_ontem = float(hist["Close"].iloc[-2])
        variacao = ((preco / preco_ontem) - 1) * 100 if preco_ontem > 0 else 0
        high_52w = float(hist["High"].max())
        low_52w = float(hist["Low"].min())
        moeda = t.info.get("currency", "USD")
        nome_curto = t.info.get("shortName") or t.info.get("longName") or ticker
        return {
            "ticker": ticker,  # retorna o ticker original, n o com .SA
            "nome": nome_curto,
            "preco": preco,
            "variacao_pct": variacao,
            "52w_high": high_52w,
            "52w_low": low_52w,
            "moeda": moeda,
        }
    except Exception:
        return None


@st.cache_data(ttl=3600)
def historico_yahoo(ticker, periodo="1y"):
    """Histórico de preços pra gráfico."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=periodo)
        if hist.empty:
            return None
        return hist["Close"]
    except Exception:
        return None


@st.cache_data(ttl=3600)
def cambio_usd_brl():
    """Cotação USD/BRL."""
    try:
        t = yf.Ticker("USDBRL=X")
        hist = t.history(period="2d")
        if hist.empty:
            return 5.0
        return float(hist["Close"].iloc[-1])
    except Exception:
        return 5.0


def converter_para_brl(valor, moeda):
    if moeda == "USD" or moeda == "USDBRL":
        cambio = cambio_usd_brl()
        return valor * cambio
    return valor  # já em BRL


# ============================================================================
# CÁLCULOS
# ============================================================================
def calcular_posicao(df_ops, cotacoes, cambio):
    """Calcula posição consolidada por ticker. preco_unitario pode estar em USD (converte se necessário)."""
    if df_ops.empty:
        return pd.DataFrame()
    posicoes = []
    for ticker, grupo in df_ops.groupby("ticker"):
        nome = grupo["nome"].iloc[0] if "nome" in grupo.columns else ticker
        qtd_total = 0
        custo_total_brl = 0
        # detecta se o ticker é em USD (heurística: tem letras sem dígito, ou ^ no início)
        is_dolar = ticker.startswith("^") or (
            ticker.replace(".", "").replace("-", "").isalpha()
        )
        print(f"[DEBUG] ticker={ticker} is_dolar={is_dolar} cambio={cambio}")
        for _, op in grupo.iterrows():
            sinal = 1 if op["tipo"] == "C" else -1
            qtd_total += sinal * op["quantidade"]
            # converte preço unitário pra BRL se for USD
            preco_op = op["preco_unitario"]
            print(f"[DEBUG] op preco={preco_op} qtd={op['quantidade']}")
            if is_dolar:
                preco_op_brl = preco_op * cambio
            else:
                preco_op_brl = preco_op
            custo_total_brl += sinal * op["quantidade"] * preco_op_brl
            print(f"[DEBUG] custo parcial={custo_total_brl}")
        if qtd_total <= 0:
            continue
        # cotação atual
        if ticker in cotacoes:
            moeda = cotacoes[ticker].get("moeda", "BRL")
            preco_atual_brl = converter_para_brl(cotacoes[ticker]["preco"], moeda)
        else:
            preco_atual_brl = custo_total_brl / qtd_total if qtd_total > 0 else 0
            moeda = "BRL"
        preco_medio_brl = custo_total_brl / qtd_total if qtd_total > 0 else 0
        valor_atual = qtd_total * preco_atual_brl
        lucro = valor_atual - custo_total_brl
        rentab = (lucro / custo_total_brl * 100) if custo_total_brl > 0 else 0
        posicoes.append({
            "Ticker": ticker,
            "Nome": nome,
            "Quantidade": qtd_total,
            "Preço Médio (R$)": preco_medio_brl,
            "Preço Atual (R$)": preco_atual_brl,
            "Custo Total (R$)": custo_total_brl,
            "Valor Atual (R$)": valor_atual,
            "Lucro/Prejuízo (R$)": lucro,
            "Rentab. (%)": rentab,
        })
    return pd.DataFrame(posicoes)


# ============================================================================
# AUTENTICAÇÃO
# ============================================================================
def autenticar():
    """Tela simples de login."""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if st.session_state.autenticado:
        return True
    st.title("🔐 " + TITULO_APP)
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == SENHA_APP:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha errada")
    return False


# ============================================================================
# PÁGINAS
# ============================================================================
def pagina_dashboard(df_posicao, cotacoes_ok):
    st.title("💰 " + TITULO_APP)
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    if df_posicao.empty:
        st.info("Vc ainda não tem operações registradas. Vá em 'Registrar Operação' pra começar.")
        return

    # métricas topo
    custo_total = df_posicao["Custo Total (R$)"].sum()
    valor_atual = df_posicao["Valor Atual (R$)"].sum()
    lucro = valor_atual - custo_total
    rentab = (lucro / custo_total * 100) if custo_total > 0 else 0
    n_ativos = len(df_posicao)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Investido", f"R$ {custo_total:,.2f}")
    col2.metric("Valor Atual", f"R$ {valor_atual:,.2f}")
    delta_str = f"{lucro:+,.2f} ({rentab:+.2f}%)"
    col3.metric("Lucro/Prejuízo", f"R$ {lucro:+,.2f}", delta=rentab, delta_color="normal")
    col4.metric("Nº de Ativos", f"{n_ativos}")

    st.divider()

    # gráfico pizza
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Distribuição por ativo")
        fig = px.pie(
            df_posicao,
            values="Valor Atual (R$)",
            names="Ticker",
            hole=0.5,
            color_discrete_sequence=["#2962ff", "#00c853", "#ff9100", "#d50000", "#aa00ff", "#00b8d4", "#ffc400", "#c51162"],
        )
        fig.update_traces(
            textposition="outside",
            textinfo="percent+label",
            textfont_size=13,
            textfont_color="#e8eef7",
            marker=dict(line=dict(color="#0a1628", width=2)),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8eef7",
            font_family="Inter",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
            ),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Posição detalhada")
        # colorir lucro positivo verde, negativo vermelho
        st.dataframe(
            df_posicao.style.format({
                "Preço Médio (R$)": "R$ {:.2f}",
                "Preço Atual (R$)": "R$ {:.2f}",
                "Custo Total (R$)": "R$ {:.2f}",
                "Valor Atual (R$)": "R$ {:.2f}",
                "Lucro/Prejuízo (R$)": "R$ {:.2f}",
                "Rentab. (%)": "{:.2f}%",
                "Quantidade": "{:.4f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    if not cotacoes_ok:
        st.warning("Algumas cotações não foram obtidas (mostrando preço médio como fallback). Verifica os tickers.")


def pagina_registrar():
    st.title("➕ Registrar Operação")
    st.caption("Compra ou venda de ativo")

    with st.form("form_op"):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data", value=date.today())
            tipo = st.selectbox("Tipo", ["C", "V"], format_func=lambda x: "🟢 Compra" if x == "C" else "🔴 Venda")
            ticker = st.text_input("Ticker (ex: NTDOY, NINT34, IVVB11)").upper().strip()
        with col2:
            nome = st.text_input("Nome do ativo (opcional)")
            quantidade = st.number_input("Quantidade", min_value=0.0, step=1.0, format="%.4f")
            preco_unitario = st.number_input("Preço unitário (BRL ou USD)", min_value=0.0, step=0.01, format="%.2f",
                                              help="Se o ticker é gringo (NTDOY, EA), digite o preço em USD. O sistema converte pra R$ automaticamente.")
        observacao = st.text_input("Observação (opcional)")
        submitted = st.form_submit_button("Registrar")

        if submitted:
            if not ticker or quantidade <= 0 or preco_unitario <= 0:
                st.error("Preencha ticker, quantidade e preço unitário")
            else:
                inserir_operacao(
                    data.strftime("%Y-%m-%d"),
                    tipo,
                    ticker,
                    nome,
                    quantidade,
                    preco_unitario,
                    observacao,
                )
                st.success(f"✅ {('Compra' if tipo == 'C' else 'Venda')} de {ticker} registrada!")
                st.rerun()


def pagina_historico():
    st.title("📋 Histórico de Operações")

    df = listar_operacoes()
    if df.empty:
        st.info("Nenhuma operação registrada ainda.")
        return

    # formata pra exibição
    df_display = df.copy()
    df_display["data"] = pd.to_datetime(df_display["data"]).dt.strftime("%d/%m/%Y")
    df_display["tipo"] = df_display["tipo"].map({"C": "🟢 Compra", "V": "🔴 Venda"})
    df_display["preco_unitario"] = df_display["preco_unitario"].apply(lambda x: f"R$ {x:.2f}")
    df_display["valor_total"] = df_display.apply(
        lambda r: f"R$ {r['quantidade'] * r['preco_unitario_raw']:,.2f}" if 'preco_unitario_raw' in df_display.columns else "",
        axis=1,
    )
    # recalcula com a coluna original antes de formatar
    df_display["valor_total"] = (df["quantidade"] * df["preco_unitario"]).apply(lambda x: f"R$ {x:,.2f}")

    st.dataframe(
        df_display[["data", "tipo", "ticker", "nome", "quantidade", "preco_unitario", "valor_total", "observacao"]]
        .rename(columns={
            "data": "Data",
            "tipo": "Tipo",
            "ticker": "Ticker",
            "nome": "Nome",
            "quantidade": "Qtd",
            "preco_unitario": "Preço Unit.",
            "valor_total": "Total",
            "observacao": "Obs",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        st.subheader("Excluir uma operação")
        op_id = st.number_input("ID da operação pra excluir", min_value=0, step=1)
        if st.button("🗑️ Excluir selecionada", type="secondary"):
            if op_id > 0:
                deletar_operacao(op_id)
                st.success("Excluída!")
                st.rerun()
    with col_del2:
        st.subheader("Apagar tudo (reset)")
        st.warning("⚠️ Isso remove TODAS as operações. Use só pra começar do zero.")
        if st.button("🗑️ APAGAR TUDO", type="primary"):
            deletar_todas_operacoes()
            st.success("Tudo apagado!")
            st.rerun()


def pagina_simulador():
    st.title("🧮 Simulador de Investimentos")

    st.subheader("Simulador de Aporte Mensal")
    col1, col2, col3 = st.columns(3)
    with col1:
        aporte = st.number_input("Aporte mensal (R$)", min_value=0.0, value=200.0, step=50.0)
        meses = st.number_input("Quantos meses", min_value=1, value=60, step=12)
    with col2:
        taxa_mensal = st.number_input("Taxa de retorno mensal (%)", min_value=0.0, value=1.0, step=0.1, format="%.2f")
        imposto = st.number_input("Imposto (%)", min_value=0.0, value=0.0, step=0.1, format="%.2f")
    with col3:
        st.markdown("**Referência de taxas**")
        st.markdown("- 0.5%/mês ≈ 6% aa (conservador)")
        st.markdown("- 1.0%/mês ≈ 12% aa (mercado)")
        st.markdown("- 1.5%/mês ≈ 18% aa (agressivo)")

    taxa = taxa_mensal / 100
    valor_final_bruto = aporte * (((1 + taxa) ** meses - 1) / taxa) if taxa > 0 else aporte * meses
    imposto_valor = valor_final_bruto * (imposto / 100)
    valor_final_liq = valor_final_bruto - imposto_valor
    total_aportado = aporte * meses
    lucro = valor_final_liq - total_aportado
    rentab = (lucro / total_aportado * 100) if total_aportado > 0 else 0

    st.divider()
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Total aportado", f"R$ {total_aportado:,.2f}")
    col_b.metric("Valor final (líq.)", f"R$ {valor_final_liq:,.2f}")
    col_c.metric("Lucro", f"R$ {lucro:+,.2f}")
    col_d.metric("Rentabilidade", f"{rentab:+.2f}%")

    # gráfico de evolução mês a mês
    st.subheader("Evolução mês a mês")
    meses_list = list(range(1, meses + 1))
    evolucao = []
    saldo = 0
    for m in meses_list:
        saldo = saldo * (1 + taxa) + aporte
        evolucao.append({"Mês": m, "Valor (R$)": saldo, "Aportado": aporte * m})
    df_evol = pd.DataFrame(evolucao)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_evol["Mês"],
        y=df_evol["Valor (R$)"],
        name="Valor da carteira",
        line=dict(color="#00c853", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 200, 83, 0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=df_evol["Mês"],
        y=df_evol["Aportado"],
        name="Total aportado",
        line=dict(color="#8fa3c7", width=2, dash="dash"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,40,68,0.4)",
        font_color="#e8eef7",
        font_family="Inter",
        xaxis=dict(gridcolor="#1e3a5f", title="Mês", zeroline=False),
        yaxis=dict(gridcolor="#1e3a5f", title="R$", zeroline=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def pagina_evolucao():
    """Gráfico de evolução histórica da carteira (se houver cotações passadas)."""
    st.title("📈 Evolução da Carteira")

    df_ops = listar_operacoes()
    if df_ops.empty:
        st.info("Sem operações ainda.")
        return

    tickers = df_ops["ticker"].unique()
    st.write(f"Tickers na carteira: {', '.join(tickers)}")
    periodo = st.selectbox("Período", ["6mo", "1y", "2y", "5y", "max"], index=2)

    with st.spinner("Baixando dados históricos..."):
        evolucao_total = None
        # pra cada ticker, soma contribuição
        for ticker in tickers:
            hist = historico_yahoo(ticker, periodo)
            if hist is None:
                continue
            # calcula qtd acumulada por data
            df_t = df_ops[df_ops["ticker"] == ticker].copy()
            df_t["data"] = pd.to_datetime(df_t["data"]).dt.tz_localize(None)
            # cria serie temporal da qtd
            datas = hist.index
            # normaliza timestamps do hist pra comparar com df_t (remove timezone se tiver)
            if hasattr(datas, "tz") and datas.tz is not None:
                datas = datas.tz_localize(None)
            qtds = []
            qtd_acum = 0
            for d in datas:
                # soma compras até essa data
                compras_ate = df_t[(df_t["data"] <= d) & (df_t["tipo"] == "C")]["quantidade"].sum()
                vendas_ate = df_t[(df_t["data"] <= d) & (df_t["tipo"] == "V")]["quantidade"].sum()
                qtd_acum = compras_ate - vendas_ate
                qtds.append(qtd_acum)
            serie_ticker = hist.values * pd.Series(qtds).values
            cambio = cambio_usd_brl() if any(c.isalpha() and not c.isdigit() for c in ticker) else 1.0
            serie_ticker_brl = serie_ticker * cambio
            if evolucao_total is None:
                evolucao_total = pd.Series(serie_ticker_brl, index=datas)
            else:
                # alinha indices
                evolucao_total = evolucao_total.add(pd.Series(serie_ticker_brl, index=datas), fill_value=0)

    if evolucao_total is None or evolucao_total.empty:
        st.warning("Não foi possível baixar histórico de nenhum ticker.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=evolucao_total.index,
        y=evolucao_total.values,
        fill="tozeroy",
        fillcolor="rgba(0, 200, 83, 0.15)",
        line=dict(color="#00c853", width=2.5),
        name="Valor da carteira",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,40,68,0.4)",
        font_color="#e8eef7",
        font_family="Inter",
        xaxis=dict(gridcolor="#1e3a5f", title="Data", zeroline=False),
        yaxis=dict(gridcolor="#1e3a5f", title="Valor (R$)", zeroline=False),
        title=dict(text="Evolução do valor da carteira", font=dict(size=18, color="#ffffff")),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# BACKTEST — simulação com dados históricos reais
# ============================================================================
BENCHMARKS = {
    "S&P 500 (EUA)": "SPY",
    "Ibovespa": "BOVA11.SA",
    "NASDAQ 100": "QQQ",
    "ETF Games (ESPO)": "ESPO",
}


@st.cache_data(ttl=3600)
def historico_mensal(ticker, data_inicio, data_fim):
    """Histórico mensal de preços (primeiro pregão de cada mês)."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=data_inicio, end=data_fim)
        if hist.empty:
            return None
        if hasattr(hist.columns, "get_level_values"):
            hist.columns = hist.columns.get_level_values(0)
        # remove timezone pra ficar simples
        if hasattr(hist.index, "tz") and hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        mensal = hist["Close"].squeeze().resample("MS").first().dropna()
        return mensal
    except Exception:
        return None


def eh_ticker_dolar(ticker):
    """Detecta se ticker é em USD (não tem dígito)."""
    return not any(c.isdigit() for c in ticker)


def simular_carteira(tickers_pesos, aporte_mensal, data_inicio, data_fim):
    """Simula aporte mensal dividido entre ativos conforme pesos.
    Retorna DataFrame com evolução mês a mês + métricas.
    """
    # pega histórico de cada ticker
    precos = {}
    cambio_inicio = None
    for ticker in tickers_pesos:
        h = historico_mensal(ticker, data_inicio, data_fim)
        if h is None or h.empty:
            return None, f"Não foi possível baixar dados de {ticker}. Verifica o ticker."
        # converte pra BRL se for USD
        if eh_ticker_dolar(ticker):
            cambio = historico_mensal("USDBRL=X", data_inicio, data_fim)
            if cambio is not None and not cambio.empty:
                if hasattr(cambio.index, "tz") and cambio.index.tz is not None:
                    cambio.index = cambio.index.tz_localize(None)
                # alinhar datas
                cambio = cambio.reindex(h.index).ffill().bfill()
                precos[ticker] = h * cambio
            else:
                precos[ticker] = h
        else:
            precos[ticker] = h

    # alinhar todas as séries pelo índice de datas (meses em comum)
    datas_comuns = None
    for t, p in precos.items():
        if datas_comuns is None:
            datas_comuns = p.index
        else:
            datas_comuns = datas_comuns.intersection(p.index)
    if datas_comuns is None or len(datas_comuns) < 2:
        return None, "Período insuficiente ou sem dados sobrepostos entre os ativos."

    datas_comuns = datas_comuns.sort_values()
    for t in precos:
        precos[t] = precos[t].reindex(datas_comuns)

    # simulação
    qtd_cotas = {t: 0.0 for t in tickers_pesos}
    evolucao = []
    total_aportado = 0.0

    for i, data in enumerate(datas_comuns):
        if i == 0:
            # primeira data: compra com aporte inicial? não, apenas registra o que vai acontecer
            # pula — primeiro aporte vai pro segundo mês pra ter "preço anterior" pra calcular
            valor_carteira = 0.0
        else:
            # distribui aporte conforme pesos
            aporte_ativos = {t: aporte_mensal * tickers_pesos[t] for t in tickers_pesos}
            # compra cotas
            for t in tickers_pesos:
                preco_t = float(precos[t].iloc[i])
                if preco_t > 0:
                    qtd_cotas[t] += aporte_ativos[t] / preco_t
            total_aportado += aporte_mensal
        # valor atual da carteira
        valor_carteira = sum(
            qtd_cotas[t] * float(precos[t].iloc[i]) for t in tickers_pesos
        )
        evolucao.append({
            "data": data,
            "valor": valor_carteira,
            "aportado": total_aportado,
        })

    df = pd.DataFrame(evolucao).set_index("data")

    # métricas
    valor_final = float(df["valor"].iloc[-1])
    total_aportado_final = float(df["aportado"].iloc[-1])
    lucro = valor_final - total_aportado_final
    rentab_total = (lucro / total_aportado_final * 100) if total_aportado_final > 0 else 0
    meses = len(df)
    anos = meses / 12
    cagr = (((valor_final / total_aportado_final) ** (1 / anos)) - 1) * 100 if anos > 0 and total_aportado_final > 0 and valor_final > 0 else 0
    # drawdown máximo
    pico = df["valor"].cummax()
    drawdown = ((df["valor"] - pico) / pico * 100).min()
    # volatilidade anualizada (ignora primeiros meses com valor zero)
    retornos = df["valor"].pct_change().dropna()
    retornos = retornos[retornos != 0]  # remove divisoes por zero do inicio
    vol_anual = float(retornos.std() * (12 ** 0.5) * 100) if len(retornos) > 1 else 0

    metricas = {
        "valor_final": valor_final,
        "total_aportado": total_aportado_final,
        "lucro": lucro,
        "rentab_total_pct": rentab_total,
        "cagr_pct": cagr,
        "drawdown_max_pct": drawdown,
        "vol_anual_pct": vol_anual,
        "meses": meses,
    }
    return (df, metricas), None


def simular_benchmark(ticker, aporte_mensal, data_inicio, data_fim):
    """Simula aporte mensal em um único ativo (benchmark)."""
    return simular_carteira({ticker: 1.0}, aporte_mensal, data_inicio, data_fim)


def pagina_backtest():
    st.title("🔬 Backtest — Simulação Histórica")
    st.caption("Teste carteiras com dados REAIS do Yahoo Finance. Compare até 3 estratégias.")

    # presets rápidos
    st.subheader("1. Período e aporte")
    col1, col2, col3 = st.columns(3)
    with col1:
        data_inicio = st.date_input(
            "Data início",
            value=datetime(2020, 1, 1).date(),
            min_value=datetime(2010, 1, 1).date(),
            max_value=datetime.now().date(),
            format="DD/MM/YYYY",
        )
    with col2:
        data_fim = st.date_input(
            "Data fim",
            value=datetime.now().date(),
            min_value=datetime(2010, 1, 1).date(),
            max_value=datetime.now().date(),
            format="DD/MM/YYYY",
        )
    with col3:
        aporte_mensal = st.number_input(
            "Aporte mensal (R$)",
            min_value=0.0,
            value=500.0,
            step=100.0,
        )

    st.divider()

    # carteiras — até 3
    st.subheader("2. Carteiras (até 3)")
    n_carteiras = st.slider("Quantas carteiras comparar?", 1, 3, 2)

    carteiras = []
    nomes_default = ["Games (minha ideia)", "S&P 500 (referência)", "Mista"]
    cores = ["#2962ff", "#00c853", "#ff9100"]
    for i in range(n_carteiras):
        with st.expander(f"📁 Carteira {i+1}: {nomes_default[i]}", expanded=(i == 0)):
            nome = st.text_input("Nome da carteira", value=nomes_default[i], key=f"nome_{i}")
            # quantos ativos
            n_ativos = st.number_input(
                "Quantos ativos?",
                min_value=1, max_value=20, value=2, step=1,
                key=f"n_{i}",
            )
            tickers = []
            pesos = []
            for j in range(int(n_ativos)):
                col_t, col_p = st.columns([3, 1])
                with col_t:
                    t = st.text_input(
                        f"Ativo {j+1} (ticker)",
                        value="" if j > 0 else ("NTDOY" if i == 0 else ("SPY" if i == 1 else "QQQ")),
                        key=f"t_{i}_{j}",
                    ).upper().strip()
                with col_p:
                    p = st.number_input(
                        "%",
                        min_value=0.0, max_value=100.0,
                        value=100.0 / int(n_ativos) if j == 0 else 0.0,
                        step=5.0,
                        key=f"p_{i}_{j}",
                    )
                if t and p > 0:
                    tickers.append(t)
                    pesos.append(p)
            # valida soma = 100
            soma = sum(pesos)
            if tickers:
                if abs(soma - 100) > 0.5:
                    st.warning(f"⚠️ Pesos somam {soma:.1f}% (precisam somar 100%)")
                else:
                    st.success(f"✅ Total: {soma:.0f}%")
            tickers_pesos = {t: p / 100 for t, p in zip(tickers, pesos)}
            carteiras.append({"nome": nome, "tickers_pesos": tickers_pesos, "cor": cores[i]})

    st.divider()

    # benchmarks
    st.subheader("3. Comparar com benchmarks?")
    usar_benchmarks = st.checkbox("Adicionar benchmarks (S&P 500, Ibovespa, etc)", value=True)
    benchmarks_escolhidos = []
    if usar_benchmarks:
        cols = st.columns(len(BENCHMARKS))
        for idx, (nome, ticker) in enumerate(BENCHMARKS.items()):
            with cols[idx]:
                if st.checkbox(nome, value=(idx < 2), key=f"bench_{ticker}"):
                    benchmarks_escolhidos.append((nome, ticker))

    st.divider()

    # rodar
    if st.button("🚀 Rodar simulação", type="primary"):
        if data_inicio >= data_fim:
            st.error("Data fim deve ser depois da data início.")
            return
        carteiras_validas = [c for c in carteiras if c["tickers_pesos"]]
        if not carteiras_validas:
            st.error("Adicione pelo menos 1 carteira com ativos válidos.")
            return
        # validação dos pesos
        for c in carteiras_validas:
            soma = sum(c["tickers_pesos"].values())
            if abs(soma - 1.0) > 0.005:
                st.error(f"Carteira '{c['nome']}': pesos devem somar 100%. Atual: {soma*100:.1f}%")
                return

        resultados = {}
        with st.spinner("Baixando dados e simulando..."):
            for c in carteiras_validas:
                r, err = simular_carteira(
                    c["tickers_pesos"], aporte_mensal,
                    data_inicio.strftime("%Y-%m-%d"),
                    data_fim.strftime("%Y-%m-%d"),
                )
                if err:
                    st.error(err)
                    return
                resultados[c["nome"]] = {"df": r[0], "metricas": r[1], "cor": c["cor"]}

            for nome, ticker in benchmarks_escolhidos:
                r, err = simular_benchmark(
                    ticker, aporte_mensal,
                    data_inicio.strftime("%Y-%m-%d"),
                    data_fim.strftime("%Y-%m-%d"),
                )
                if err:
                    st.warning(f"Benchmark {nome}: {err}")
                    continue
                resultados[f"📊 {nome}"] = {"df": r[0], "metricas": r[1], "cor": "#8fa3c7"}

        # salvar em session pra rerender sem perder
        st.session_state["resultados_backtest"] = resultados

    # exibe resultados
    if "resultados_backtest" in st.session_state:
        resultados = st.session_state["resultados_backtest"]
        st.divider()
        st.subheader("📊 Resultados")

        # tabela resumo
        rows = []
        for nome, r in resultados.items():
            m = r["metricas"]
            rows.append({
                "Carteira": nome,
                "Valor Final": f"R$ {m['valor_final']:,.2f}",
                "Total Aportado": f"R$ {m['total_aportado']:,.2f}",
                "Lucro": f"R$ {m['lucro']:,.2f}",
                "Rentab. Total": f"{m['rentab_total_pct']:+.2f}%",
                "CAGR (anual)": f"{m['cagr_pct']:+.2f}%",
                "Drawdown Máx.": f"{m['drawdown_max_pct']:.2f}%",
                "Volatilidade": f"{m['vol_anual_pct']:.2f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # texto pra copiar e mandar pro TJRv2
        texto_resumo = "📊 *Resultado Backtest Folia*\n\n"
        for row in rows:
            texto_resumo += (
                f"• *{row['Carteira']}*\n"
                f"  Valor final: {row['Valor Final']}\n"
                f"  Aportado: {row['Total Aportado']}\n"
                f"  Lucro: {row['Lucro']} ({row['Rentab. Total']})\n"
                f"  CAGR: {row['CAGR (anual)']}\n"
                f"  Drawdown: {row['Drawdown Máx.']}\n"
                f"  Volatilidade: {row['Volatilidade']}\n\n"
            )
        texto_resumo += "_Manda esse texto pro @tjrv2bot e pede análise._"
        st.text_area(
            "📋 Copie e mande pro TJRv2",
            value=texto_resumo,
            height=250,
            help="Clica no campo, dá Ctrl+A pra selecionar tudo, Ctrl+C pra copiar. Cola no Telegram pro @tjrv2bot.",
        )

        # gráfico de evolução — valor absoluto
        fig = go.Figure()
        for nome, r in resultados.items():
            fig.add_trace(go.Scatter(
                x=r["df"].index,
                y=r["df"]["valor"],
                name=nome,
                line=dict(color=r["cor"], width=2.5),
                mode="lines",
            ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(20,40,68,0.4)",
            font_color="#e8eef7",
            font_family="Inter",
            xaxis=dict(gridcolor="#1e3a5f", zeroline=False),
            yaxis=dict(gridcolor="#1e3a5f", title="Valor (R$)", zeroline=False),
            title=dict(text="Evolução do patrimônio", font=dict(size=18, color="#ffffff")),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # gráfico normalizado (todos começam em 0%, melhor pra comparar performance)
        st.subheader("Rentabilidade acumulada (base 0)")
        fig2 = go.Figure()
        for nome, r in resultados.items():
            serie = (r["df"]["valor"] / r["df"]["valor"].iloc[0] - 1) * 100
            fig2.add_trace(go.Scatter(
                x=r["df"].index,
                y=serie,
                name=nome,
                line=dict(color=r["cor"], width=2.5),
            ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(20,40,68,0.4)",
            font_color="#e8eef7",
            font_family="Inter",
            xaxis=dict(gridcolor="#1e3a5f", zeroline=False),
            yaxis=dict(gridcolor="#1e3a5f", title="Rentabilidade (%)", zeroline=False),
            title=dict(text="Rentabilidade acumulada (todos começam em 0%)", font=dict(size=16, color="#ffffff")),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
            height=450,
        )
        st.plotly_chart(fig2, use_container_width=True)

        # gráfico drawdown
        st.subheader("Drawdown ao longo do tempo (quedas desde o pico)")
        fig3 = go.Figure()
        for nome, r in resultados.items():
            pico = r["df"]["valor"].cummax()
            dd = (r["df"]["valor"] - pico) / pico * 100
            fig3.add_trace(go.Scatter(
                x=r["df"].index,
                y=dd,
                name=nome,
                line=dict(color=r["cor"], width=2),
                fill="tozeroy",
                fillcolor="rgba(213, 0, 0, 0.05)",
            ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(20,40,68,0.4)",
            font_color="#e8eef7",
            font_family="Inter",
            xaxis=dict(gridcolor="#1e3a5f", zeroline=False),
            yaxis=dict(gridcolor="#1e3a5f", title="Drawdown (%)", zeroline=False),
            title=dict(text="Drawdown (quanto caiu do pico)", font=dict(size=16, color="#ffffff")),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)

        # interpretação
        st.divider()
        st.subheader("💡 Como ler")
        st.markdown("""
        - **Rentabilidade Total**: lucro/prejuízo em % sobre tudo q vc aportou
        - **CAGR**: rentabilidade anualizada (média composta por ano). É a melhor métrica pra comparar investimentos de prazos diferentes
        - **Drawdown Máximo**: a maior queda q a carteira teve do pico até o vale. Mostra o sofrimento. -20% = em algum momento vc viu a carteira valer 20% menos q o melhor momento
        - **Volatilidade**: o quanto oscila. Maior = mais arriscado. S&P 500 historicamente ~15%, ativos individuais pode ser 30-50%
        - **Rentabilidade passada não garante futura**, mas ajuda a entender o comportamento de uma estratégia
        """)


# ============================================================================
# MERCADO — lista simples de ações
# ============================================================================
# benchmarks clássicos que sempre aparecem
BENCHMARKS_MERCADO = [
    ("PETR4", "Petrobras"),
    ("VALE3", "Vale"),
    ("ITUB4", "Itaú Unibanco"),
    ("BBAS3", "Banco do Brasil"),
    ("BBDC4", "Bradesco"),
    ("ABEV3", "Ambev"),
    ("WEGE3", "WEG"),
    ("MGLU3", "Magazine Luiza"),
    ("^BVSP", "IBOVESPA"),
    ("^GSPC", "S&P 500"),
    ("^IXIC", "NASDAQ"),
    ("ESPO", "ETF Games (EUA)"),
]


def render_tabela_mercado(tickers_com_nomes, titulo=""):
    """Renderiza tabela compacta de cotações."""
    if titulo:
        st.subheader(titulo)
    rows = []
    n = len(tickers_com_nomes)
    progress = st.progress(0, text=f"Carregando 0/{n} tickers...")
    for i, (ticker, _) in enumerate(tickers_com_nomes):
        dados = cotacao_rapida(ticker)
        if dados is None:
            rows.append({"Ticker": ticker, "Nome": "—", "Preço": "—", "Var %": "—", "52w High": "—", "52w Low": "—"})
        else:
            emoji = "🟢" if dados["variacao_pct"] >= 0 else "🔴"
            rows.append({
                "Ticker": dados["ticker"],
                "Nome": dados["nome"][:30] if dados["nome"] else "—",
                "Preço": f"{dados['moeda']} {dados['preco']:.2f}",
                "Var %": f"{emoji} {dados['variacao_pct']:+.2f}%",
                "52w High": f"{dados['moeda']} {dados['52w_high']:.2f}",
                "52w Low": f"{dados['moeda']} {dados['52w_low']:.2f}",
            })
        progress.progress((i + 1) / n, text=f"Carregando {i+1}/{n} tickers...")
    progress.empty()
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados pra mostrar.")


def pagina_mercado(df_posicao):
    """Página Mercado: watchlist + seus ativos + benchmarks + busca livre + IBOV."""
    st.title("📈 Mercado")
    st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # ===== SEÇÃO 1: MERCADO AGORA (seus ativos + benchmarks) =====
    st.subheader("� Mercado Agora")
    tickers_usuario = []
    if not df_posicao.empty:
        tickers_usuario = [(r["Ticker"], r["Nome"]) for _, r in df_posicao.iterrows()]
    tickers_mercado = list({t: n for t, n in (tickers_usuario + BENCHMARKS_MERCADO)}.items())
    render_tabela_mercado(tickers_mercado)

    # ===== SEÇÃO 2: WATCHLIST =====
    st.divider()
    st.subheader("⭐ Sua Watchlist")

    col_add, col_clear = st.columns([3, 1])
    with col_add:
        novo_ticker = st.text_input("Adicionar ticker", placeholder="Ex: NTDOY, AAPL, PETR4", key="wl_add").upper().strip()
    with col_clear:
        st.write("")  # espaço pra alinhar
        st.write("")
        if st.button("🗑️ Limpar watchlist", key="wl_clear"):
            limpar_watchlist()
            st.rerun()

    if st.button("➕ Adicionar", key="wl_btn_add"):
        if novo_ticker:
            if adicionar_watchlist(novo_ticker):
                st.success(f"✅ {novo_ticker} adicionado à watchlist")
                st.rerun()
            else:
                st.warning(f"⚠️ {novo_ticker} já tá na watchlist")

    wl = listar_watchlist()
    if wl.empty:
        st.info("Watchlist vazia. Adicione tickers acima pra acompanhar.")
    else:
        tickers_wl = [(t, t) for t in wl["ticker"].tolist()]
        render_tabela_mercado(tickers_wl)

        # botão remover por ticker
        with st.expander("🗑️ Remover da watchlist"):
            ticker_remover = st.selectbox("Ticker pra remover", wl["ticker"].tolist(), key="wl_remove_sel")
            if st.button("Remover", key="wl_btn_remove"):
                remover_watchlist(ticker_remover)
                st.success(f"✅ {ticker_remover} removido")
                st.rerun()

    # ===== SEÇÃO 3: PESQUISA LIVRE =====
    st.divider()
    st.subheader("🔍 Buscar Ação")
    busca = st.text_input("Digite o ticker", placeholder="Ex: NTDOY, AAPL, VALE3", key="busca_mercado").upper().strip()
    if busca:
        dados = cotacao_rapida(busca)
        if dados:
            col1, col2, col3, col4 = st.columns(4)
            emoji = "🟢" if dados["variacao_pct"] >= 0 else "🔴"
            col1.metric("Preço", f"{dados['moeda']} {dados['preco']:.2f}")
            col2.metric("Variação", f"{emoji} {dados['variacao_pct']:+.2f}%")
            col3.metric("52w High", f"{dados['moeda']} {dados['52w_high']:.2f}")
            col4.metric("52w Low", f"{dados['moeda']} {dados['52w_low']:.2f}")
            st.caption(f"_{dados['nome']}_")
        else:
            st.error(f"❌ Não encontrei dados pra '{busca}'. Verifica o ticker.")

    # ===== SEÇÃO 4: IBOV COMPLETO =====
    st.divider()
    with st.expander("🇧🇷 Lista dos 78 IBOV (principais via Yahoo Finance)"):
        st.caption("Lista parcial dos constituintes do IBOVESPA. Adicione mais na watchlist.")
        ibov_main = [
            "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3",
            "WEGE3", "MGLU3", "B3SA3", "SUZB3", "GGBR4", "CSAN3",
            "JBSS3", "NATU3", "EQTL3", "CYRE3", "ELET3", "ELET6",
            "RENT3", "HAPV3", "RDOR3", "PRIO3", "LREN3", "TOTS3",
            "RAIZ4", "CSNA3", "PCAR3", "EMBR3", "AZUL4", "VIVT3",
        ]
        st.caption(f"Mostrando {len(ibov_main)} dos 78 (principais). Adicione os outros na watchlist.")
        if st.button("📊 Ver cotação destes", key="ibov_view"):
            render_tabela_mercado([(t, t) for t in ibov_main])


# ============================================================================
# MAIN
# ============================================================================
def main():
    init_db()
    if not autenticar():
        return

    # sidebar com navegação
    with st.sidebar:
        st.title("📊 Navegação")
        pagina = st.radio("Ir pra", ["Dashboard", "Mercado", "Registrar Operação", "Histórico", "Evolução", "Backtest", "Simulador"])
        st.divider()
        if st.button("🔄 Atualizar cotações"):
            st.cache_data.clear()
            st.rerun()
        st.caption("Cache de cotações: 15min")

    # carrega dados
    print(f"[MAIN] Lendo DB: {DB_PATH}")
    df_ops = listar_operacoes()
    print(f"[MAIN] df_ops tem {len(df_ops)} operacoes")
    tickers_unicos = listar_tickers_ativos()
    print(f"[MAIN] tickers_unicos: {list(tickers_unicos['ticker']) if not tickers_unicos.empty else 'vazio'}")
    cotacoes = {}
    cotacoes_ok = True
    if not tickers_unicos.empty:
        with st.spinner("Buscando cotações..."):
            for _, row in tickers_unicos.iterrows():
                cot = cotacao_yahoo(row["ticker"])
                print(f"[MAIN] cotacao {row['ticker']}: {cot}")
                if cot:
                    cotacoes[row["ticker"]] = cot
                else:
                    cotacoes_ok = False

    cambio = cambio_usd_brl()
    print(f"[MAIN] cambio USD/BRL: {cambio}")
    df_posicao = calcular_posicao(df_ops, cotacoes, cambio)
    print(f"[MAIN] df_posicao tem {len(df_posicao)} linhas")

    # roteia
    if pagina == "Dashboard":
        pagina_dashboard(df_posicao, cotacoes_ok)
    elif pagina == "Mercado":
        pagina_mercado(df_posicao)
    elif pagina == "Registrar Operação":
        pagina_registrar()
    elif pagina == "Histórico":
        pagina_historico()
    elif pagina == "Evolução":
        pagina_evolucao()
    elif pagina == "Backtest":
        pagina_backtest()
    elif pagina == "Simulador":
        pagina_simulador()


if __name__ == "__main__":
    main()
