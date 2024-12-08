import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(
    page_title="Starbuck Insight",
    page_icon=":bar_chart:",
)

st.write("# Welcome to Starbuck Insight! :bar_chart: ")
st.write("**by Napatee**")
# st.sidebar.success("Select a demo above.")

file_path = r"C:\Users\AS-LAB1\Mek\quiz\Starbuck.csv"
data = pd.read_csv(file_path)

st.write("📋 **Sample Data**",data.head())


# Compare number of Store in Thailand, Indonesia, and Malaysia
st.write("📋 **Compare number of Starbuck Stores in Thailand, Indonesia, and Malaysia**")
df1 = pd.DataFrame({'name': ['Thailand','Indonesia','Malaysia'], 'count': [data['Country'].value_counts()['TH'],data['Country'].value_counts()['ID'],data['Country'].value_counts()['MY'] ] })

st.bar_chart(df1, x="name", y="count", color="name", stack=False)

# Compare number of Store in Thailand, Indonesia, and Malaysia
df = data.query("Country == 'TH'")
df = df[df['Street Address'].str.contains('Phuket')] 
df = df.dropna(subset=['Latitude','Longitude'])
data = df.rename(columns={'Store Name':'name','Latitude':'lat','Longitude':'lon'})

ALL_LAYERS = {
    "Starbucks": pdk.Layer(
        "HexagonLayer",
        data=data,  
        get_position=['lon','lat'],
        radius=200,
        elevation_scale=4,
        elevation_range=[1000, 1000],
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
                "latitude": 7.9594603361578535,
                "longitude": 98.33903195549381,
                "zoom": 11,
                "pitch": 50,
            },
            layers=selected_layers,
        )
    )

st.write("### Store Location in Bangkok", data.head(50).sort_index())  
