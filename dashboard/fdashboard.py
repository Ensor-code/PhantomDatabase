" Functions used in dashboard.py "


def fetch_recent_data(index_name, client, size=1000):
    """
    Fetch recent data from Elasticsearch using no extra filters
    """
    from elasticsearch import Elasticsearch
    import streamlit as st
    try:
        query_body = {
            "size": size,
            "sort": [
                {
                    "model date": {
                        "order": "desc"
                    }
                },  # Primary sort by date
            ]
        }

        response = client.search(index=index_name, body=query_body)
        return [hit['_source'] for hit in response['hits']['hits']]

    except Exception as e:
        st.error(f"Error fetching recent data from Elasticsearch: {e}")
        return []


def get_field_values(index_name, client, field):
    '''
    Get all unique values for a field in the index
    '''
    from elasticsearch import Elasticsearch

    aggregation = {"unique_values": {"terms": {"field": field, "size": 10000}}}

    values = client.search(index=index_name, body={"aggs": aggregation})

    return [
        _['key'] for _ in values['aggregations']['unique_values']['buckets']
    ]


def get_range(index_name, client, field) -> tuple:
    '''
    Get the minimum and maximum values for a field in the index
    '''
    from elasticsearch import Elasticsearch

    max_aggregation = {"max_val": {"max": {"field": field}}}

    min_aggregation = {"min_val": {"min": {"field": field}}}

    max_result = client.search(index=index_name,
                               body={"aggs": max_aggregation})
    min_result = client.search(index=index_name,
                               body={"aggs": min_aggregation})

    max = max_result['aggregations']['max_val']['value']
    min = min_result['aggregations']['min_val']['value']

    return min, max


def update_results(results):
    '''
    Update the results of the search
    '''
    import os
    import streamlit as st
    import streamlit_ext as ste
    try:
        for result_item in results:
            # Display document
            st.markdown(f"##### {result_item['Model name']}")
            # Details arranged in columns
            col1_, col2_, col3_ = st.columns([1, 1, 1])
            # search button
            with col1_:
                # basic model info
                st.markdown(
                    f"{result_item['icompanion_star']} companion(s), version {result_item['version']}"
                )
                if result_item['icompanion_star'] == 1:
                    # binary parameters
                    st.write(
                        f"Binary parameters: e={result_item['eccentricity']}, q={round(result_item['mass_ratio'],2)},"
                        +
                        f" a={round(result_item['semi_major_axis'],2)} AU, P={round(result_item['period'],2)} days"
                    )
                elif result_item['icompanion_star'] == 2:
                    if result_item['subst'] == 11:
                        st.write(
                            f"Wide binary: e={result_item['eccentricity']}, q={round(result_item['mass_ratio'],2)}, i={result_item['inclination']},"
                            +
                            f" a={round(result_item['semi_major_axis'],2)} AU, P={round(result_item['period'],2)} days"
                        )
                        st.write(
                            f"Tight binary (M1 and M2): e={result_item['binary2_e']}, q={round(result_item['secondary_mass']/result_item['primary_mass'],2)},"
                            +
                            f" a={round(result_item['binary2_a'],2)} AU, P={round(result_item['binary2_p'],2)} days"
                        )
                    elif result_item['subst'] == 12:
                        st.write(
                            f"Wide binary: e={result_item['eccentricity']}, q={round(result_item['mass_ratio'],2)}, i={result_item['inclination']},"
                            +
                            f" a={round(result_item['semi_major_axis'],2)} AU, P={round(result_item['period'],2)} days"
                        )
                        st.write(
                            f"Tight binary (M2 and M3): e={result_item['binary2_e']}, q={round(result_item['tertiary_mass']/result_item['secondary_mass'],2)},"
                            +
                            f" a={round(result_item['binary2_a'],2)} AU, P={round(result_item['binary2_p'],2)} days"
                        )
                try:
                    st.write(
                        f" Wind terminal velocity: {round(result_item['wind_terminal_velocity'],2)} km/s"
                    )
                except:
                    st.write(" Wind terminal velocity: Not available")
                f" Wind mass loss rate: {result_item['wind_mass_rate']} Msun/yr"
                try:
                    st.markdown(f"Published in {result_item['Publication']}")
                except:
                    st.markdown(f"Unpublished")
                # timestamp
                timestamp = result_item.get('model date', '')
                if timestamp:
                    st.write(f"ran on {timestamp}")

            with col2_:
                st.markdown(
                    f"<p align=center> Equatorial slice (XY plane) </p>",
                    unsafe_allow_html=True)
                try:
                    st.image(
                        os.path.join(result_item['path to folder'],
                                     "orbital.png"))
                except:
                    st.markdown(
                        f" <p align=center> snapshot not available </p>",
                        unsafe_allow_html=True)
            with col3_:
                st.markdown(f" <p align=center> Close up </p>",
                            unsafe_allow_html=True)
                try:
                    st.image(
                        os.path.join(result_item['path to folder'],
                                     "orbital_zoom.png"))
                except:
                    st.markdown(f" <p align=center> not available </p>",
                                unsafe_allow_html=True)
            col1_, col2_, col3_, col4_ = st.columns([1, 1, 1, 1])
            with col1_:
                pass
            with col2_:
                with open(
                        os.path.join(result_item['path to folder'], 'wind.in'),
                        "rb") as f:
                    # regular dl buttons refresh the state of the page so we use streamlit_ext buttons
                    ste.download_button(
                        "Download .in file",
                        data=f,
                        file_name='wind.in',
                    )
            with col3_:
                with open(
                        os.path.join(result_item['path to folder'],
                                     'wind.setup'), "rb") as f:
                    ste.download_button(
                        "Download .setup file",
                        data=f,
                        file_name='wind.setup',
                    )
            with col4_:
                pass

            with st.expander("More details", icon='🔥'):
                st.write(
                    'Here are all the model parameters stored in the database:'
                )
                st.write(
                    '(see the home page for more details on the meaning and units of each parameter)'
                )
                for key, value in result_item.items():
                    st.write(f"**{key}**: {value}")

            st.write("---")

    except Exception as e:
        st.markdown(f"{result_item} ")
        st.error(f"Error performing search in Elasticsearch: {e}")


