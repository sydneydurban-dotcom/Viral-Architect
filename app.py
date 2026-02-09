import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="The Viral Architect", page_icon="🏗️", layout="wide")

# ─────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    .main .block-container { max-width: 1100px; padding-top: 2rem; }

    h1, h2, h3 { font-family: 'Inter', sans-serif; }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 14px;
        padding: 1.4rem;
        text-align: center;
        color: #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .metric-card .label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #8892b0;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 800;
        color: #64ffda;
    }
    .metric-card .sub {
        font-size: 0.78rem;
        color: #8892b0;
        margin-top: 0.2rem;
    }
    .metric-card.warn .value { color: #ff6b6b; }
    .metric-card.gold .value { color: #ffd700; }

    .matrix-title {
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.4rem;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        display: inline-block;
    }
    .q-title { background: #1a1a2e; color: #64ffda; border: 1px solid #0f3460; }
    .r-title { background: #2d1b2e; color: #ff6b9d; border: 1px solid #4a1942; }
    .f-title { background: #1b2e1b; color: #a8ff64; border: 1px solid #2e5a1b; }
    .b-title { background: #2e2b1b; color: #ffd700; border: 1px solid #5a4e1b; }

    div[data-testid="stDataFrame"] table { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.markdown("# 🏗️ The Viral Architect")
st.markdown("*Absorbing Markov Chain simulator for social-media growth funnels*")
st.divider()

# ─────────────────────────────────────────────────────────────
# Sidebar – state definitions
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Architecture Setup")

    preset = st.selectbox("Load preset", [
        "Custom",
        "Part 1 – 4-State Retention Loop",
        "Part 2 – 6-State Deep Funnel",
    ])

    if preset == "Part 1 – 4-State Retention Loop":
        default_names = ["Viewer", "Creator", "Influencer", "Ghost"]
        default_types = ["Transient", "Transient", "Absorbing", "Absorbing"]
        default_P = [
            [0.3, 0.4, 0.0, 0.3],
            [0.1, 0.6, 0.2, 0.1],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    elif preset == "Part 2 – 6-State Deep Funnel":
        default_names = ["Newbie", "Casual", "Power User", "Community Leader", "Verified Legend", "Deleted Account"]
        default_types = ["Transient", "Transient", "Transient", "Transient", "Absorbing", "Absorbing"]
        default_P = [
            [0.40, 0.20, 0.00, 0.00, 0.00, 0.40],
            [0.00, 0.30, 0.30, 0.00, 0.00, 0.40],
            [0.00, 0.00, 0.30, 0.50, 0.00, 0.20],
            [0.00, 0.00, 0.00, 0.30, 0.60, 0.10],
            [0.00, 0.00, 0.00, 0.00, 1.00, 0.00],
            [0.00, 0.00, 0.00, 0.00, 0.00, 1.00],
        ]
    else:
        default_names = ["Newbie", "Casual", "Power User", "Community Leader", "Verified Legend", "Deleted Account"]
        default_types = ["Transient", "Transient", "Transient", "Transient", "Absorbing", "Absorbing"]
        default_P = None

    st.subheader("State Names & Types")
    num_states = st.slider("Number of states", 3, 8, len(default_names))

    state_names = []
    state_types = []
    for i in range(num_states):
        c1, c2 = st.columns([2, 1])
        with c1:
            name = st.text_input(f"S{i+1}", value=default_names[i] if i < len(default_names) else f"State {i+1}", key=f"name_{i}")
        with c2:
            stype = st.selectbox("Type", ["Transient", "Absorbing"],
                                 index=0 if (i < len(default_types) and default_types[i] == "Transient") else 1,
                                 key=f"type_{i}")
        state_names.append(name)
        state_types.append(stype)

    transient_idx = [i for i, t in enumerate(state_types) if t == "Transient"]
    absorbing_idx = [i for i, t in enumerate(state_types) if t == "Absorbing"]
    t_names = [state_names[i] for i in transient_idx]
    a_names = [state_names[i] for i in absorbing_idx]
    n_t = len(transient_idx)
    n_a = len(absorbing_idx)

    if n_a < 1:
        st.error("You need at least 1 absorbing state.")
        st.stop()
    if n_t < 1:
        st.error("You need at least 1 transient state.")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Transition matrix input
# ─────────────────────────────────────────────────────────────
st.subheader("📝 Transition Matrix P")
st.caption("Enter transition probabilities. Each row must sum to 1. Absorbing states must have a self-loop of 1.0.")

# Reorder: transient first, absorbing last
ordered_idx = transient_idx + absorbing_idx
ordered_names = [state_names[i] for i in ordered_idx]

# Build default matrix in reordered form
if default_P is not None and len(default_P) == num_states:
    P_default = np.array(default_P, dtype=float)
    # reorder rows and cols
    P_default = P_default[np.ix_(ordered_idx, ordered_idx)]
else:
    P_default = np.zeros((num_states, num_states))
    for i in range(num_states):
        if ordered_idx[i] in absorbing_idx:
            P_default[i, i] = 1.0

# Editable dataframe
df_P_input = pd.DataFrame(P_default, index=ordered_names, columns=ordered_names)

edited_P = st.data_editor(
    df_P_input,
    use_container_width=True,
    key="P_editor",
    num_rows="fixed",
)

P = edited_P.values.astype(float)

# ─────── Validate rows ───────
row_sums = P.sum(axis=1)
valid = True
for i, s in enumerate(row_sums):
    if abs(s - 1.0) > 0.02:
        st.warning(f"Row **{ordered_names[i]}** sums to {s:.4f} (should be 1.0)")
        valid = False

# Check absorbing rows
for j, ai in enumerate(range(n_t, n_t + n_a)):
    if abs(P[ai, ai] - 1.0) > 0.001:
        st.warning(f"Absorbing state **{a_names[j]}** must have self-loop = 1.0")
        valid = False

if not valid:
    st.error("Fix the transition matrix before proceeding.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# Extract Q, R, compute F, B
# ─────────────────────────────────────────────────────────────
Q = P[:n_t, :n_t]
R = P[:n_t, n_t:]
I = np.eye(n_t)
IQ = I - Q

try:
    F = np.linalg.inv(IQ)
except np.linalg.LinAlgError:
    st.error("(I − Q) is singular — check your Q matrix.")
    st.stop()

B = F @ R

# Row sums of F = expected life in system (τ)
tau = F.sum(axis=1)

# ─────────────────────────────────────────────────────────────
# What-If toggle
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔀 What-If Analysis")
st.caption("Reduce the probability that **Newbies (first transient state)** drop out and see how many more Legends are created.")

# Find "exit" absorbing state (last one) and "win" absorbing state (first one if 2 exist, else only)
win_col = 0  # first absorbing col in R
exit_col = n_a - 1 if n_a >= 2 else 0

whatif_on = st.toggle("Enable What-If toggle", value=False)
reduction = 0.0
if whatif_on:
    reduction = st.slider(
        "Reduce Newbie dropout probability by:",
        min_value=0.0,
        max_value=float(R[0, exit_col]) - 0.01 if R[0, exit_col] > 0.01 else 0.0,
        value=0.0,
        step=0.01,
        format="%.2f",
    )

# Build adjusted matrices
if whatif_on and reduction > 0:
    P_adj = P.copy()
    # Row 0 is first transient state (Newbie)
    P_adj[0, n_t + exit_col] -= reduction  # reduce exit
    P_adj[0, 0] += reduction  # redistribute to self-loop (stay)
    Q_adj = P_adj[:n_t, :n_t]
    R_adj = P_adj[:n_t, n_t:]
    F_adj = np.linalg.inv(np.eye(n_t) - Q_adj)
    B_adj = F_adj @ R_adj
    tau_adj = F_adj.sum(axis=1)
else:
    Q_adj, R_adj, F_adj, B_adj, tau_adj = Q, R, F, B, tau

# ─────────────────────────────────────────────────────────────
# Dashboard Metrics
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Dashboard")

# Success probability for first transient → first absorbing (WIN)
p_success = B_adj[0, win_col]
p_exit = B_adj[0, exit_col] if n_a >= 2 else 1 - p_success
life_exp = tau_adj[0]

# Bottleneck: which state has highest F value in row 0
bottleneck_idx = np.argmax(F_adj[0])
bottleneck_name = t_names[bottleneck_idx]

cols = st.columns(4)
with cols[0]:
    st.markdown(f"""<div class="metric-card gold">
        <div class="label">🏆 Success Rate</div>
        <div class="value">{p_success*100:.2f}%</div>
        <div class="sub">{t_names[0]} → {a_names[win_col]}</div>
    </div>""", unsafe_allow_html=True)
with cols[1]:
    st.markdown(f"""<div class="metric-card warn">
        <div class="label">👻 Exit Rate</div>
        <div class="value">{p_exit*100:.2f}%</div>
        <div class="sub">{t_names[0]} → {a_names[exit_col]}</div>
    </div>""", unsafe_allow_html=True)
with cols[2]:
    st.markdown(f"""<div class="metric-card">
        <div class="label">⏳ Life Expectancy (τ)</div>
        <div class="value">{life_exp:.2f}</div>
        <div class="sub">steps from {t_names[0]}</div>
    </div>""", unsafe_allow_html=True)
with cols[3]:
    st.markdown(f"""<div class="metric-card">
        <div class="label">🔄 Bottleneck State</div>
        <div class="value" style="font-size:1.4rem;">{bottleneck_name}</div>
        <div class="sub">{F_adj[0, bottleneck_idx]:.2f} expected visits</div>
    </div>""", unsafe_allow_html=True)

# What-if comparison
if whatif_on and reduction > 0:
    delta_success = (B_adj[0, win_col] - B[0, win_col]) * 100
    delta_life = tau_adj[0] - tau[0]
    st.markdown("#### 🔬 What-If Impact")
    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        sign = "+" if delta_success >= 0 else ""
        st.metric("Success Rate Change", f"{B_adj[0,win_col]*100:.2f}%", f"{sign}{delta_success:.2f}pp")
    with wc2:
        sign = "+" if delta_life >= 0 else ""
        st.metric("Life Expectancy Change", f"{tau_adj[0]:.2f}", f"{sign}{delta_life:.2f} steps")
    with wc3:
        st.metric("Dropout Reduction", f"−{reduction:.2f}", f"from {R[0,exit_col]:.2f} → {R[0,exit_col]-reduction:.2f}")

# ─────────────────────────────────────────────────────────────
# Sub-matrices display
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔢 Computed Matrices")

tab_q, tab_r, tab_f, tab_b = st.tabs(["Q (Social Ladder)", "R (Exit Logic)", "F (Fundamental)", "B (Absorption)"])

with tab_q:
    st.markdown('<span class="matrix-title q-title">Q — Transient-to-Transient transitions</span>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(Q_adj, index=t_names, columns=t_names).style.format("{:.4f}"), use_container_width=True)

with tab_r:
    st.markdown('<span class="matrix-title r-title">R — Transient-to-Absorbing transitions</span>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(R_adj, index=t_names, columns=a_names).style.format("{:.4f}"), use_container_width=True)

with tab_f:
    st.markdown('<span class="matrix-title f-title">F = (I − Q)⁻¹ — Expected visits to each transient state</span>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(F_adj, index=t_names, columns=t_names).style.format("{:.4f}"), use_container_width=True)
    st.caption("Row sums = total life expectancy (τ) from each starting state.")
    st.dataframe(pd.DataFrame({"τ (Life Expectancy)": tau_adj}, index=t_names).style.format("{:.4f}"), use_container_width=True)

with tab_b:
    st.markdown('<span class="matrix-title b-title">B = F × R — Absorption probabilities</span>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(B_adj, index=t_names, columns=a_names).style.format("{:.4f}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Visualizations
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Visualizations")

v1, v2 = st.tabs(["Absorption Probabilities", "Expected Visits (F matrix)"])

with v1:
    # Grouped bar: for each transient state, show absorption probs
    bar_data = []
    for i, tn in enumerate(t_names):
        for j, an in enumerate(a_names):
            bar_data.append({"Starting State": tn, "Destination": an, "Probability": B_adj[i, j]})
    df_bar = pd.DataFrame(bar_data)
    fig_bar = px.bar(df_bar, x="Starting State", y="Probability", color="Destination",
                     barmode="group",
                     color_discrete_sequence=["#64ffda", "#ff6b6b", "#ffd700", "#a78bfa"],
                     title="Absorption Probabilities by Starting State")
    fig_bar.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", yaxis_range=[0, 1],
        title_font_size=16,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with v2:
    # Heatmap of F
    fig_heat = go.Figure(data=go.Heatmap(
        z=F_adj,
        x=t_names,
        y=t_names,
        colorscale=[[0, "#0e1117"], [0.5, "#1a535c"], [1, "#64ffda"]],
        text=np.round(F_adj, 3),
        texttemplate="%{text}",
        textfont={"size": 13},
    ))
    fig_heat.update_layout(
        title="Fundamental Matrix F — Expected Visits",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_size=16,
        xaxis_title="Destination State", yaxis_title="Starting State",
        yaxis_autorange="reversed",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Forensic Audit helpers (Part 3 questions)
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔍 Forensic Audit (Part 3 Insights)")

if n_t >= 3:
    f13 = F_adj[0, 2]
    f33 = F_adj[2, 2]
    h13 = f13 / f33
    st.markdown(f"**Q1 — Probability {t_names[0]} ever reaches {t_names[2]}:**  "
                f"f₁₃ / f₃₃ = {f13:.4f} / {f33:.4f} = **{h13:.4f}** ({h13*100:.2f}%)")

if n_t >= 4:
    f11 = F_adj[0, 0]
    f44 = F_adj[3, 3]
    stickier = t_names[0] if f11 > f44 else t_names[3]
    st.markdown(f"**Q2 — Stickiness:**  f₁₁ = {f11:.4f} ({t_names[0]}), f₄₄ = {f44:.4f} ({t_names[3]}).  "
                f"**{stickier}** is stickier.")
    if n_a >= 2:
        b41 = B_adj[3, win_col]
        b42 = B_adj[3, exit_col]
        st.markdown(f"**Q3 — Fate of the Elite ({t_names[3]}):**  "
                    f"P(→ {a_names[win_col]}) = **{b41:.4f}**, P(→ {a_names[exit_col]}) = **{b42:.4f}**")

    f11_val = F_adj[0, 0]
    loop_back = (f11_val - 1) / f11_val
    st.markdown(f"**Q4 — Loop-Back Proof:**  (f₁₁ − 1)/f₁₁ = ({f11_val:.4f} − 1)/{f11_val:.4f} = **{loop_back:.4f}**  "
                f"(compare to P₁₁ = {Q_adj[0,0]:.4f})")

# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────
st.divider()
st.caption("Built for *The Viral Architect* — Probabilistic Modeling with Absorbing Markov Chains")
