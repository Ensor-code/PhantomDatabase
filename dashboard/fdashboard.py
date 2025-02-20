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
    try:
        for result_item in results:
            # Display document
            st.markdown(f"##### {result_item['Model name']}")
            # Details arranged in columns
            col1_, col2_, col3_ = st.columns([1, 1, 1])
            # search button
            with col1_:
                if result_item['icompanion_star'] > 0:
                    # binary parameters
                    st.write(
                        f"Eccentricity: {result_item['eccentricity']}, " +
                        f"Mass ratio: {round(result_item['mass_ratio'],2)}, " +
                        f"Semi-major axis: {result_item['semi_major_axis']} AU, "
                        + f"Period: {round(result_item['period'], 2)} yrs")
                    try:
                        st.write(
                            f" Wind terminal velocity: {result_item['wind_terminal_velocity']} km/s"
                        )
                    except:
                        st.write(" Wind terminal velocity: Not available")
                    f" Wind mass loss rate: {result_item['wind_mass_rate']} Msun/yr"
                # basic model info
                st.markdown(
                    f"{result_item['icompanion_star']} companion(s), version {result_item['version']}"
                )
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
                st.markdown(
                    f" <p align=center> Close up </p>",
                    unsafe_allow_html=True)
                try:
                    st.image(
                        os.path.join(result_item['path to folder'],
                                     "orbital_zoom.png"))
                except:
                    st.markdown(
                    f" <p align=center> not available </p>",
                    unsafe_allow_html=True)

            st.write("---")

    except Exception as e:
        st.markdown(f"{result_item} ")
        st.error(f"Error performing search in Elasticsearch: {e}")


def fetch_data(index_name,
               client,
               eccentricity,
               massratio,
               sma,
               period,
               icompanion,
               version,
               publication,
               size=10000):
    '''
    Fetch data from Elasticsearch based on an optional search query, and ranges and filters applied
    '''

    import streamlit as st

    try:
        query_body = {"size": size, "query": {"bool": {"should": []}}}

        # Add binary ranges to query if needed
        if icompanion:
            if 0 not in icompanion:
                query_body["query"]["bool"]["must"] = [{
                    "range": {
                        "eccentricity": {
                            "gte": eccentricity[0],
                            "lte": eccentricity[1]
                        }
                    }
                }, {
                    "range": {
                        "mass_ratio": {
                            "gte": massratio[0],
                            "lte": massratio[1]
                        }
                    }
                }, {
                    "range": {
                        "semi_major_axis": {
                            "gte": sma[0],
                            "lte": sma[1]
                        }
                    }
                }, {
                    "range": {
                        "period": {
                            "gte": period[0],
                            "lte": period[1]
                        }
                    }
                }]

        # add filters on number of companions and Phantom version
        query_body["query"]["bool"]["filter"] = []
        if icompanion:
            query_body["query"]["bool"]["filter"].append(
                {"terms": {
                    'icompanion_star': icompanion
                }})
        if version != "All":
            query_body["query"]["bool"]["filter"].append(
                {"term": {
                    'version': version
                }})
        if publication != "All":
            if publication == "Unpublished":
                query_body["query"]["bool"]["filter"].append(
                    {"bool": {
                        "must_not": {
                            "exists": {
                                "field": "Publication"
                            }
                        }
                    }})
            else:
                query_body["query"]["bool"]["filter"].append(
                    {"term": {
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
