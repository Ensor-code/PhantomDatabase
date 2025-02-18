""" test of streamlit dahsboard"""

import os
from datetime import datetime

import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from streamlit_js_eval import streamlit_js_eval

import fdashboard as db

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# app settings
st.set_page_config(page_title="Test Dashboard",
                   page_icon="💫",
                   layout="wide",
                   initial_sidebar_state="expanded")

alt.themes.enable("dark")

load_dotenv()
client = Elasticsearch("https://localhost:9200/",
                       api_key=os.getenv('API_KEY'),
                       verify_certs=False)

# Define data labels needed for dataframe
# format is -> {elastic_field_name: "Label to display"}
dlabels = {
    "eccentricity": "Eccentricity",
    "mass_ratio": "Mass ratio",
    "semi_major_axis": "Semi-major axis (AU)",
    "period": "Orbital period (yr)",
    "icompanion_star": "Number of companions",
    "Model name": "Model name",
    "wind_mass_rate": "Mass loss rate (M_sun/yr)",
    "wind_terminal_velocity": "Wind terminal velocity (km/s)",
}

if "display" not in st.session_state:
    st.session_state["display"] = False

# page length (used for column placements)
page_width = streamlit_js_eval(
    js_expressions='window.innerWidth',
    key='WIDTH',
    want_output=True,
)
if not page_width:
    page_width = 800  # default page width value to prevent complaining about Nonetype

db.remove_upper_padding(
)  # workaround for padding issues at the top, may need to change in the future

##### SIDEBAR #####

st.sidebar.title("Welcome to the jungle! 🌴")

selected_index = st.sidebar.selectbox("Elasticsearch Index", ["wind"],
                                      key="selected_index")
st.session_state['display'] = False

# version selector
versions = db.get_field_values(selected_index, client, "version")
versions.insert(0, "All")
version = st.sidebar.selectbox("Phantom version",
                               versions,
                               key="selected_version")

# Publication selector
publications = db.get_field_values(selected_index, client, "Publication")
publications.append("Unpublished")
publications.insert(0, "All")
publication = st.sidebar.selectbox("Publication",
                                   publications,
                                   key="selected_publication")

# add checkboxes for number of companions
st.sidebar.write("Number of companions")
col1_, col2_, col3_ = st.sidebar.columns(3)
with col1_:
    comp0 = col1_.checkbox("0", key="comp_0", value=True)
with col2_:
    comp1 = col2_.checkbox("1", key="comp_1", value=True)
with col3_:
    comp2 = col3_.checkbox("2", key="comp_2", value=True)
# build companion filter for later query
icompanion = []
if comp0: icompanion.append(0)
if comp1: icompanion.append(1)
if comp2: icompanion.append(2)

# get range of binary parameters in index
ranges = {
    "eccentricity": [0.0, 1.0],
    "mass_ratio": [0.0, 2.0],
    "semi_major_axis": [2.0, 215.0],
    "period": [2.0, 2000.0]
}
for range in ranges.keys():
    ranges[range] = db.get_range(selected_index, client, range)

# Add range sliders for binary parameters
if 0 in icompanion:
    # disable them for single stars/ all models (i.e. minumum number of companions of 0)
    disable = True
else:
    disable = False

eccentricity = st.sidebar.slider(
    "Eccentricity range",
    ranges['eccentricity'][0],
    ranges['eccentricity'][1],
    (ranges['eccentricity'][0], ranges['eccentricity'][1]),
    disabled=disable)
massratio = st.sidebar.slider(
    "Mass ratio range",
    ranges['mass_ratio'][0],
    ranges['mass_ratio'][1],
    (ranges['mass_ratio'][0], ranges['mass_ratio'][1]),
    disabled=disable)
sma = st.sidebar.slider(
    "Semi-major axis range",
    ranges['semi_major_axis'][0],
    ranges['semi_major_axis'][1],
    (ranges['semi_major_axis'][0], ranges['semi_major_axis'][1]),
    disabled=disable)
period = st.sidebar.slider("Orbital period range",
                           ranges['period'][0],
                           ranges['period'][1],
                           (ranges['period'][0], ranges['period'][1]),
                           disabled=disable)

# immediate fetch of recent data, before making queries, maybe uneccessary
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = db.fetch_recent_data(selected_index,
                                                              client,
                                                              size=1000)

##### TABS #####
home, plots, list = st.tabs(["Home", "Plots", "List"])

with home:
    st.header("Hi")
    st.write("We can add more information here later on.\n")
    st.image("/Users/camille/Pictures/loop.jpg", width=600)

with list:
    st.header("List of models")
    st.write("Here is a list of the models you queried. To prevent performance issues, the list is " \
             + "hidden by default. You can display/hiding by using the buttons below.")

    st.write("For each model, we display important parameters, as well as snapshots of the model"\
             + "in the equatorial (xy) plane, showing a broad view and a close up view of the system.")

    # show models buttons
    col1_, col2_, col3_, col4_ = st.columns([1, 1, 1, 1])
    with col1_:
        pass
    with col2_:
        if st.button(
            "Show models",
            help="Check to display the list of models with snapshots. \n" \
            + " This may hinder performances for large queries, use at your own risks."
        ):
            on_click = st.session_state["display"] = True
    with col3_:
        if st.button("Hide models",
                     help="Check to hide the list of models with snapshots. \n"):
            st.session_state["display"] = False
    with col4_:
        pass
    # display model list if the box is checked
    if st.session_state['display']:
        db.update_results(st.session_state['search_results'])

# search button in the sidebar
col1_, col2_, col3_ = st.sidebar.columns([1, 1, 1])
with col1_:
    pass
