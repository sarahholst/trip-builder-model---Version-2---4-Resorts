import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Trip Builder Impact Model", layout="wide")

# -----------------------------
# Resort baseline data
# -----------------------------
thredbo_data = pd.DataFrame({
    "Month": ["Mar 2025", "Apr 2025", "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
              "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026"],
    "Users": [19039, 26577, 27753, 70516, 93283, 66166, 26092, 9916, 12191, 17995, 20829, 25202],
    "Conversion %": [15.25, 17.83, 11.94, 17.39, 23.47, 28.04, 23.88, 13.95, 17.73, 20.15, 18.81, 11.81],
    "AOV": [377.68, 358.49, 728.17, 363.39, 271.07, 241.58, 206.06, 186.23, 221.00, 156.29, 149.02, 439.35]
})

big_sky_data = pd.DataFrame({
    "Month": ["Mar 2025", "Apr 2025", "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
              "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026"],
    "Users": [66815, 31590, 17112, 14369, 20635, 22566, 22782, 27375, 37622, 61843, 61839, 54231],
    "Conversion %": [21.36, 19.31, 28.75, 9.99, 10.17, 10.01, 15.03, 10.88, 12.27, 14.68, 19.18, 25.60],
    "AOV": [368.50, 533.85, 1181.15, 218.20, 371.94, 573.60, 939.53, 990.45, 817.37, 683.10, 531.47, 401.77]
})

snowbird_data = pd.DataFrame({
    "Month": ["Mar 2025", "Apr 2025", "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
              "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026"],
    "Users": [53180, 23228, 17490, 15601, 24488, 28358, 34249, 37449, 18606, 54498, 49142, 54651],
    "Conversion %": [18.18, 13.78, 17.66, 9.41, 14.67, 10.96, 11.82, 6.18, 6.12, 7.85, 16.73, 20.48],
    "AOV": [283.50, 489.62, 1529.40, 110.90, 110.61, 214.44, 437.30, 358.27, 636.04, 375.12, 231.32, 213.98]
})

killington_data = pd.DataFrame({
    "Month": ["Mar 2025", "Apr 2025", "May 2025", "Jun 2025", "Jul 2025", "Aug 2025",
              "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026"],
    "Users": [63092, 27193, 8857, 11931, 11582, 18598, 22816, 36150, 77331, 109147, 115175, 100522],
    "Conversion %": [25.85, 15.18, 12.02, 29.46, 30.83, 24.60, 18.42, 20.27, 13.35, 18.66, 23.90, 28.48],
    "AOV": [224.21, 331.65, 907.93, 992.47, 177.83, 208.14, 384.04, 358.74, 312.56, 324.24, 262.68, 245.93]
})

resort_data = {
    "Thredbo": thredbo_data,
    "Big Sky": big_sky_data,
    "Snowbird": snowbird_data,
    "Killington": killington_data
}

# -----------------------------
# Helpers
# -----------------------------
def calculate_scenario(df, trip_builder_use_pct, tb_conversion_increase_pct, tb_aov_increase_pct):
    working = df.copy()

    working["Baseline Conversion"] = working["Conversion %"] / 100
    working["Trip Builder Use"] = trip_builder_use_pct / 100
    working["TB Conversion"] = working["Baseline Conversion"] * (1 + (tb_conversion_increase_pct / 100))
    working["TB AOV Multiplier"] = 1 + (tb_aov_increase_pct / 100)

    working["Baseline GMV"] = working["Users"] * working["Baseline Conversion"] * working["AOV"]

    working["TB Users"] = working["Users"] * working["Trip Builder Use"]
    working["Non-TB Users"] = working["Users"] * (1 - working["Trip Builder Use"])

    working["New GMV"] = (
        working["TB Users"] * working["TB Conversion"] * (working["AOV"] * working["TB AOV Multiplier"])
        + working["Non-TB Users"] * working["Baseline Conversion"] * working["AOV"]
    )

    total_baseline = working["Baseline GMV"].sum()
    total_new = working["New GMV"].sum()
    lift = total_new - total_baseline
    lift_pct = (lift / total_baseline * 100) if total_baseline else 0

    return {
        "monthly": working[["Month", "Baseline GMV", "New GMV"]].copy(),
        "baseline_gmv": total_baseline,
        "new_gmv": total_new,
        "lift": lift,
        "lift_pct": lift_pct
    }


def format_summary_table(df):
    formatted = df.copy()

    currency_cols = [col for col in formatted.columns if "GMV" in col or "Lift $" in col]
    pct_cols = [col for col in formatted.columns if "%" in col]

    for col in currency_cols:
        formatted[col] = formatted[col].map(lambda x: f"${x:,.0f}")
    for col in pct_cols:
        formatted[col] = formatted[col].map(lambda x: f"{x:.2f}%")

    return formatted


