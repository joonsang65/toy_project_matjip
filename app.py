import streamlit as st
from streamlit_folium import st_folium
from utils.data_loader import load_data
from utils.map import create_map
from utils.distance import *

df = load_data()

st.title("📍 수원시 착한가격업소 & 모범음식점 지도")

# --- 필터링 UI ---
with st.sidebar.expander("🔍 업종 필터링", expanded=True):
    selected_category = st.multiselect(
        "업종을 선택하세요", sorted(df['업종'].dropna().unique()), default=list(df['업종'].unique())
    )
    filtered_df = df[df['업종'].isin(selected_category)] if selected_category else df.iloc[0:0]

# --- 지도 출력 ---
m = create_map(filtered_df)
st_folium(m, width=800, height=600)


# 거리 측정 UI
with st.sidebar.expander("📏 거리 계산", expanded=False):
    method = st.radio("위치 입력 방식 선택", ["위도/경도 직접 입력", "주소 입력"])

    user_location = None
    location_detail = None

    if method == "위도/경도 직접 입력":
        user_lat = st.number_input("현재 위도 입력", format="%.6f")
        user_lon = st.number_input("현재 경도 입력", format="%.6f")
        if st.button("거리 계산 시작 (좌표 기반)"):
            if user_lat and user_lon:
                user_location = (user_lat, user_lon)
            else:
                st.warning("위도와 경도를 모두 입력해주세요.")

    elif method == "주소 입력":
        address_input = st.text_input("현재 주소 입력 (예: 수원시 장안구 연무동 123-4)")
        if st.button("거리 계산 시작 (주소 기반)"):
            geocoded = geocode_address(address_input)
            if geocoded:
                user_location = (geocoded["위도"], geocoded["경도"])
                location_detail = geocoded["정확도"]
                st.success(f"📍 변환된 위치: {location_detail}")
                st.write(f"→ 위도: {user_location[0]:.6f}, 경도: {user_location[1]:.6f}")
            else:
                st.error("주소 변환에 실패했습니다. 더 정확한 주소를 입력해주세요.")

    if user_location:
        st.subheader("📌 거리 계산 결과 (최단 거리 기준)")
        distance_df = calculate_distances(filtered_df, user_location)
        if not distance_df.empty:
            st.dataframe(distance_df[["업소명", "업종", "도로명주소", "전화번호", "거리_km"]].reset_index(drop=True))
        else:
            st.info("선택된 업종에서 거리를 계산할 수 있는 업소가 없습니다.")