with col2_:
    if col2_.button("Apply"):
        st.session_state['search_results'] = db.fetch_data(
            selected_index, client, eccentricity, massratio, sma, period,
            icompanion, version, publication)
        st.session_state["display"] = True
        # unchecked the display box
with col3_:
    pass

with plots:
    st.header("Plots")
    st.write("Here are some useful plots to explore the parameter space of our dataset." \
             + " The data shown here is affected by the ranges and filters selected in the sidebar.")

    st.write("The plots below are interactive. Hovering over data points gives extra information, and"\
             + " selecting a piece of the legend will hide the corresponding data points."\
             + " You can zoom in and out by selecting an area of the plot with your mouse, and click the"\
             + " reset button (🏠) on the interface showing at the top of each plot to go back to the original view."\
             + " You can also save the plot as a png file by clicking on the camera icon (📷) in the interface, and "\
             + "you can display the plot in full screen by clicking on the square icon.")

    # Get data
    d = {label: [] for label in dlabels.values()}
    # get data from search results
    for result in st.session_state['search_results']:
        for key, value in dlabels.items():
            if key in result.keys():
                if key == "icompanion_star":
                    d[value].append(str(result[key]))
                else:
                    d[value].append(result[key])
            else:
                d[value].append(None)
    # build dataframe
    data = pd.DataFrame(d)

    # 3D scatter plots
    st.write("### Binary parameters")
    col1_, col2_ = st.columns(2)
    with col1_:
        fig = px.scatter_3d(
            data,
            x="Eccentricity",
            y="Mass ratio",
            z="Semi-major axis (AU)",
            color="Number of companions",
            hover_data=["Model name"],
            title="Mass ratio vs. Eccentricity axis vs. Semi-major axis",
            color_discrete_sequence=px.colors.qualitative.Safe,
            opacity=0.7,
        )
        st.plotly_chart(fig)

    with col2_:
        fig = px.scatter_3d(
            data,
            x="Eccentricity",
            y="Mass ratio",
            z="Orbital period (yr)",
            color="Number of companions",
            hover_data=["Model name"],
            title="Mass ratio vs. Eccentricity axis vs. Orbital period",
            color_discrete_sequence=px.colors.qualitative.Safe,
            opacity=0.7,
        )
        st.plotly_chart(fig)

    # 2D scatter plots
    st.write("### Wind properties")
    col1_, col2_ = st.columns(2)
    with col1_:
        fig = px.scatter(
            data,
            x="Wind terminal velocity (km/s)",
            y="Mass loss rate (M_sun/yr)",
            color="Number of companions",
            hover_data=["Model name"],
            title="Wind terminal velocity vs. Wind mass loss rate",
            color_discrete_sequence=px.colors.qualitative.Safe,
            opacity=0.7,
        )
        st.plotly_chart(fig)

    # circle plots
    st.write("### Model counts")
    col1_, col2_ = st.columns(2)
    count_df = data.groupby(["Eccentricity", "Mass ratio"
                             ])["Model name"].count().reset_index()
    if count_df.empty:
        st.write("No data to display")
    else:
        with col1_:
            # Eccentricity vs Mass ratio
            count_df.rename(columns={"Model name": "Model count"},
                            inplace=True)
            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Eccentricity",
                                 y="Mass ratio",
                                 size="Model count",
                                 color="Model count",
                                 hover_name="Model count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

            # Semi-major axis vs Mass ratio
            count_df = data.groupby(["Semi-major axis (AU)", "Mass ratio"
                                     ])["Model name"].count().reset_index()
            count_df.rename(columns={"Model name": "Model count"},
                            inplace=True)
            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Semi-major axis (AU)",
                                 y="Mass ratio",
                                 size="Model count",
                                 color="Model count",
                                 hover_name="Model count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

        with col2_:
            # Eccentricity vs Semi-major axis
            count_df = data.groupby(["Eccentricity", "Semi-major axis (AU)"
                                     ])["Model name"].count().reset_index()
            count_df.rename(columns={"Model name": "Model count"},
                            inplace=True)

            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Eccentricity",
                                 y="Semi-major axis (AU)",
                                 size="Model count",
                                 color="Model count",
                                 hover_name="Model count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

            # make 3d scatter plot
            count_df = data.groupby(
                ["Eccentricity", "Mass ratio",
                 "Semi-major axis (AU)"])["Model name"].count().reset_index()
            count_df.rename(columns={"Model name": "Model count"},
                            inplace=True)
            count_df["bubble size"] = (np.sqrt(count_df['Model count']))
            sizeref = 2. * max(count_df['bubble size']) / (1000)

            fig = px.scatter_3d(
                count_df,
                x="Eccentricity",
                y="Semi-major axis (AU)",
                z="Mass ratio",
                size="bubble size",
                color="Model count",
                title="Eccentricity vs. Semi-major axis vs. Mass ratio",
                color_continuous_scale='Turbo',
                opacity=0.7,
            )
            fig.update_traces(marker=dict(line=dict(width=20, color='white')),
                              selector=dict(mode='markers'))
            fig.update_layout(scene=dict(
                xaxis=dict(
                    backgroundcolor="#cfe2f3",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white",
                ),
                yaxis=dict(backgroundcolor="#cfe2f3",
                           gridcolor="white",
                           showbackground=True,
                           zerolinecolor="white"),
                zaxis=dict(
                    backgroundcolor="#cfe2f3",
                    gridcolor="white",
                    showbackground=True,
                    zerolinecolor="white",
                ),
            ), )
            fig.update_traces(mode='markers',
                              marker=dict(sizemode='area',
                                          sizeref=sizeref,
                                          line_width=2))
            st.plotly_chart(fig)

# display query results
st.write(str(len(st.session_state['search_results'])) + " models found")
