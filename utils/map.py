import folium
import pandas as pd

def create_map(dataframe):
    if dataframe.empty or dataframe['위도'].isnull().all() or dataframe['경도'].isnull().all():
        # 기본 지도 (수원시청 중심 좌표 사용)
        m = folium.Map(location=[37.2636, 127.0286], zoom_start=12)
        return m

    map_center = [dataframe['위도'].mean(), dataframe['경도'].mean()]
    m = folium.Map(location=map_center, zoom_start=13)

    for _, row in dataframe.iterrows():
        address = row['도로명주소'] if pd.notnull(row['도로명주소']) else row['지번주소']
        popup_text = f"""
        <b>업소명:</b> {row['업소명']}<br>
        <b>업종:</b> {row['업종']}<br>
        <b>주소:</b> {address}<br>
        <b>전화:</b> {row['전화번호']}<br>
        """
        folium.Marker(
            location=[row['위도'], row['경도']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    return m
