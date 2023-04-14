import os 
os.system('pip install -r requirements.txt')

import gradio as gr
import folium
import pandas as pd 

from src.paths import PARENT_DIR


def create_map():
    url = (
        "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data"
    )
    state_geo = f"{url}/world-countries.json"
    m = folium.Map(location=[0, 0], zoom_start=2)
    
    tweet_data = pd.read_csv(PARENT_DIR/'data/output.csv')

    folium.Choropleth(
        geo_data=state_geo,
        name="choropleth",
        data=tweet_data,
        columns=["country_code", "values_norm"],
        key_on="feature.id",
        fill_color="RdBu",
        fill_opacity=0.7,
        line_opacity=1.0,
        legend_name="ChatGPT Sentiment (Negative to Positive)",
    ).add_to(m)


    # return the HTML representation of the map
    return m._repr_html_()

interface = gr.Interface(fn=create_map, inputs=None, outputs="html", 
             title="How do people feel about ChatGPT?").launch(share = False)