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
                   initial_sidebar_state="expanded"
                   )

alt.themes.enable("dark")

load_dotenv()
# for now it uses my api key, but eventually I'll create one just for the dashboar
client = Elasticsearch("https://localhost:9200/",
                       api_key=os.getenv('API_KEY'),
                       verify_certs=False)

# CSV path to provide details on the index mappings
csv_path = "/Users/camille/Documents/PhantomDatabase/metadata.csv"

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

#index selector
selected_index = st.sidebar.selectbox("Elasticsearch Index", ["wind"],
                                      key="selected_index")
st.session_state['display'] = False

# number of companions selector
icomp = db.get_field_values(selected_index, client, "icompanion_star")
icompanion = st.sidebar.multiselect("Number of companions",
    icomp,icomp,key='icompanion_star')

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
manual_query = None


##### TABS #####
home, search, list, plots = st.tabs(["Home", "Search", "List", "Plots"])

with home:
    st.header("Hi")
    st.write('''We can add more information here later on.  
             Some details for the users, maybe a brief description of the database,
             the models, the parameters, etc.  
             Some useful links, people to contact.''')
    st.write('''We also need a same for this thing.''')
    st.write("Also we can add a small tutorial on how to make queries using the python API, for people who want more specific queries.")
    st.write('''If you have any questions or suggestions, please contact the database administrator.''')


with search:
    st.header("Search")
    st.write('''If you need to make a specific query that goes beyond what the sidebar on the left offers, 
             you can add your own query using the search bar below. Your results can then be dispayed in the "List" tab.''')
    st.write('''To query models, first fill in the search bar with the parameters values/ranges you are looking for, and complete using the keyword
             filters below if needed. Then click on the :red-background[search] button to run the query.''')
    st.write('''The parameters selected in the sidebar will also be used for the query.''')
    st.write('''Details on the fields that can used for queries are displayed at the bottom of the page.''')
    st.write('''Please note that the search bar is for queries on numeric fields only. For queries on keywords (strings), please use the selectors in the sidebar.''')
    st.write('''If you wish to cancel your search, just click on the :red-background[search] button with an empty query.''')



    st.markdown("---")
    # search bar
    manual_query = st.text_input("Query", key="manual_query")
    # add details on the query syntax
    st.write('''The search bar is for queries on numeric variables, and should be made with the following syntax:  
             - The field name followed by a colon, then the value you are looking for.   
             - You can specifiy a range with square brackets, or curly brackets for exclusive bounds.  
             - Similarly, you can specify upper or lower bounds with the symbols >, <, >= or <=.  
             - All of the above can be combined with AND, OR, and NOT, and parentheses.''')
    
    st.write('''For example, if you want models with a mass ratio above 1, and an eccentricity between 0.5 and 0.8, you can use the following query:  
             :grey-background[eccentricity:{0.5 TO 0.8} AND mass_ratio:>1] or :grey-background[eccentricity:(>=0.5  AND <=0.8) AND mass_ratio:>1]''')
    st.write('''For more information, please refer to the Elasticsearch documentation.''')


    # Keyword selectors
    st.write("For queries on keyword fields, please use the selectors below.")
    with st.popover("Keyword filters"):
        # Version selector
        versions = db.get_field_values(selected_index, client, "version")
        version = st.multiselect("Phantom versions",
            versions,versions,key='version')
        def _select_all():
            st.session_state.version = versions
        st.button("Select all Phantom versions", on_click=_select_all)

        # Publication selector
        publications = db.get_field_values(selected_index, client, "Publication")
        publication = st.multiselect("Publications",
            publications,publications,key='publication')
        def _select_all():
            st.session_state.publication = publications
        st.button("Select both published and non-published work", on_click=_select_all)

    col1_, col2_, col3_ = st.columns((2*page_width/6, page_width/6,  2*page_width/6))
    with col1_:
        pass
    with col3_:
        pass
    with col2_:
        if st.button("Search", type='primary'):
            st.session_state['search_results'] = db.fetch_data(
                selected_index,  client, manual_query, eccentricity, massratio, sma, period,
                icompanion, publication)

    st.markdown("---")
    st.markdown("### Field details")
    st.write("Here are the field name, the type of field (int, float, etc.), its format, units, and the file it is obtained from, if applicable.")
    with open(csv_path, "r") as csvfile:
        for lines in csvfile:
            if lines.startswith("#") or lines.startswith("0"):
                continue
            cell1, cell2 = lines.strip().split(",#,")
            line = cell1.split(",")
            string = f"- :orange[{line[0]}:]"
            for s in line[1:]:
                if s != "0":
                    string+=f" {s},"
            string = string.strip(",")
            if cell2 != "0":
                string+= "\n\n" +f"   {cell2.strip('"')}"
            st.write(string.strip(","))


with list:
    st.header("List of models")
    st.write("Here is a list of the models you queried. To prevent performance issues, the list is " \
             + "hidden by default. You can display/hide the list by using the buttons below.")

    st.write("For each model, we display orbital parameters, as well as snapshots of the model"\
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
        if st.button(
                "Hide models",
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
            selected_index, client, manual_query, eccentricity, massratio, sma, period,
            icompanion, publication)
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
st.sidebar.write(str(len(st.session_state['search_results'])) + " models found")
st.write(str(len(st.session_state['search_results'])) + " models found")
