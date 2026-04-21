import pandas as pd
import streamlit as st
from pathlib import Path

#page set up 
st.set_page_config(
    page_title="Air Quality Health Risk Dashboard",
    layout="wide"
)

# Loading data 
project_folder = Path(__file__).resolve().parent
data_file = project_folder / "air_quality_health_risk_assessment_cleaned.csv"

@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)

    numeric_cols = [
        "population",
        "affected_population",
        "area_km2",
        "air_pollution_avg_ug_m3",
        "air_pollution_pop_weighted_avg_ug_m3",
        "value",
        "value_lower_ci",
        "value_upper_ci",
        "value_per_100k",
        "value_per_100k_lower_ci",
        "value_per_100k_upper_ci",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

df = load_data(data_file)

#Column Check
required_cols = [
    "country",
    "nuts_name",
    "pollutant",
    "category",
    "outcome",
    "health_indicator",
    "value",
    "value_per_100k",
    "air_pollution_avg_ug_m3"
]

missing_required = [col for col in required_cols if col not in df.columns]
if missing_required:
    st.error(f"Missing required columns: {missing_required}")
    st.stop()


metric_labels = {
    "value_per_100k": "Value per 100k",
    "value": "Value",
    "air_pollution_avg_ug_m3": "Air Pollution Average (ug/m3)"
}

aggregate_names = [
    "All Countries",
    "European Environment Agency Member Countries",
    "European Union Countries"
]

def get_sorted_options(series):
    return sorted(series.dropna().astype(str).unique().tolist())

def remove_aggregates(dataframe):
    return dataframe[~dataframe["country"].isin(aggregate_names)]

def section_visible(section_name, selected_section):
    return selected_section == "Show All Sections" or selected_section == section_name

#Table of contents 
st.sidebar.title("Table of Contents")
selected_section = st.sidebar.radio(
    "Navigate",
    [
        "Show All Sections",
        "1. Overview",
        "2. Top Regions",
        "3. Country Comparison",
        "4. Pollutant Comparison",
        "5. Data Table"
    ]
)

#Title
st.title("Air Quality Health Risk Dashboard")
st.markdown(
    "This dashboard explores air quality health risk patterns across countries and NUTS regions. "
    "Each visual uses its own purpose-specific filter controls."
)

#Overview
if section_visible("1. Overview", selected_section):
    st.header("1. Overview")

    st.markdown("### Overview controls")
    c1, c2, c3 = st.columns(3)

    overview_metric = c1.radio(
        "Choose summary metric",
        ["value_per_100k", "value", "air_pollution_avg_ug_m3"],
        format_func=lambda x: metric_labels[x],
        key="overview_metric"
    )

    overview_scope = c2.radio(
        "Geographic scope",
        ["All geography entries", "Exclude aggregate geography"],
        key="overview_scope"
    )

    overview_pollutant = c3.selectbox(
        "Main pollutant focus",
        ["All"] + get_sorted_options(df["pollutant"]),
        key="overview_pollutant"
    )

    overview_df = df.copy()

    if overview_scope == "Exclude aggregate geography":
        overview_df = remove_aggregates(overview_df)

    if overview_pollutant != "All":
        overview_df = overview_df[overview_df["pollutant"] == overview_pollutant]

    overview_df = overview_df.dropna(subset=[overview_metric])

    if overview_df.empty:
        st.warning("No data available for the selected overview controls.")
    else:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Rows", f"{len(overview_df):,}")
        k2.metric("Countries", f"{overview_df['country'].nunique():,}")
        k3.metric("Regions", f"{overview_df['nuts_name'].nunique():,}")
        k4.metric(f"Average {metric_labels[overview_metric]}", f"{overview_df[overview_metric].mean():,.2f}")

    st.divider()

#Top regions
if section_visible("2. Top Regions", selected_section):
    st.header("2. Top Regions")

    st.markdown("### Filters for Top Regions chart")
    c1, c2, c3, c4 = st.columns(4)

    top_country = c1.selectbox(
        "Country focus",
        ["All"] + [c for c in get_sorted_options(df["country"]) if c not in aggregate_names],
        key="top_country"
    )

    top_metric = c2.selectbox(
        "Ranking metric",
        ["value_per_100k", "value"],
        format_func=lambda x: metric_labels[x],
        key="top_metric"
    )

    top_pollutant = c3.selectbox(
        "Pollutant",
        ["All"] + get_sorted_options(df["pollutant"]),
        key="top_pollutant"
    )

    top_n = c4.slider(
        "How many regions?",
        min_value=5,
        max_value=20,
        value=10,
        key="top_n"
    )

    top_df = remove_aggregates(df)

    if top_country != "All":
        top_df = top_df[top_df["country"] == top_country]

    if top_pollutant != "All":
        top_df = top_df[top_df["pollutant"] == top_pollutant]

    top_df = top_df.dropna(subset=[top_metric])

    if top_df.empty:
        st.warning("No data available for the selected Top Regions filters.")
    else:
        top_regions = (
            top_df.groupby("nuts_name", as_index=False)[top_metric]
            .mean()
            .sort_values(top_metric, ascending=False)
            .head(top_n)
        )

        st.bar_chart(top_regions.set_index("nuts_name")[[top_metric]])
        st.caption("This chart ranks NUTS regions using the selected metric.")
        st.dataframe(top_regions, use_container_width=True)

    st.divider()

#Country Comparison
if section_visible("3. Country Comparison", selected_section):
    st.header("3. Country Comparison")

    st.markdown("### Filters for Country Comparison chart")
    c1, c2, c3, c4 = st.columns(4)

    country_metric = c1.selectbox(
        "Comparison metric",
        ["value_per_100k", "value", "air_pollution_avg_ug_m3"],
        format_func=lambda x: metric_labels[x],
        key="country_metric"
    )

    country_category = c2.selectbox(
        "Category focus",
        get_sorted_options(df["category"]),
        key="country_category"
    )

    country_outcome = c3.selectbox(
        "Outcome focus",
        get_sorted_options(df["outcome"]),
        key="country_outcome"
    )

    country_health = c4.selectbox(
        "Health indicator focus",
        get_sorted_options(df["health_indicator"]),
        key="country_health"
    )

    country_df = remove_aggregates(df)
    country_df = country_df[
        (country_df["category"] == country_category) &
        (country_df["outcome"] == country_outcome) &
        (country_df["health_indicator"] == country_health)
    ]
    country_df = country_df.dropna(subset=[country_metric])

    if country_df.empty:
        st.warning("No data available for the selected Country Comparison filters.")
    else:
        country_chart = (
            country_df.groupby("country", as_index=False)[country_metric]
            .mean()
            .sort_values(country_metric, ascending=False)
        )

        st.bar_chart(country_chart.set_index("country")[[country_metric]])
        st.caption("This chart compares countries for one specific analytical scenario.")
        st.dataframe(country_chart, use_container_width=True)

    st.divider()

#Pollutant Comparison
if section_visible("4. Pollutant Comparison", selected_section):
    st.header("4. Pollutant Comparison")

    st.markdown("### Filters for Pollutant Comparison chart")
    c1, c2, c3, c4 = st.columns(4)

    pollutant_country = c1.selectbox(
        "Select country",
        [c for c in get_sorted_options(df["country"]) if c not in aggregate_names],
        key="pollutant_country"
    )

    region_options = get_sorted_options(df[df["country"] == pollutant_country]["nuts_name"])
    pollutant_region = c2.selectbox(
        "Select region",
        ["All"] + region_options,
        key="pollutant_region"
    )

    pollutant_metric = c3.radio(
        "Metric view",
        ["value_per_100k", "air_pollution_avg_ug_m3"],
        format_func=lambda x: metric_labels[x],
        key="pollutant_metric"
    )

    pollutant_health = c4.selectbox(
        "Health indicator",
        get_sorted_options(df["health_indicator"]),
        key="pollutant_health"
    )

    pollutant_df = remove_aggregates(df)
    pollutant_df = pollutant_df[
        (pollutant_df["country"] == pollutant_country) &
        (pollutant_df["health_indicator"] == pollutant_health)
    ]

    if pollutant_region != "All":
        pollutant_df = pollutant_df[pollutant_df["nuts_name"] == pollutant_region]

    pollutant_df = pollutant_df.dropna(subset=[pollutant_metric])

    if pollutant_df.empty:
        st.warning("No data available for the selected Pollutant Comparison filters.")
    else:
        pollutant_chart = (
            pollutant_df.groupby("pollutant", as_index=False)[pollutant_metric]
            .mean()
            .sort_values(pollutant_metric, ascending=False)
        )

        st.bar_chart(pollutant_chart.set_index("pollutant")[[pollutant_metric]])
        st.caption("This chart compares pollutants within the selected country or region.")
        st.dataframe(pollutant_chart, use_container_width=True)

    st.divider()

#Data Table
if section_visible("5. Data Table", selected_section):
    st.header("5. Data Table")

    st.markdown("### Filters for Data Table")
    c1, c2, c3 = st.columns(3)

    table_country = c1.selectbox(
        "Country",
        ["All"] + [c for c in get_sorted_options(df["country"]) if c not in aggregate_names],
        key="table_country"
    )

    if table_country == "All":
        table_region_options = ["All"] + get_sorted_options(df["nuts_name"])
    else:
        table_region_options = ["All"] + get_sorted_options(df[df["country"] == table_country]["nuts_name"])

    table_region = c2.selectbox(
        "Region",
        table_region_options,
        key="table_region"
    )

    table_rows = c3.slider(
        "Number of rows to show",
        min_value=10,
        max_value=100,
        value=25,
        step=5,
        key="table_rows"
    )

    search_term = st.text_input("Search outcome or health indicator", key="table_search")

    table_df = df.copy()

    if table_country != "All":
        table_df = table_df[table_df["country"] == table_country]

    if table_region != "All":
        table_df = table_df[table_df["nuts_name"] == table_region]

    if search_term.strip():
        search_lower = search_term.strip().lower()
        table_df = table_df[
            table_df["outcome"].astype(str).str.lower().str.contains(search_lower, na=False) |
            table_df["health_indicator"].astype(str).str.lower().str.contains(search_lower, na=False)
        ]

    st.dataframe(table_df.head(table_rows), use_container_width=True)