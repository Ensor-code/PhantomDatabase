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
# only show error type to users, hide traceback details
st.set_option("client.showErrorDetails", "type")

alt.theme.enable("dark")

load_dotenv()
# for now it uses my api key, but eventually I'll create one just for the dashboar
client = Elasticsearch("https://localhost:9200/",
                       api_key=os.getenv('API_KEY'),
                       verify_certs=False,
                       ssl_show_warn=False)

# CSV path to provide details on the index mappings
csv_path = "/cosma/home/dr011/dc-land2/PhantomDatabase/metadata.csv"
# model data directory
model_dir = "/cosma/apps/dr011/dc-land2/database"

# Directory of assets
assets_dir = os.path.join(os.path.abspath(os.getcwd()), "assets")

# Define data labels needed for dataframe
# format is -> {elastic_field_name: "Label to display"}
dlabels = {
    "eccentricity": "Eccentricity",
    "mass_ratio": "Mass ratio",
    "semi_major_axis": "Semi-major axis (AU)",
    "period": "Orbital period (yr)",
    "icompanion_star": "Number of companions",
    "model_name": "model_name",
    "wind_mass_rate": "Mass loss rate (M_sun/yr)",
    "wind_terminal_velocity": "Wind terminal velocity (km/s)",
}

# Initialise session state variables for buttons
if "display" not in st.session_state:
    st.session_state["display"] = False
if "dl" not in st.session_state:
    st.session_state["dl"] = False

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

st.sidebar.title("Quick search 🔎")

#index selector
selected_index = st.sidebar.selectbox("Database Index", ["wind"],
                                      key="selected_index")

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
    st.header("Welcome!")
    col1_, col2_ = st.columns((2*page_width/3, page_width/3))
    with col1_:
        st.write('''  This is a database of 3D hydrodynamics models of winds around AGB stars in single and multiple systems.
                These models were computed using the Phantom code (Price et al. 2018, https://phantomsph.github.io/), an SPH code, and their aim is to study the interaction 
                of stellar winds with one or more companions.''')
        st.write('''To use this tool, please select the :grey-background[Database index] you want to query in the sidebar on the left. Then adjust the parameters ranges and filters to your needs.
                For more specific queries, you can switch to the :grey-background[Search] tab, more details are given there. The result of the query will be displayed in the :grey-background[List] tab, in the form
                of a model list, along with their parameters and snapshots of the simulations.''')
        st.write('''The plots tab contains some useful plots to explore the parameter space of our dataset. The data shown there is 
                affected by the ranges and filters selected in the sidebar and the search bar.''')
    with col2_:
        st.image(os.path.join(assets_dir,
                            "orbital.png"))

st.markdown("---")
st.write('''##### Publications   
The models accessible in this database are described in the following publications:  
- SPH modelling of AGB wind morphology in hierarchical triple systems and a comparison to observation of R Aql, Malfait et al., 2024, Astronomy & Astrophysics, Volume 691, id.A57, 17 pp.  
- Impact of H I cooling and study of accretion disks in asymptotic giant branch wind-companion smoothed particle hydrodynamic simulations, Malfait et al., 2024, Astronomy & Astrophysics, Volume 691, id.A84, 20 pp.  
- SPH modelling of companion-perturbed AGB outflows including a new morphology classification scheme, Maes et al., 2021, Astronomy & Astrophysics, Volume 653, id.A25, 18 pp.  
- SPH modelling of wind-companion interactions in eccentric AGB binary systems Malfait et al., 2021, Astronomy & Astrophysics, Volume 652, id.A51, 21 pp.  
         ''')


