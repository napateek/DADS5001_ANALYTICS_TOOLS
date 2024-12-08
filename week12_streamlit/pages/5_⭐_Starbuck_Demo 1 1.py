import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import pydeck as pdk
import numpy as np
import time
import altair as alt
from urllib.error import URLError


# ตั้งค่าหน้าสำหรับ Streamlit
st.set_page_config(page_title="Starbucks World Location", page_icon="🌍")

st.markdown("# :star2: :star2: Starbucks Location :star2: :star2:")
st.sidebar.header("Filter Options")

# เพิ่มรูปภาพ Header
# st.image("images2.jpg", use_column_width=True)

# อ่านข้อมูลจากไฟล์ CSV ที่อยู่ในโฟลเดอร์ปัจจุบัน
file_path = r"C:\Users\AS-LAB1\Mek\quiz\Starbuck.csv"
data = pd.read_csv(file_path)
#################################################################################
# ดึงคำที่สอง (index = 1) จากคอลัมน์ Timezone
data['Region'] = data['Timezone'].str.split(' ').str.get(1)
data['Region'] = data['Region'].str.split('/').str.get(0)
# ตรวจสอบผลลัพธ์
#print(data.head())
#print(data['Region'].value_counts())
#################################################################################
# ตรวจสอบว่าคอลัมน์ที่จำเป็นอยู่ใน DataFrame
if 'Region' in data.columns and 'Ownership Type' in data.columns:
    # นับจำนวนสาขาในแต่ละ Region และแยกตาม Ownership Type
    region_count = data.groupby(['Region', 'Ownership Type']).size().reset_index(name='Count')

    # สร้าง Stacked Bar Chart ด้วย Plotly
    fig = px.bar(
        region_count,
        y='Region',
        x='Count',
        color='Ownership Type',
        orientation='h',  # ทำให้ Bar Chart เป็นแนวนอน
        title='Number of Starbucks Locations by Region and Ownership Type',
        labels={'Count': 'Number of Locations', 'Region': 'Region'},
        barmode='stack',
        height=600
    )

    # แสดง Bar Chart ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("The file does not contain the required columns: 'Region' and 'Ownership Type'.")

#################################################################################

# ตรวจสอบว่าคอลัมน์ 'Latitude' และ 'Longitude' อยู่ใน DataFrame
if 'Latitude' in data.columns and 'Longitude' in data.columns:
    # แปลงคอลัมน์ Latitude และ Longitude ให้เป็น float
    data['Latitude'] = pd.to_numeric(data['Latitude'], errors='coerce')
    data['Longitude'] = pd.to_numeric(data['Longitude'], errors='coerce')

    # ลบข้อมูลที่มี Latitude หรือ Longitude เป็น NaN
    data = data.dropna(subset=['Latitude', 'Longitude'])

    # สร้างคอลัมน์สำหรับการจัดวางเลือกในแถวเดียวกัน
    col1, col2, col3 = st.columns(3)

    # สร้าง Multiple Selection Box สำหรับเลือก Region
    with col1:
        region_list = sorted(data['Region'].dropna().unique().tolist())
        selected_regions = st.multiselect("Select Regions", region_list)

    # กรองข้อมูลตาม Region ที่เลือก
    if selected_regions:
        data = data[data['Region'].isin(selected_regions)]

    # สร้าง Multiple Selection Box สำหรับเลือก Country
    with col2:
        if not data.empty:
            country_list = sorted(data['Country'].dropna().unique().tolist())
        else:
            country_list = []
        selected_countries = st.multiselect("Select Countries", country_list)

    # กรองข้อมูลตาม Country ที่เลือก
    if selected_countries:
        data = data[data['Country'].isin(selected_countries)]

    # สร้าง Multiple Selection Box สำหรับเลือก City
    with col3:
        if not data.empty:
            city_list = sorted(data['City'].dropna().unique().tolist())
        else:
            city_list = []
        selected_cities = st.multiselect("Select Cities", city_list)

    # กรองข้อมูลตาม City ที่เลือก
    if selected_cities:
        data = data[data['City'].isin(selected_cities)]

    # แสดงข้อมูลที่กรองแล้ว
    st.write("📋 **Filtered Data**", data.head())

    # สร้างแผนที่ด้วย ColumnLayer หากข้อมูลไม่ว่าง
    if not data.empty:
        layer = pdk.Layer(
            'ColumnLayer',
            data=data,
            get_position=['Longitude', 'Latitude'],
            get_elevation=100,
            elevation_scale=50,
            radius=500,
            get_fill_color=[0, 255, 0, 160],  # เปลี่ยนเป็นสีเขียว
            pickable=True,
            auto_highlight=True,
        )

        # ตั้งค่า initial view ของแผนที่
        view_state = pdk.ViewState(
            latitude=data['Latitude'].mean(),
            longitude=data['Longitude'].mean(),
            zoom=6,
            pitch=45,
        )

        # แสดงแผนที่ด้วย pydeck
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v10',
            initial_view_state=view_state,
            layers=[layer],
        ))
    else:
        st.warning("No data available for the selected filters.")
else:
    st.error("The file does not contain 'Latitude' and 'Longitude' columns.")