def fetch_data(index_name,
               client,
               manual_query,
               eccentricity,
               massratio,
               sma,
               period,
               icompanion,
               publication,
               size=10000):
    '''
    Fetch data from Elasticsearch based on an optional search query, and ranges and filters applied
    '''

    import streamlit as st

    try:
        query_body = {"size": size, "query": {"bool": {"should": []}}}
        query_body["query"]["bool"]["must"] = []

        # Add manual query if needed
        if manual_query:
            query_body["query"]["bool"]["must"].append(
                {"query_string": {
                    "query": manual_query,
                    "default_field": "mass ratio"
                }})

        # Add binary ranges to query if needed
        if icompanion:
            if 0 not in icompanion:
                query_body["query"]["bool"]["must"].append({
                    "range": {
                        "eccentricity": {
                            "gte": eccentricity[0],
                            "lte": eccentricity[1]
                        }
                    }})
                query_body["query"]["bool"]["must"].append({
                    "range": {
                        "mass_ratio": {
                            "gte": massratio[0],
                            "lte": massratio[1]
                        }
                    }})
                query_body["query"]["bool"]["must"].append({
                    "range": {
                        "semi_major_axis": {
                            "gte": sma[0],
                            "lte": sma[1]
                        }
                    }})
                query_body["query"]["bool"]["must"].append({
                    "range": {
                        "period": {
                            "gte": period[0],
                            "lte": period[1]
                        }
                    }})

        # add filters on number of companions
        query_body["query"]["bool"]["filter"] = []
        if icompanion:
            query_body["query"]["bool"]["filter"].append(
                {"terms": {
                    'icompanion_star': icompanion
                }})
        if publication:
                query_body["query"]["bool"]["filter"].append(
                    {"terms": {
                        'Publication': publication
                    }})

        # Query
        result = client.search(index=index_name, body=query_body)

        return [hit['_source'] for hit in result['hits']['hits']]

    except Exception as e:
        st.error(f"Error fetching data from Elasticsearch: {e}")
        return []


def scatterplot(data, x, y, size, color, hover_name, opacity,
                color_continuous_scale):
    '''
    Create a scatter plot using Plotly Express
    '''
    import plotly.express as px

    fig = px.scatter(
        data,
        x=x,
        y=y,
        size=size,
        color=color,
        hover_name=hover_name,
        #log_x=True,
        #log_y=True,
        opacity=opacity,
        color_continuous_scale=color_continuous_scale,
    )

    fig.update_layout(plot_bgcolor="#cfe2f3")
    fig.update_xaxes(nticks=10)
    fig.update_xaxes(showgrid=True,
                     gridwidth=1,
                     gridcolor='white',
                     zerolinecolor='white',
                     linecolor='white',
                     mirror=True)
    fig.update_yaxes(showgrid=True,
                     gridwidth=1,
                     gridcolor='white',
                     zerolinecolor='white',
                     linecolor='white',
                     mirror=True)

    return fig


def remove_upper_padding():
    '''
    Uses CSS to remove padding at the top of the page
    '''
    import streamlit as st
    st.markdown("""
    <style>
    
           /* Remove blank space at top and bottom */ 
           .block-container {
               padding-top: 0rem;
               padding-bottom: 0rem;
            }
           
           /* Remove blank space at the center canvas */ 
           .st-emotion-cache-z5fcl4 {
               position: relative;
               top: -62px;
               }
           
           /* Make the toolbar transparent and the content below it clickable */ 
           .st-emotion-cache-18ni7ap {
               pointer-events: none;
               background: rgb(255 255 255 / 0%)
               }
           .st-emotion-cache-zq5wmm {
               pointer-events: auto;
               background: rgb(255 255 255);
               border-radius: 5px;
               }
    </style>
    """,
                unsafe_allow_html=True)
