import streamlit as st
import requests
import pandas as pd
import time
import re

API_BASE = "http://localhost:8000"

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="WhisperQL · SQL Generator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injection ───────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
/* ── Reset & base ──────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}

/* Dark background across entire app */
.stApp {
    background: #080b12 !important;
}

/* Main content area */
.main .block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1100px !important;
}

/* ── Sidebar ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1017 !important;
    border-right: 1px solid rgba(82,196,255,0.1) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 2rem 1.2rem !important;
}

/* ── Text defaults ──────────────────────────────────── */
h1, h2, h3, h4, label, p, span, div {
    color: #e8eaf2 !important;
}

/* ── Scrollbar ──────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #080b12; }
::-webkit-scrollbar-thumb { background: #1e2535; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #52c4ff33; }

/* ── Input fields ───────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #0d1320 !important;
    border: 1px solid #1e2a3d !important;
    border-radius: 10px !important;
    color: #c8f0ff !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.83rem !important;
    caret-color: #52c4ff !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    padding: 0.75rem 1rem !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #52c4ff !important;
    box-shadow: 0 0 0 3px rgba(82,196,255,0.08) !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #3a4a60 !important;
}
[data-testid="stTextArea"] textarea {
    min-height: 120px !important;
    resize: vertical !important;
}

/* ── Labels ─────────────────────────────────────────── */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #4a6280 !important;
    margin-bottom: 6px !important;
}

/* ── Buttons ─────────────────────────────────────────── */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

