import folium
import pandas as pd

def create_map(dataframe, center=None, zoom=13):
    # center가 유효한 위도/경도 리스트인지 확인
    if (
        not isinstance(center, (list, tuple)) or
        len(center) != 2 or
        not all(isinstance(c, (int, float)) for c in center)
    ):
        center = [37.2636, 127.0286]  # 기본 중심: 수원시청

    if dataframe.empty or dataframe['위도'].isnull().all() or dataframe['경도'].isnull().all():
        return folium.Map(location=center, zoom_start=zoom)

    map_center = [dataframe['위도'].mean(), dataframe['경도'].mean()]
    m = folium.Map(location=map_center, zoom_start=zoom)

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
