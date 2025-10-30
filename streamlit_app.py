# Ghana Population Dashboard

# Import Libraries
import streamlit as st
import pandas as pd
import os
import plotly.express as px
import altair as alt
import json

# Page Configuration
st.set_page_config(
    page_title="Ghana Population Dashboard",
    layout="wide"
)

# Load Data
@st.cache_data
def load_data():
    file_path = os.path.expanduser("ghana_population.csv")
    df = pd.read_csv(file_path)
    return df

df = load_data()

# Drop first row if it contains total Ghana population
if df.iloc[0]["Name"].lower() == "ghana":
    df = df.drop(0).reset_index(drop=True)

# --- Year Mappings ---
year_cols = {
    "2000": "Population 2000",
    "2010": "Population 2010",
    "2021": "Population 2021"
}
years = list(year_cols.keys())
value_vars = list(year_cols.values())  # for melt operations

# --- Sidebar Controls ---
st.sidebar.header("Filters")
selected_year = st.sidebar.selectbox("Select Year", years, index=2)
pop_col = year_cols[selected_year]

region_options = df["Name"].unique()
selected_regions = st.sidebar.multiselect("Select Regions", region_options, default=region_options)

min_pop = st.sidebar.slider(
    "Minimum Regional Population",
    int(df[pop_col].min()),
    int(df[pop_col].max()),
    int(df[pop_col].min())
)

# Filtered data
filtered_df = df[df["Name"].isin(selected_regions) & (df[pop_col] >= min_pop)]

# Dashboard Title & Metrics
st.title("🇬🇭 Ghana Population Insights Dashboard (2000–2021)")
st.caption("Interactive view of Ghana's regional population trends using census data from 2000, 2010, and 2021.")

# Metrics
total_pop = filtered_df[pop_col].sum()
growth_since_2000 = ((df[year_cols[selected_year]].sum() / df[year_cols['2000']].sum()) - 1) * 100
most_populous_region = filtered_df.loc[filtered_df[pop_col].idxmax(), "Name"]

col1, col2, col3 = st.columns([1.5, 4, 1.5], gap="medium")
col1.metric("Total Population", f"{total_pop:,.0f}")
col2.metric("Growth since 2000", f"{growth_since_2000:.1f}%", delta="↑")
col3.metric("Most Populous Region", most_populous_region)

# Tabs
tab_map, tab_heatmap, tab_trend = st.tabs(["Map", "Heatmap", "Trends"])

# MAP: Regional Population
with tab_map:
    st.subheader(f"Regional Population Map ({selected_year})")
    geo_path = os.path.expanduser("~/Desktop/Projects/Practice/Streeamlit/Ghana_pop/gadm41_GHA_1.json")
    try:
        with open(geo_path, "r") as f:
            gh_geojson = json.load(f)
    except FileNotFoundError:
        st.error("GeoJSON file not found. Please check the path.")
        gh_geojson = None

    # Map region names to GeoJSON
    mapping = {
        "Ahafo": "Ahafo",
        "Ashanti": "Ashanti",
        "Bono (Brong Ahafo)": "Bono",
        "Bono East": "BonoEast",
        "Central": "Central",
        "Eastern": "Eastern",
        "Greater Accra": "GreaterAccra",
        "North East": "NorthEast",
        "Northern": "Northern",
        "Oti": "Oti",
        "Savannah": "Savannah",
        "Upper East": "UpperEast",
        "Upper West": "UpperWest",
        "Volta": "Volta",
        "Western": "Western",
        "Western North": "WesternNorth"
    }
    df["Geo_Name"] = df["Name"].map(mapping)
    df_map = df[df["Name"].isin(selected_regions)]

    if gh_geojson:
        fig_map = px.choropleth(
            df_map,
            geojson=gh_geojson,
            featureidkey="properties.NAME_1",
            locations="Geo_Name",
            color=pop_col,
            hover_name="Name",
            hover_data={
                "Population 2000": True,
                "Population 2010": True,
                "Population 2021": True,
                "Geo_Name": False
            },
            color_continuous_scale="Blues",
            title=f"Ghana Regional Population ({selected_year})"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)

# HEATMAP: Regional Population Across Years
with tab_heatmap:
    st.subheader(" Heatmap: Regional Population Across Years")
    heatmap_df = df.melt(id_vars=["Name"], value_vars=value_vars, var_name="Year", value_name="Population")
    heatmap_df = heatmap_df[heatmap_df["Name"].isin(selected_regions)]
    heatmap_height = max(400, len(selected_regions)*30)

    heatmap = alt.Chart(heatmap_df).mark_rect().encode(
        x=alt.X("Year:O", title="Year"),
        y=alt.Y("Name:O", title="Region"),
        color=alt.Color("Population:Q", scale=alt.Scale(scheme='blues')),
        tooltip=["Name", "Year", "Population"]
    ).properties(width=800, height=heatmap_height)
    st.altair_chart(heatmap, use_container_width=True)

# TRENDS: Line, Bar, Pie, Stacked
with tab_trend:
    # Line chart: National Population Trend
    st.subheader(" National Population Trend")
    trend = [df[col].sum() for col in year_cols.values()]
    trend_df = pd.DataFrame({"Year": years, "Population": trend})
    fig_line = px.line(trend_df, x="Year", y="Population", markers=True, title="Ghana's Total Population (2000–2021)")
    st.plotly_chart(fig_line, use_container_width=True)

    # Bar chart: Top 10 regions
    st.subheader(f"Top 10 Most Populous Regions ({selected_year})")
    top_10 = filtered_df.sort_values(by=pop_col, ascending=False).head(10)
    fig_bar = px.bar(top_10, x="Name", y=pop_col, title=f"Top 10 Regions in {selected_year}", color=pop_col)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart: Population share
    st.subheader(f"Population Share by Region ({selected_year})")
    fig_pie = px.pie(filtered_df, names="Name", values=pop_col, title=f"Population Share in {selected_year}")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Stacked bar chart: Contribution to national population
    st.subheader("Regional Contribution to National Population Over Time")
    stacked_df = df.melt(id_vars=["Name"], value_vars=value_vars, var_name="Year", value_name="Population")
    stacked_df = stacked_df[stacked_df["Name"].isin(selected_regions)]
    stacked_df["Percent"] = stacked_df.groupby("Year")["Population"].transform(lambda x: x / x.sum() * 100)

    fig_stack = px.bar(
        stacked_df,
        x="Year",
        y="Population",
        color="Name",
        title="Regional Contribution (2000–2021)"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# Download Filtered Data
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download filtered data as CSV",
    data=csv,
    file_name="ghana_population_filtered.csv",
    mime='text/csv'
)