col1_, col2_ = st.columns((page_width/2, page_width/2))
with col1_:
    st.write('''##### Acknowlegments   
A large fraction of the models stored in this database are part of an effort to characterise the morphology of AGB winds carried by the ALMA large program ATOMIUM (https://astro-atomium.github.io/).''')
    st.write(''' This database was built in collaboration with DiRAC and the Cosma Supercomputer at Durham University, UK. It uses Elasticsearch to manage the data and queries, and streamlit to display it.
The plots showed are made using plotly, Altair (VanderPlas et al. 2018), pandas (McKinney 2010), and NumPy (Harris et al. 2020).''')
    st.write(''' This work is supported by the KU Leuven C1 excellence grant BRAVE C16/23/009.''')
    marg_l, imcol1_, imcol2_, imcol3_, marg_r = st.columns(5)
    with marg_l:
        pass
    with imcol1_:
        st.image(os.path.join(assets_dir,
                        "Atomium.png"), width='stretch')
    with imcol2_:
        st.image(os.path.join(assets_dir,
                        "DIRAC.webp"),width='stretch')
    with imcol3_:
        st.image(os.path.join(assets_dir,
                        "BRAVE.png"), width='stretch')
    with marg_r:
        pass

with col2_:
    st.write('''##### Database administrator:  
- Camille Landri, KU Leuven, Belgium  
Contact: camille.landri@kuleuven.be''')

    st.write('''##### Database contributors (in alphabetical order):  
- Taïssa Danilovich, Monash University, Australia  
- Davide Dionese, Université Libre de Bruxelles, Belgium  
- Mats Esseldeurs, KU Leuven, Belgium  
- Marcus Keil, University College London, UK  
- Jolien Malfait, previously KU Leuven, Belgium
- Lionel Siess, Université Libre de Bruxelles, Belgium  
- Owen Vermeulen, KU Leuven, Belgium  
- Jeremy Yates, University College London, UK''')


st.markdown("<p style='text-align: center;'> If you have any questions or suggestions, please reach out to the database administrators!</p>", unsafe_allow_html=True)




with search:
    st.header("Search")
    st.write('''If you need to make a specific query that goes beyond what the sidebar on the left offers, 
             you can add your own query using the search bar below. Your results can then be dispayed in the "List" tab.''')
    st.write('''To query models, first fill in the search bar with the parameters values/ranges you are looking for, and complete using the keyword
             filters below if needed. Then click on the :red-background[search] button to run the query.''')
    st.write('''The parameters selected in the sidebar will also be used for the query.
                Please restrain the search bar for queries on numeric fields. Queries on keywords (strings), e.g. publications, can be made 
                with the selector box called :grey-background[Keyword filters]. Queries on model names are allowed, but only for exact matches;
                regular expressions, wildcards and fuzzy queries are not supported for performance and security reasons.''')   
    st.write('''If you wish to cancel your search, just click on the :red-background[search] button with an empty query.''')
    st.write('''Details on the fields that can used for queries are displayed at the bottom of the page.''') 

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
        st.button("Select all Phantom versions", on_click=_select_all,width='stretch')

        # Publication selector
        publications = db.get_field_values(selected_index, client, "publication")
        publication = st.multiselect("Publications",
            publications,publications,key='publication')
        def _select_all():
            st.session_state.publication = publications
        st.button("Select all published and non-published work", on_click=_select_all,width='stretch')

    col1_, col2_, col3_ = st.columns((2*page_width/6, page_width/6,  2*page_width/6))
    with col1_:
        pass
    with col3_:
        pass
    with col2_:
        if st.button("Search", type='primary', width='stretch'):
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

# search button in the sidebar
col1_, col2_, col3_ = st.sidebar.columns([1, 2, 1])
with col1_:
    pass
with col2_:
    if col2_.button("Apply",width='stretch'):
        st.session_state['search_results'] = db.fetch_data(
            selected_index, client, manual_query, eccentricity, massratio, sma, period,
            icompanion, publication)
        on_click = st.session_state["display"] = False
        on_click = st.session_state["dl"] = False
with col3_:
    pass