/* Primary button – glowing cyan */
.stButton > button[kind="primary"],
.stButton > button:first-child {
    background: linear-gradient(135deg, #52c4ff, #3a8fff) !important;
    color: #020810 !important;
    border: none !important;
    box-shadow: 0 0 22px rgba(82,196,255,0.25) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button:first-child:hover {
    box-shadow: 0 0 36px rgba(82,196,255,0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:active,
.stButton > button:first-child:active {
    transform: translateY(0px) !important;
}

/* Secondary ghost button */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #1e2a3d !important;
    color: #52c4ff !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #52c4ff !important;
    background: rgba(82,196,255,0.05) !important;
}

/* ── Expander ────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #0d1017 !important;
    border: 1px solid #1a2233 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    color: #4a6280 !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stExpander"] summary:hover {
    color: #52c4ff !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0 1rem 1rem !important;
}

/* ── Dataframe / table ───────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a2233 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] iframe {
    background: #0d1017 !important;
}

/* ── Code block ──────────────────────────────────────── */
[data-testid="stCode"],
.stCodeBlock {
    border-radius: 12px !important;
    border: 1px solid #1a2233 !important;
    overflow: hidden !important;
}

/* ── Divider ─────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #151e2e !important;
    margin: 2rem 0 !important;
}

/* ── Spinner ─────────────────────────────────────────── */
[data-testid="stSpinner"] > div {
    border-top-color: #52c4ff !important;
}

/* ── Alert / info / error / success boxes ────────────── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-width: 1px !important;
    font-family: 'Syne', sans-serif !important;
}

/* ── Metric cards ────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #0d1017 !important;
    border: 1px solid #1a2233 !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #4a6280 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #52c4ff !important;
}

/* ── Tabs ────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1a2233 !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #4a6280 !important;
    border-radius: 0 !important;
    padding: 0.6rem 1.2rem !important;
    transition: color 0.2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #52c4ff !important;
    border-bottom: 2px solid #52c4ff !important;
    background: transparent !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: #c8f0ff !important;
    background: rgba(82,196,255,0.04) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helper: custom HTML components ────────────────────────────────────────────

def render_header():
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:space-between;padding:0.5rem 0 2rem;border-bottom:1px solid #151e2e;margin-bottom:2.5rem;">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:8px;height:8px;border-radius:50%;background:#52c4ff;"></div>
                <p style="font-family:'SF Pro Display','Segoe UI','Inter',system-ui,sans-serif;font-weight:800;font-size:1.6rem;letter-spacing:-0.04em;line-height:1;margin:0;">
                    <font color="#e8eaf2">Whisper</font><font color="#52c4ff">QL</font>
                </p>
            </div>
            <div style="width:1px;height:28px;background:#1e2a3a;margin:0 4px;"></div>
            <div style="font-family:'SF Mono','Fira Code','Consolas',monospace;font-size:0.65rem;color:#2e4460;line-height:1.7;letter-spacing:0.02em;">
                Natural Language<br><font color="#3a6080">→ SQL</font>
            </div>
        </div>
        <div style="font-family:'SF Mono','Fira Code','Consolas',monospace;font-size:0.68rem;color:#2e3f55;background:#0d1017;border:1px solid #1a2233;padding:5px 13px;border-radius:100px;">v1.0 · LLM Powered</div>
    </div>
    """, unsafe_allow_html=True)


def render_sql_card(sql: str):
    import re

    keywords = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
                "ON", "AND", "OR", "NOT", "IN", "IS", "NULL", "AS", "GROUP", "BY",
                "ORDER", "HAVING", "LIMIT", "OFFSET", "INSERT", "INTO", "VALUES",
                "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "DROP", "ALTER",
                "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX", "CASE", "WHEN",
                "THEN", "ELSE", "END", "WITH", "UNION", "ALL", "EXISTS", "BETWEEN"]

    def highlight(sql_text):
        # Escape HTML special chars FIRST
        escaped = (sql_text
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))

        # Highlight quoted identifiers like "Employee_details"
        escaped = re.sub(
            r'(&quot;.*?&quot;|"[^"]*")',
            r'<span style="color:#fbbf24;">\1</span>',
            escaped
        )
        # Highlight single-quoted strings
        escaped = re.sub(
            r"('.*?')",
            r'<span style="color:#fbbf24;">\1</span>',
            escaped
        )
        # Highlight numbers
        escaped = re.sub(
            r'\b(\d+)\b',
            r'<span style="color:#a78bfa;">\1</span>',
            escaped
        )
        # Highlight SQL keywords (must come LAST to avoid re-matching span attributes)
        for kw in keywords:
            escaped = re.sub(
                rf'(?<![a-zA-Z#:;-])\b({kw})\b(?![a-zA-Z#:;-])',
                lambda m: f'<span style="color:#52c4ff;font-weight:600;">{m.group(1).upper()}</span>',
                escaped,
                flags=re.IGNORECASE
            )
        return escaped

    highlighted = highlight(sql)

    st.markdown(f"""
    <div style="
        background:#0a0f1a;
        border:1px solid rgba(82,196,255,0.2);
        border-radius:12px;
        overflow:hidden;
        margin:1rem 0;
    ">
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            padding:10px 16px;
            background:#0d1017;
            border-bottom:1px solid rgba(82,196,255,0.12);
            position:relative;
        ">
            <div style="display:flex; gap:7px; align-items:center;">
                <div style="width:11px;height:11px;border-radius:50%;background:#ff5f57;"></div>
                <div style="width:11px;height:11px;border-radius:50%;background:#febc2e;"></div>
                <div style="width:11px;height:11px;border-radius:50%;background:#28c840;"></div>
            </div>
            <span style="
                position:absolute; left:50%; transform:translateX(-50%);
                font-family:'Space Mono',monospace;
                font-size:0.68rem; color:rgba(82,196,255,0.5);
                letter-spacing:0.1em; text-transform:uppercase;
            ">Generated SQL</span>
            <span></span>
        </div>
        <div style="
            padding:1.4rem 1.8rem;
            font-family:'Space Mono',monospace;
            font-size:0.84rem;
            line-height:2;
            color:#e2e8f0;
            white-space:pre-wrap;
            word-break:break-word;
            overflow-x:auto;
        ">{highlighted}</div>
    </div>
    """, unsafe_allow_html=True)


def render_result_header(rows: int, cols: int, attempts: int, elapsed: float):
    st.markdown(f"""
    <div style="
        display:flex; align-items:center; gap:12px; flex-wrap:wrap;
        margin: 1.5rem 0 1rem;
    ">
        <div style="
            background:rgba(40,200,100,0.08);
            border:1px solid rgba(40,200,100,0.2);
            border-radius:8px; padding:5px 14px;
            font-family:'Space Mono',monospace;
            font-size:0.75rem; color:#28c864;
            font-weight:700;
        ">✓ &nbsp;{rows} row{'s' if rows != 1 else ''} · {cols} col{'s' if cols != 1 else ''}</div>
        <div style="
            background:#0d1017; border:1px solid #1a2233;
            border-radius:8px; padding:5px 14px;
            font-size:0.75rem; color:#4a6280;
            font-family:'Space Mono',monospace;
        ">⏱ {elapsed:.2f}s</div>
    </div>
    """, unsafe_allow_html=True)


def render_error_card(msg: str):
    escaped = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(f"""
    <div style="
        background: rgba(255,80,80,0.05);
        border: 1px solid rgba(255,80,80,0.2);
        border-left: 3px solid #ff5050;
        border-radius:12px; padding:1rem 1.2rem;
        margin:1rem 0;
    ">
        <div style="font-size:0.72rem; font-weight:700; letter-spacing:0.1em;
                    text-transform:uppercase; color:#ff5050; margin-bottom:8px;">
            ⚠ Execution Failed
        </div>
        <pre style="font-family:'Space Mono',monospace; font-size:0.78rem;
                    color:#ff9090; white-space:pre-wrap; margin:0;">{escaped}</pre>
    </div>
    """, unsafe_allow_html=True)


def render_history_item(i: int, item: dict):
    status_color = "#28c864" if item["success"] else "#ff5050"
    status_icon  = "✓" if item["success"] else "✗"
    q_escaped    = item["question"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    sql_escaped  = item["sql"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f"""
    <div style="
        background:#0d1017; border:1px solid #1a2233;
        border-radius:10px; padding:0.9rem 1.1rem;
        margin-bottom:10px;
    ">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="
                font-family:'Space Mono',monospace; font-size:0.65rem;
                color:{status_color}; background:rgba(0,0,0,0.3);
                border:1px solid {status_color}33;
                border-radius:6px; padding:2px 8px; font-weight:700;
            ">{status_icon} #{i+1}</span>
            <span style="font-size:0.88rem; color:#c8d0e0; font-weight:600;">{q_escaped}</span>
        </div>
        <pre style="
            font-family:'Space Mono',monospace; font-size:0.72rem;
            color:#3a5070; margin:0;
            white-space:pre-wrap; word-break:break-word;
        ">{sql_escaped}</pre>
    </div>
    """, unsafe_allow_html=True)


def render_schema_box(schema: str):
    escaped = schema.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f"""
    <div style="
        background:#080b12; border:1px solid #1a2233;
        border-radius:10px; padding:1rem 1.2rem;
        font-family:'Space Mono',monospace;
        font-size:0.74rem; line-height:1.9;
        color:#3a6090;
        max-height:260px; overflow-y:auto;
    ">{escaped}</div>
    """, unsafe_allow_html=True)


def render_example_chip(label: str):
    return f"""
    <span style="
        display:inline-block;
        background:#0d1320; border:1px solid #1e2a3d;
        border-radius:8px; padding:6px 14px;
        font-size:0.78rem; color:#4a7090;
        cursor:pointer; margin:4px;
        font-family:'Syne',sans-serif;
        transition:all 0.2s;
    " title="Click to copy">{label}</span>
    """


# ── Session state init ─────────────────────────────────────────────────────────
if "schema_text" not in st.session_state:
    st.session_state.schema_text = ""
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_sql" not in st.session_state:
    st.session_state.pending_sql = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
                    text-transform:uppercase; color:#2a3a50; margin-bottom:1rem;">
            ◈ &nbsp;Connection
        </div>
    </div>
    """, unsafe_allow_html=True)

    db_host = st.text_input(
        "Host",
        value="localhost",
        help="Database server hostname or IP",
    )
    db_port = st.text_input(
        "Port",
        value="5432",
        help="Database server port",
    )
    db_name = st.text_input(
        "Database",
        value="",
        help="Name of the database to connect to",
    )
    db_user = st.text_input(
        "Username",
        value="",
        help="Database username",
    )
    db_pass = st.text_input(
        "Password",
        value="",
        type="password",
        help="Database password",
    )

    def _build_db_config():
        """Build the db_config dict from sidebar inputs."""
        return {
            "host": db_host.strip(),
            "port": int(db_port.strip()) if db_port.strip() else 5432,
            "database": db_name.strip(),
            "username": db_user.strip(),
            "password": db_pass,
        }

    def _db_fields_filled():
        return all([db_host.strip(), db_port.strip(), db_name.strip(), db_user.strip(), db_pass])

    if st.button("⚡ Load Schema", use_container_width=True):
        if not _db_fields_filled():
            st.warning("Please fill in all connection fields.")
        else:
            with st.spinner("Introspecting database..."):
                try:
                    r = requests.post(
                        f"{API_BASE}/schema",
                        json={"db_config": _build_db_config()},
                        timeout=10,
                    )
                    if r.status_code == 200:
                        st.session_state.schema_text = r.json().get("schema", "")
                        st.success("Schema loaded!")
                    else:
                        detail = r.json().get("detail", r.text)
                        st.error(f"Error {r.status_code}: {detail}")
                except Exception as e:
                    st.error(f"Cannot reach API: {e}")

    if st.session_state.schema_text:
        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
        with st.expander("📐 Schema Preview"):
            render_schema_box(st.session_state.schema_text)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Health indicator
    st.markdown("""
    <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
                text-transform:uppercase; color:#2a3a50; margin-bottom:0.8rem;">
        ◈ &nbsp;API Status
    </div>
    """, unsafe_allow_html=True)

    try:
        hr = requests.get(f"{API_BASE}/health", timeout=3)
        if hr.status_code == 200:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:9px;
                        background:#0a1a10;border:1px solid #1a3a20;
                        border-radius:8px;padding:8px 14px;">
                <div style="width:8px;height:8px;border-radius:50%;
                            background:#28c864;box-shadow:0 0 8px #28c864;"></div>
                <span style="font-family:'Space Mono',monospace;
                             font-size:0.72rem;color:#28c864;">Backend online</span>
            </div>""", unsafe_allow_html=True)
        else:
            raise Exception()
    except:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:9px;
                    background:#1a0a0a;border:1px solid #3a1a1a;
                    border-radius:8px;padding:8px 14px;">
            <div style="width:8px;height:8px;border-radius:50%;
                        background:#ff5050;box-shadow:0 0 8px #ff5050;"></div>
            <span style="font-family:'Space Mono',monospace;
                         font-size:0.72rem;color:#ff5050;">Backend offline</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Tips
    st.markdown("""
    <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
                text-transform:uppercase; color:#2a3a50; margin-bottom:0.8rem;">
        ◈ &nbsp;Tips
    </div>
    <div style="font-size:0.78rem; color:#2a3a50; line-height:1.9;">
        • Start with <span style="color:#3a6080;">Load Schema</span><br>
        • Be specific about filters<br>
        • Mention table/column names<br>
        • Review SQL before executing
    </div>
    """, unsafe_allow_html=True)


# ── Main content ───────────────────────────────────────────────────────────────
render_header()

# Tabs: Query | History
tab_query, tab_history = st.tabs(["⚡  Query", "📜  History"])

# ── TAB 1: Query ──────────────────────────────────────────────────────────────
with tab_query:

    # Example chips (decorative / informational)
    st.markdown("""
    <div style="margin-bottom:1.4rem;">
        <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
                    text-transform:uppercase; color:#2a3a50; margin-bottom:0.7rem;">
            Try an example
        </div>
        <div>
    """ +
        render_example_chip("List all users who signed up this year") +
        render_example_chip("Top 5 products by revenue") +
        render_example_chip("Orders with status = pending") +
        render_example_chip("Average order value per customer") +
    """  
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Question input
    question = st.text_area(
        "Ask a question about your database",
        placeholder="e.g.  How many orders were placed last month, grouped by status?",
        height=110,
        label_visibility="visible",
    )

    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        generate_clicked = st.button("🔮  Generate SQL", use_container_width=True)
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.last_result = None
            st.session_state.pending_sql = None
            st.session_state.pending_question = None
            st.rerun()

    # ── Step 1: Generate SQL (no execution) ───────────────────────────────
    if generate_clicked:
        if not question.strip():
            st.warning("Please enter a question first.")
        elif not _db_fields_filled():
            st.warning("Please fill in all database connection fields in the sidebar.")
        else:
            with st.spinner("🔮 Generating SQL..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/generate",
                        json={"question": question, "db_config": _build_db_config()},
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.pending_sql = data["sql"]
                        st.session_state.pending_question = question
                        st.session_state.last_result = None
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Generation failed ({resp.status_code}): {detail}")
                except Exception as e:
                    st.error(f"Could not reach the backend: {e}")

    # ── Step 2: Show generated SQL and ask for confirmation ───────────────
    if st.session_state.pending_sql and st.session_state.last_result is None:
        render_sql_card(st.session_state.pending_sql)

        st.markdown("""
        <div style="
            background: rgba(82,196,255,0.05);
            border: 1px solid rgba(82,196,255,0.15);
            border-radius: 10px; padding: 0.8rem 1.1rem;
            margin: 0.8rem 0 1.2rem;
            display: flex; align-items: center; gap: 10px;
        ">
            <span style="font-size:1.2rem;">⚠️</span>
            <span style="font-size:0.82rem; color:#7ab8d9;">
                Review the generated SQL above. Click <b>Execute Query</b> to run it, or <b>Cancel</b> to discard.
            </span>
        </div>
        """, unsafe_allow_html=True)

        col_exec, col_cancel = st.columns([3, 1])
        with col_exec:
            execute_clicked = st.button("⚡ Execute Query", use_container_width=True)
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.pending_sql = None
                st.session_state.pending_question = None
                st.rerun()

        if execute_clicked:
            start = time.time()
            with st.spinner("⚡ Executing..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/execute",
                        json={
                            "sql": st.session_state.pending_sql,
                            "question": st.session_state.pending_question,
                            "db_config": _build_db_config(),
                        },
                        timeout=60,
                    )
                    elapsed = time.time() - start
                    if resp.status_code == 200:
                        data = resp.json()
                        data["elapsed"] = elapsed
                        data["question"] = st.session_state.pending_question
                        st.session_state.last_result = data
                        st.session_state.history.insert(0, {
                            "question": st.session_state.pending_question,
                            "sql": data["sql"],
                            "success": data["error"] is None,
                        })
                        st.session_state.history = st.session_state.history[:10]
                        st.session_state.pending_sql = None
                        st.session_state.pending_question = None
                        st.rerun()
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Execution failed ({resp.status_code}): {detail}")
                except Exception as e:
                    st.error(f"Could not reach the backend: {e}")

    # ── Results display ──────────────────────────────────────────────────
    res = st.session_state.last_result
    if res:
        render_sql_card(res["sql"])

        if res["error"] is None:
            rows  = res["rows"]
            cols  = res["columns"]
            render_result_header(
                len(rows), len(cols),
                res.get("attempts", 1),
                res.get("elapsed", 0),
            )
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=min(400, 38 + len(df) * 35),
                )
            else:
                st.markdown("""
                <div style="text-align:center; padding:2.5rem;
                            color:#2a3a50; font-size:0.88rem;">
                    Query ran successfully — no rows returned.
                </div>
                """, unsafe_allow_html=True)
        else:
            render_error_card(res["error"])
            st.markdown("""
            <div style="font-size:0.78rem; color:#3a4a60; margin-top:0.5rem;">
                The query failed. Try rephrasing your question and generating again.
            </div>
            """, unsafe_allow_html=True)


# ── TAB 2: History ─────────────────────────────────────────────────────────────
with tab_history:
    try:
        hr = requests.get(f"{API_BASE}/history", timeout=5)
        if hr.status_code == 200:
            api_history = hr.json()
        else:
            api_history = st.session_state.history
    except:
        api_history = st.session_state.history

    if not api_history:
        st.markdown("""
        <div style="
            text-align:center; padding:4rem 2rem;
            color:#2a3a50;
        ">
            <div style="font-size:2.5rem; margin-bottom:1rem; opacity:0.4;">📭</div>
            <div style="font-size:0.9rem; font-weight:600;">No queries yet</div>
            <div style="font-size:0.78rem; margin-top:0.5rem; opacity:0.6;">
                Run a query from the Query tab to see it here.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
                    text-transform:uppercase; color:#2a3a50; margin-bottom:1rem;">
            Last {len(api_history)} queries
        </div>
        """, unsafe_allow_html=True)
        for i, item in enumerate(api_history):
            render_history_item(i, item)