##############################################################################################




##############################################################################################
# ส่วนของการสร้าง Bar Chart
st.markdown("## Number of Starbucks Locations by Country")

# ตรวจสอบว่าคอลัมน์ 'Country' อยู่ใน DataFrame
if 'Country' in data.columns:
    # นับจำนวนสาขา Starbucks ในแต่ละประเทศ (ไม่สนใจการกรองเมือง)
    original_data = pd.read_csv(file_path)
    country_count = original_data['Country'].value_counts().reset_index()
    country_count.columns = ['Country', 'Count']

    # สร้าง Bar Chart ด้วย Altair
    bar_chart = alt.Chart(country_count).mark_bar().encode(
        x=alt.X('Country:N', sort='-y', title='Country'),
        y=alt.Y('Count:Q', title='Number of Locations'),
        color=alt.value('green'),
        tooltip=['Country', 'Count']
    ).properties(
        title='Number of Starbucks Locations by Country',
        width=800,
        height=400
    )

    # แสดง Bar Chart ใน Streamlit
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.error("The file does not contain a 'Country' column.")
######################################################################################

# ตรวจสอบว่าคอลัมน์ 'Country' อยู่ใน DataFrame
if 'Country' in data.columns:
    # นับจำนวนสาขา Starbucks ในแต่ละประเทศ (ไม่สนใจการกรองเมือง)
    original_data = pd.read_csv(file_path)
    country_count = original_data['Country'].value_counts().reset_index()
    country_count.columns = ['Country', 'Count']

    # สร้าง Bar Chart ด้วย Plotly
    fig = px.bar(
        country_count,
        x='Country',
        y='Count',
        color='Count',
        color_continuous_scale='Blues',
        title='Number of Starbucks Locations by Country',
        labels={'Count': 'Number of Locations', 'Country': 'Country'},
        height=600,
    )

    # แสดง Bar Chart ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("The file does not contain a 'Country' column.")


#######################################################################################
# ตรวจสอบว่าคอลัมน์ 'City' อยู่ใน DataFrame
if 'City' in data.columns:
    # สร้าง Histogram ด้วย Plotly
    fig = px.histogram(
        data,
        x='City',
        nbins=30,
        title='Distribution of Starbucks Locations by City',
        labels={'City': 'City', 'count': 'Number of Locations'},
        color_discrete_sequence=['#FF5733']
    )

    # แสดง Histogram ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("The file does not contain a 'City' column.")

#####################################################################################


# ส่วนของการสร้าง Histogram ด้วย Plotly (Top 10 Locations)
st.markdown("## Top 10 Cities with the Most Starbucks Locations")

# ตรวจสอบว่าคอลัมน์ 'City' อยู่ใน DataFrame
if 'City' in data.columns:
    # นับจำนวนสาขา Starbucks ในแต่ละเมือง
    city_count = data['City'].value_counts().reset_index()
    city_count.columns = ['City', 'Count']

    # กรองเฉพาะ Top 10 เมืองที่มีจำนวนสาขามากที่สุด
    top_10_cities = city_count.head(10)

    # สร้าง Histogram ด้วย Plotly
    fig = px.bar(
        top_10_cities,
        x='City',
        y='Count',
        color='Count',
        color_continuous_scale='Blues',
        title='Top 10 Cities with Most Starbucks Locations',
        labels={'Count': 'Number of Locations', 'City': 'City'},
        height=600,
    )

    # แสดง Histogram ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("The file does not contain a 'City' column.")

#######################################################################################

# สร้าง Scatter Plot ด้วย Plotly
st.markdown("## Starbucks Locations Scatter Plot")

if not data.empty:
    fig = px.scatter_mapbox(
        data,
        lat='Latitude',
        lon='Longitude',
        hover_name='Store Name',
        hover_data=['City', 'Country', 'Store Number'],
        color_discrete_sequence=['red'],
        zoom=5,
        height=600,
    )

    # ตั้งค่าแผนที่ให้ใช้ Mapbox
    fig.update_layout(
        mapbox_style="open-street-map",
        title='Starbucks Locations',
        margin={"r":0,"t":50,"l":0,"b":0}
    )

    # แสดง Scatter Plot ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

############################################################################################
# ตรวจสอบว่าคอลัมน์ 'Country' อยู่ใน DataFrame
if 'Country' in data.columns:
    # นับจำนวนสาขา Starbucks ในแต่ละประเทศ
    country_count = data['Country'].value_counts().reset_index()
    country_count.columns = ['Country', 'Count']

    # กรองเฉพาะ Top 10 ประเทศที่มีจำนวนสาขามากที่สุด (ถ้าต้องการ)
    top_10_countries = country_count.head(10)

    # สร้าง Pie Chart ด้วย Plotly
    fig = px.pie(
        top_10_countries,
        values='Count',
        names='Country',
        title='Top 10 Countries with Most Starbucks Locations',
        color_discrete_sequence=px.colors.sequential.RdBu,
        hole=0.4  # เพิ่ม hole เพื่อสร้าง Donut Chart
    )

    # แสดง Pie Chart ใน Streamlit
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("The file does not contain a 'Country' column.")
########################################## Continue ########################################