def add_selected_resorts_total_row(summary_df):
    totals = summary_df.drop(columns=["Resort"]).sum(numeric_only=True)

    # Recalculate lift percentages correctly from aggregated dollar values
    totals["Low Lift %"] = (totals["Low Lift $"] / totals["Baseline GMV"] * 100) if totals["Baseline GMV"] else 0
    totals["Mid Lift %"] = (totals["Mid Lift $"] / totals["Baseline GMV"] * 100) if totals["Baseline GMV"] else 0
    totals["High Lift %"] = (totals["High Lift $"] / totals["Baseline GMV"] * 100) if totals["Baseline GMV"] else 0

    totals["Resort"] = "Selected Resorts Total"

    return pd.concat([summary_df, pd.DataFrame([totals])], ignore_index=True)


# -----------------------------
# App header
# -----------------------------
st.title("Trip Builder Impact Model")
st.caption("Scenario-based model for estimating GMV impact from Trip Builder adoption across selected resorts.")

# -----------------------------
# Scenario assumptions
# -----------------------------
st.subheader("Scenario Assumptions")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    low_use = st.number_input("Low Trip Builder Use %", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
with col2:
    mid_use = st.number_input("Mid Trip Builder Use %", min_value=0.0, max_value=100.0, value=25.0, step=0.5)
with col3:
    high_use = st.number_input("High Trip Builder Use %", min_value=0.0, max_value=100.0, value=40.0, step=0.5)
with col4:
    tb_conversion_increase = st.number_input("TB Conversion % Increase", min_value=0.0, max_value=500.0, value=20.0, step=0.5)
with col5:
    tb_aov_increase = st.number_input("TB AOV % Increase", min_value=0.0, max_value=500.0, value=20.0, step=1.0)

# -----------------------------
# Editable baseline data
# -----------------------------
st.subheader("Monthly Baseline Inputs by Resort")

if "edited_resort_data" not in st.session_state:
    st.session_state.edited_resort_data = {
        resort: df.copy() for resort, df in resort_data.items()
    }

for resort in resort_data.keys():
    with st.expander(f"Edit Baseline Data — {resort}", expanded=False):
        edited_df = st.data_editor(
            st.session_state.edited_resort_data[resort],
            use_container_width=True,
            num_rows="fixed",
            key=f"editor_{resort}"
        )
        st.session_state.edited_resort_data[resort] = edited_df

# -----------------------------
# Run scenarios for all resorts
# -----------------------------
results = {}

for resort, df in st.session_state.edited_resort_data.items():
    results[resort] = {
        "Low": calculate_scenario(df, low_use, tb_conversion_increase, tb_aov_increase),
        "Mid": calculate_scenario(df, mid_use, tb_conversion_increase, tb_aov_increase),
        "High": calculate_scenario(df, high_use, tb_conversion_increase, tb_aov_increase),
    }

# -----------------------------
# Summary comparison table
# -----------------------------
summary_rows = []
for resort, scenario_set in results.items():
    low = scenario_set["Low"]
    mid = scenario_set["Mid"]
    high = scenario_set["High"]

    summary_rows.append({
        "Resort": resort,
        "Baseline GMV": mid["baseline_gmv"],
        "Low Scenario GMV": low["new_gmv"],
        "Low Lift $": low["lift"],
        "Low Lift %": low["lift_pct"],
        "Mid Scenario GMV": mid["new_gmv"],
        "Mid Lift $": mid["lift"],
        "Mid Lift %": mid["lift_pct"],
        "High Scenario GMV": high["new_gmv"],
        "High Lift $": high["lift"],
        "High Lift %": high["lift_pct"],
    })

summary_df = pd.DataFrame(summary_rows)
summary_df = add_selected_resorts_total_row(summary_df)

st.subheader("Resort Comparison Summary")
st.dataframe(format_summary_table(summary_df), use_container_width=True)

# -----------------------------
# Comparison chart
# -----------------------------
chart_source = summary_df[summary_df["Resort"] != "Selected Resorts Total"].melt(
    id_vars="Resort",
    value_vars=["Low Lift $", "Mid Lift $", "High Lift $"],
    var_name="Scenario",
    value_name="Incremental GMV"
)

fig = px.bar(
    chart_source,
    x="Resort",
    y="Incremental GMV",
    color="Scenario",
    barmode="group",
    title="Incremental GMV by Resort and Scenario"
)
fig.update_layout(xaxis_title="", yaxis_title="Incremental GMV")
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Monthly detail by resort
# -----------------------------
st.subheader("Monthly Detail by Resort (Mid Scenario)")

for resort, scenario_set in results.items():
    with st.expander(f"Monthly Detail — {resort}", expanded=False):
        monthly_df = scenario_set["Mid"]["monthly"].copy()
        monthly_df["Baseline GMV"] = monthly_df["Baseline GMV"].map(lambda x: f"${x:,.0f}")
        monthly_df["New GMV"] = monthly_df["New GMV"].map(lambda x: f"${x:,.0f}")
        st.dataframe(monthly_df, use_container_width=True)