import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io

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
# Presets
# ─────────────────────────────────────────────────────────────
PRESETS = {
    "Part 1 – 4-State Retention Loop": {
        "names": ["Viewer", "Creator", "Influencer", "Ghost"],
        "types": ["Transient", "Transient", "Absorbing", "Absorbing"],
        "P": [
            [0.3, 0.4, 0.0, 0.3],
            [0.1, 0.6, 0.2, 0.1],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
    },
    "Part 2 – 6-State Deep Funnel": {
        "names": ["Newbie", "Casual", "Power User", "Community Leader", "Verified Legend", "Deleted Account"],
        "types": ["Transient", "Transient", "Transient", "Transient", "Absorbing", "Absorbing"],
        "P": [
            [0.40, 0.20, 0.00, 0.00, 0.00, 0.40],
            [0.00, 0.30, 0.30, 0.00, 0.00, 0.40],
            [0.00, 0.00, 0.30, 0.50, 0.00, 0.20],
            [0.00, 0.00, 0.00, 0.30, 0.60, 0.10],
            [0.00, 0.00, 0.00, 0.00, 1.00, 0.00],
            [0.00, 0.00, 0.00, 0.00, 0.00, 1.00],
        ],
    },
}

# ─────────────────────────────────────────────────────────────
# Sidebar – State definitions
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Architecture Setup")

    preset = st.selectbox("Load preset", ["Custom"] + list(PRESETS.keys()))
    pre = PRESETS.get(preset)

    st.subheader("State Names & Types")
    default_n = len(pre["names"]) if pre else 6
    num_states = st.slider("Number of states", 3, 15, default_n)

    state_names: list[str] = []
    state_types: list[str] = []

    default_names_list = pre["names"] if pre else [
        "Newbie", "Casual", "Power User", "Community Leader", "Verified Legend", "Deleted Account"
    ]
    default_types_list = pre["types"] if pre else [
        "Transient", "Transient", "Transient", "Transient", "Absorbing", "Absorbing"
    ]

    for i in range(num_states):
        c1, c2 = st.columns([2, 1])
        with c1:
            name = st.text_input(
                f"S{i+1}",
                value=default_names_list[i] if i < len(default_names_list) else f"State {i+1}",
                key=f"name_{i}",
            )
        with c2:
            default_type_idx = 0
            if i < len(default_types_list) and default_types_list[i] == "Absorbing":
                default_type_idx = 1
            stype = st.selectbox("Type", ["Transient", "Absorbing"], index=default_type_idx, key=f"type_{i}")
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

# Canonical ordering: transient first, absorbing last
ordered_idx = transient_idx + absorbing_idx
ordered_names = [state_names[i] for i in ordered_idx]
N = num_states

# ─────────────────────────────────────────────────────────────
# Input mode selection
# ─────────────────────────────────────────────────────────────
st.subheader("📝 Transition Matrix P")

input_mode = st.radio(
    "Input method",
    ["Grid Editor", "Per-State Rows", "Rule Builder", "CSV Upload"],
    horizontal=True,
    help="Choose how to enter transition probabilities. All methods produce the same P matrix.",
)

P = None

# ─────────────────────────────────────────────────────────────
# MODE 1: Grid Editor
# ─────────────────────────────────────────────────────────────
if input_mode == "Grid Editor":
    st.caption("Edit cells directly. Each row must sum to 1. Best for ≤8 states.")

    if pre and len(pre["P"]) == num_states:
        P_default = np.array(pre["P"], dtype=float)[np.ix_(ordered_idx, ordered_idx)]
    else:
        P_default = np.zeros((N, N))
        for i in range(N):
            if i >= n_t:
                P_default[i, i] = 1.0

    df_P_input = pd.DataFrame(P_default, index=ordered_names, columns=ordered_names)
    edited_P = st.data_editor(df_P_input, use_container_width=True, key="grid_editor", num_rows="fixed")
    P = edited_P.values.astype(float)

# ─────────────────────────────────────────────────────────────
# MODE 2: Per-State Rows
# ─────────────────────────────────────────────────────────────
elif input_mode == "Per-State Rows":
    st.caption(
        "Set outgoing probabilities for each transient state. "
        "The **remainder** (1 − sum) auto-fills as the self-loop (stay) probability. "
        "Absorbing rows are set automatically."
    )

    if pre and len(pre["P"]) == num_states:
        P_pre = np.array(pre["P"], dtype=float)[np.ix_(ordered_idx, ordered_idx)]
    else:
        P_pre = None

    P = np.zeros((N, N))
    for j in range(n_t, N):
        P[j, j] = 1.0

    for i in range(n_t):
        with st.expander(f"**{ordered_names[i]}** → transitions", expanded=(i < 4)):
            cols = st.columns(min(N - 1, 4))
            assigned = 0.0
            col_idx = 0
            for j in range(N):
                if j == i:
                    continue
                default_val = float(P_pre[i, j]) if P_pre is not None else 0.0
                with cols[col_idx % len(cols)]:
                    val = st.number_input(
                        f"→ {ordered_names[j]}",
                        min_value=0.0, max_value=1.0,
                        value=default_val, step=0.05,
                        key=f"row_{i}_{j}",
                        format="%.2f",
                    )
                    P[i, j] = val
                    assigned += val
                col_idx += 1

            remain = max(0.0, 1.0 - assigned)
            P[i, i] = remain
            if assigned > 1.0:
                st.error(f"⚠️ Outgoing probabilities sum to {assigned:.2f} (>1). Reduce some values.")
            else:
                st.info(f"Self-loop (stay as {ordered_names[i]}): **{remain:.2f}**  |  Total: {assigned + remain:.2f}")

# ─────────────────────────────────────────────────────────────
# MODE 3: Rule Builder (sparse)
# ─────────────────────────────────────────────────────────────
elif input_mode == "Rule Builder":
    st.caption(
        "Define transition rules as **From → To = probability**. "
        "Any unassigned probability in a row becomes the self-loop. "
        "Great for large, sparse chains (10+ states)."
    )

    if "rules" not in st.session_state:
        if pre and len(pre["P"]) == num_states:
            P_pre = np.array(pre["P"], dtype=float)[np.ix_(ordered_idx, ordered_idx)]
            init_rules = []
            for i in range(n_t):
                for j in range(N):
                    if i != j and P_pre[i, j] > 0:
                        init_rules.append({"from": ordered_names[i], "to": ordered_names[j], "prob": float(P_pre[i, j])})
            st.session_state.rules = init_rules
        else:
            st.session_state.rules = []

    rules_to_remove = []
    for idx, rule in enumerate(st.session_state.rules):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            st.text(f"{rule['from']}")
        with c2:
            st.text(f"→ {rule['to']}")
        with c3:
            st.text(f"p = {rule['prob']:.2f}")
        with c4:
            if st.button("✕", key=f"rm_rule_{idx}"):
                rules_to_remove.append(idx)

    for idx in sorted(rules_to_remove, reverse=True):
        st.session_state.rules.pop(idx)
    if rules_to_remove:
        st.rerun()

    st.markdown("**Add a rule:**")
    rc1, rc2, rc3, rc4 = st.columns([3, 3, 2, 1])
    transient_names_only = ordered_names[:n_t]
    with rc1:
        new_from = st.selectbox("From", transient_names_only, key="rule_from")
    with rc2:
        other_states = [s for s in ordered_names if s != new_from]
        new_to = st.selectbox("To", other_states, key="rule_to")
    with rc3:
        new_prob = st.number_input("Prob", 0.01, 1.0, 0.10, 0.01, key="rule_prob", format="%.2f")
    with rc4:
        st.write("")
        if st.button("➕ Add", key="add_rule"):
            st.session_state.rules.append({"from": new_from, "to": new_to, "prob": new_prob})
            st.rerun()

    P = np.zeros((N, N))
    for j in range(n_t, N):
        P[j, j] = 1.0

    name_to_idx = {name: i for i, name in enumerate(ordered_names)}
    for rule in st.session_state.rules:
        fi = name_to_idx.get(rule["from"])
        ti = name_to_idx.get(rule["to"])
        if fi is not None and ti is not None and fi < n_t:
            P[fi, ti] = rule["prob"]

    for i in range(n_t):
        assigned = sum(P[i, j] for j in range(N) if j != i)
        P[i, i] = max(0.0, 1.0 - assigned)

    st.markdown("**Resulting matrix:**")
    st.dataframe(
        pd.DataFrame(P, index=ordered_names, columns=ordered_names).style.format("{:.2f}"),
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────
# MODE 4: CSV Upload
# ─────────────────────────────────────────────────────────────
elif input_mode == "CSV Upload":
    st.caption(
        "Upload a CSV where rows/columns match your state order (transient first, absorbing last). "
        "Headers optional. Best for large pre-computed matrices."
    )

    template = pd.DataFrame(
        np.zeros((N, N)),
        index=ordered_names,
        columns=ordered_names,
    )
    for j in range(n_t, N):
        template.iloc[j, j] = 1.0

    csv_buf = io.StringIO()
    template.to_csv(csv_buf)
    st.download_button("📥 Download blank template", csv_buf.getvalue(), "P_template.csv", "text/csv")

    uploaded = st.file_uploader("Upload P matrix CSV", type=["csv"])
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded, index_col=0)
            if df_up.shape != (N, N):
                st.error(f"Expected {N}×{N} matrix, got {df_up.shape[0]}×{df_up.shape[1]}")
                st.stop()
            P = df_up.values.astype(float)
            st.success("Matrix loaded!")
            st.dataframe(
                pd.DataFrame(P, index=ordered_names, columns=ordered_names).style.format("{:.4f}"),
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")
            st.stop()
    else:
        st.info("Upload a CSV to continue, or switch to another input mode.")
        st.stop()

# ─────────────────────────────────────────────────────────────
# Validate P
# ─────────────────────────────────────────────────────────────
if P is None:
    st.stop()

row_sums = P.sum(axis=1)
valid = True
for i, s in enumerate(row_sums):
    if abs(s - 1.0) > 0.02:
        st.warning(f"Row **{ordered_names[i]}** sums to {s:.4f} (should be 1.0)")
        valid = False

for j in range(n_a):
    ai = n_t + j
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
I_mat = np.eye(n_t)
IQ = I_mat - Q

try:
    F = np.linalg.inv(IQ)
except np.linalg.LinAlgError:
    st.error("(I − Q) is singular — check your Q matrix.")
    st.stop()

B = F @ R
tau = F.sum(axis=1)

# ─────────────────────────────────────────────────────────────
# What-If toggle
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔀 What-If Analysis")
st.caption("Reduce the dropout probability for any transient state and see the impact.")

win_col = 0
exit_col = n_a - 1 if n_a >= 2 else 0

whatif_on = st.toggle("Enable What-If toggle", value=False)
reduction = 0.0
whatif_state = 0

if whatif_on:
    wc1, wc2 = st.columns(2)
    with wc1:
        whatif_state = st.selectbox(
            "Which state to reduce dropout for?",
            range(n_t),
            format_func=lambda x: t_names[x],
        )
    with wc2:
        max_red = float(R[whatif_state, exit_col]) - 0.01 if R[whatif_state, exit_col] > 0.01 else 0.0
        reduction = st.slider(
            "Reduce dropout by:",
            min_value=0.0,
            max_value=max_red,
            value=0.0,
            step=0.01,
            format="%.2f",
        )

if whatif_on and reduction > 0:
    P_adj = P.copy()
    P_adj[whatif_state, n_t + exit_col] -= reduction
    P_adj[whatif_state, whatif_state] += reduction
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

p_success = B_adj[0, win_col]
p_exit = B_adj[0, exit_col] if n_a >= 2 else 1 - p_success
life_exp = tau_adj[0]
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
        st.metric("Dropout Reduction", f"−{reduction:.2f}",
                   f"from {R[whatif_state,exit_col]:.2f} → {R[whatif_state,exit_col]-reduction:.2f}")

# ─────────────────────────────────────────────────────────────
# Life expectancy bar chart
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("⏳ Life Expectancy by Starting State")
tau_df = pd.DataFrame({"Starting State": t_names, "Life Expectancy (τ)": tau_adj})
fig_tau = px.bar(
    tau_df, x="Starting State", y="Life Expectancy (τ)",
    color="Life Expectancy (τ)",
    color_continuous_scale=["#0f3460", "#64ffda"],
    title="Total Expected Steps Before Absorption",
)
fig_tau.update_layout(
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
    font_color="#e0e0e0", title_font_size=16, showlegend=False,
)
st.plotly_chart(fig_tau, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Sub-matrices
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

v1, v2, v3 = st.tabs(["Absorption Probabilities", "Expected Visits Heatmap", "State Flow Sankey"])

with v1:
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
        font_color="#e0e0e0", yaxis_range=[0, 1], title_font_size=16,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with v2:
    fig_heat = go.Figure(data=go.Heatmap(
        z=F_adj, x=t_names, y=t_names,
        colorscale=[[0, "#0e1117"], [0.5, "#1a535c"], [1, "#64ffda"]],
        text=np.round(F_adj, 3), texttemplate="%{text}", textfont={"size": 12},
    ))
    fig_heat.update_layout(
        title="Fundamental Matrix F — Expected Visits",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_size=16,
        xaxis_title="Destination State", yaxis_title="Starting State",
        yaxis_autorange="reversed",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with v3:
    sankey_labels = list(ordered_names)
    sources, targets, values, colors = [], [], [], []

    for i in range(n_t):
        for j in range(N):
            val = P[i, j] if i != j else 0
            if val > 0.005:
                sources.append(i)
                targets.append(j)
                values.append(float(val))
                colors.append(
                    "rgba(100,255,218,0.25)" if j < n_t else
                    ("rgba(255,215,0,0.4)" if j == n_t else "rgba(255,107,107,0.4)")
                )

    node_colors = ["#1a535c"] * n_t + ["#ffd700"] + ["#ff6b6b"] * max(0, n_a - 1)
    fig_sankey = go.Figure(go.Sankey(
        node=dict(pad=20, thickness=20, label=sankey_labels, color=node_colors[:N]),
        link=dict(source=sources, target=targets, value=values, color=colors),
    ))
    fig_sankey.update_layout(
        title="State Flow Diagram (transition weights)",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="#e0e0e0", title_font_size=16, height=450,
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Forensic Audit (Part 3)
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔍 Forensic Audit (Part 3 Insights)")

if n_t >= 3:
    f13 = F_adj[0, 2]
    f33 = F_adj[2, 2]
    h13 = f13 / f33 if f33 != 0 else 0
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

if n_t >= 1:
    f11_val = F_adj[0, 0]
    loop_back = (f11_val - 1) / f11_val if f11_val != 0 else 0
    st.markdown(f"**Q4 — Loop-Back Proof:**  (f₁₁ − 1)/f₁₁ = ({f11_val:.4f} − 1)/{f11_val:.4f} = **{loop_back:.4f}**  "
                f"(compare to P₁₁ = {Q_adj[0,0]:.4f})")

# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────
st.divider()
st.caption("Built for *The Viral Architect* — Probabilistic Modeling with Absorbing Markov Chains")
