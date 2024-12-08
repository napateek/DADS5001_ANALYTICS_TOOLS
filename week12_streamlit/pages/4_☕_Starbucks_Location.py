import streamlit as st
import pandas as pd
import pydeck as pdk
from urllib.error import URLError

st.set_page_config(page_title="Starbucks Locations", page_icon=":coffee:")


st.markdown("# Starbucks Locations")
st.sidebar.header("Starbucks Locations")
st.write(
    """This pages shows Starbucks Locations"""
)

df = pd.read_csv(r"C:\Users\AS-LAB1\Mek\streamlit\directory.csv", delimiter=',', encoding="utf-8-sig")
df = df.query("Country == 'TH'")
df = df.dropna(subset=['Latitude','Longitude'])
data = df.rename(columns={'Store Name':'name','Latitude':'lat','Longitude':'lon'})
data.info()
print(data.columns)
print(data.head(50))
# geo = data['lon','lat']
# name = data['name','lon','lat']

ALL_LAYERS = {
    "Starbucks": pdk.Layer(
        "HexagonLayer",
        data=data,  
        get_position=['lon','lat'],
        radius=200,
        elevation_scale=4,
        elevation_range=[100, 1000],
        extruded=True,
    ),
    "Shop Names": pdk.Layer(
        "TextLayer",
        data=data,
        get_position=['lon','lat'],
        get_text="name",
        get_color=[0, 0, 0, 200],
        get_size=10,
        get_alignment_baseline="'top'",
    )
}

st.sidebar.markdown("### Map Layers")
selected_layers = [
    layer
    for layer_name, layer in ALL_LAYERS.items()
    if st.sidebar.checkbox(layer_name, True)
]
if selected_layers:
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": 13.753,
                "longitude": 100.502,
                "zoom": 11,
                "pitch": 50,
            },
            layers=selected_layers,
        )
    )

st.write("### Store Location in Bangkok", data.head(50).sort_index())  