with list:
    st.header("List of models")
    st.write("Here is a list of the models you queried. To prevent performance issues, the list is " \
             + "hidden by default. You can display/hide the list by using the buttons below.")
    st.write("For each model, we display orbital parameters, as well as snapshots of the model "\
             + "in the equatorial (xy) and meridional (xz) planes.")
    st.write("If you want the plots to display our whole dataset, just reset the query by refreshing the page.")
    st.write("You can download a .csv file containing the list of models fitting your query by clicking on the " \
             + "download button below. You can then choose between a file containing the model with all the parameters "\
             + "stored in the database, or just a list of the model names." \
             + " You can download the input and setup files used for a model by clicking on the relevant "\
             + "buttons below each model. If you wish to obtain a full dataset, please contact the database "\
             + "administrator and the first author of the corresponding publication (if applicable).")

    # show models buttons
    marg_l, col1_, col2_, marg_r = st.columns([1, 1,1,1])
    with marg_l:
        pass
    with col1_:
        if st.button(
            "Show/hide models",
            help="Check to display the list of models with snapshots. \n" \
            + " This may hinder performances for large queries, use at your own risks.",
            width='stretch'):
            if st.session_state['display'] == False:
                on_click = st.session_state["display"] = True
            else:
                on_click = st.session_state["display"] = False
    with col2_:
        if st.button(
                "Download list as .csv",
                help="Download the list of queried models as a .csv file. \n",
                width='stretch'):
            if len(st.session_state['search_results'])>0:
                if st.session_state['dl'] == False:
                    on_click = st.session_state["dl"] = True
                else:
                    on_click = st.session_state["dl"] = False
            else:
                st.warning("The query returned no results!")
    with marg_r:
        pass

    if st.session_state["dl"]:
        db.download_model_list(st.session_state['search_results'])

    # display model list if the box is checked
    if st.session_state['display']:
        db.update_results(st.session_state['search_results'], selected_index, model_dir)

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
            hover_data=["model_name"],
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
            hover_data=["model_name"],
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
            hover_data=["model_name"],
            title="Wind terminal velocity vs. Wind mass loss rate",
            color_discrete_sequence=px.colors.qualitative.Safe,
            opacity=0.7,
        )
        st.plotly_chart(fig)

    # circle plots
    st.write("### model_counts")
    col1_, col2_ = st.columns(2)
    count_df = data.groupby(["Eccentricity", "Mass ratio"
                             ])["model_name"].count().reset_index()
    if count_df.empty:
        st.write("No data to display")
    else:
        with col1_:
            # Eccentricity vs Mass ratio
            count_df.rename(columns={"model_name": "model_count"},
                            inplace=True)
            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Eccentricity",
                                 y="Mass ratio",
                                 size="model_count",
                                 color="model_count",
                                 hover_name="model_count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

            # Semi-major axis vs Mass ratio
            count_df = data.groupby(["Semi-major axis (AU)", "Mass ratio"
                                     ])["model_name"].count().reset_index()
            count_df.rename(columns={"model_name": "model_count"},
                            inplace=True)
            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Semi-major axis (AU)",
                                 y="Mass ratio",
                                 size="model_count",
                                 color="model_count",
                                 hover_name="model_count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

        with col2_:
            # Eccentricity vs Semi-major axis
            count_df = data.groupby(["Eccentricity", "Semi-major axis (AU)"
                                     ])["model_name"].count().reset_index()
            count_df.rename(columns={"model_name": "model_count"},
                            inplace=True)

            # make scatter plot
            fig = db.scatterplot(count_df,
                                 x="Eccentricity",
                                 y="Semi-major axis (AU)",
                                 size="model_count",
                                 color="model_count",
                                 hover_name="model_count",
                                 opacity=0.7,
                                 color_continuous_scale='Turbo')
            st.plotly_chart(fig)

            # make 3d scatter plot
            count_df = data.groupby(
                ["Eccentricity", "Mass ratio",
                 "Semi-major axis (AU)"])["model_name"].count().reset_index()
            count_df.rename(columns={"model_name": "model_count"},
                            inplace=True)
            count_df["bubble size"] = (np.sqrt(count_df['model_count']))
            sizeref = 2. * max(count_df['bubble size']) / (1000)

            fig = px.scatter_3d(
                count_df,
                x="Eccentricity",
                y="Semi-major axis (AU)",
                z="Mass ratio",
                size="bubble size",
                color="model_count",
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
