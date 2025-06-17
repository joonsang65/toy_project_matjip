import streamlit as st
from streamlit_folium import st_folium
from utils.data_loader import load_data
from utils.map import create_map
from utils.distance import *
from utils.model import RestaurantRecommender  # 순수 벡터 DB 모델 import

# 데이터 로드 및 추천 시스템 초기화
@st.cache_resource
def initialize_recommendation_system():
    """추천 시스템 초기화 (캐시 적용)"""
    return RestaurantRecommender("./datas/merged_data.csv")

df = load_data()
recommender = initialize_recommendation_system()

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

# --- AI 추천 시스템 추가 ---
st.markdown("---")
st.header("🤖 AI 맞춤 추천 시스템")

with st.expander("💡 음식점 추천받기", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        # 기본 추천 옵션
        st.subheader("🎯 빠른 추천")
        quick_options = [
            "가족 식사하기 좋은 곳",
            "데이트하기 좋은 곳", 
            "혼밥하기 좋은 곳",
            "회식하기 좋은 곳",
            "착한가격업소 추천",
            "모범음식점 추천"
        ]
        
        selected_quick = st.selectbox("상황을 선택하세요", ["선택하세요"] + quick_options)
        
        if st.button("빠른 추천 받기", key="quick_rec"):
            if selected_quick != "선택하세요":
                with st.spinner("추천 음식점을 찾고 있습니다..."):
                    recommendations = recommender.search(selected_quick)
                    
                    if recommendations:
                        st.success("🎉 추천 결과가 나왔습니다!")
                        st.markdown(recommendations)
                    else:
                        st.warning("추천 결과를 찾지 못했습니다. 다른 키워드로 시도해보세요.")
    
    with col2:
        # 상세 추천 옵션
        st.subheader("🔍 상세 추천")
        
        # 업종 선택
        cuisine_type = st.selectbox(
            "선호하는 음식 종류", 
            ["전체"] + sorted(df['업종'].dropna().unique().tolist())
        )
        
        # 지역 선택 (구 단위)
        districts = df['도로명주소'].dropna().str.extract(r'수원시\s+(\S+구)')[0].dropna().unique()
        selected_district = st.selectbox("선호하는 지역", ["전체"] + sorted(districts.tolist()))
        
        # 커스텀 요청
        custom_request = st.text_area(
            "추가 요청사항 (선택사항)",
            placeholder="예: 특정 음식 종류, 분위기, 원하는 조건 등"
        )
        
        if st.button("상세 추천 받기", key="detailed_rec"):
            # 추천 쿼리 구성
            query_parts = []
            
            if cuisine_type != "전체":
                query_parts.append(f"{cuisine_type}")
            
            if selected_district != "전체":
                query_parts.append(f"{selected_district}")
            
            if custom_request.strip():
                query_parts.append(custom_request.strip())
            
            if not query_parts:
                query_parts = ["맛있는 음식점"]
            
            query = " ".join(query_parts)
            
            with st.spinner("맞춤 추천을 생성하고 있습니다..."):
                recommendations = recommender.search(query)
                
                if recommendations:
                    st.success("🎉 맞춤 추천 결과가 나왔습니다!")
                    st.markdown(recommendations)
                else:
                    st.warning("추천 결과를 찾지 못했습니다. 다른 조건으로 시도해보세요.")

# 추천 히스토리 (세션 상태 활용)
if 'recommendation_history' not in st.session_state:
    st.session_state.recommendation_history = []

# 최근 추천 기록 표시
if st.session_state.recommendation_history:
    with st.expander("📋 최근 추천 기록", expanded=False):
        for i, (query, result) in enumerate(reversed(st.session_state.recommendation_history[-5:])):
            st.markdown(f"**{i+1}. {query}**")
            st.markdown(result[:200] + "..." if len(result) > 200 else result)
            st.markdown("---")

# 거리 측정 UI (주소 입력만 사용)
st.markdown("---")
with st.sidebar.expander("📏 거리 계산", expanded=False):
    st.markdown("**주소 기반 거리 계산**")
    
    address_input = st.text_input("현재 주소 입력 (예: 수원시 장안구 연무동 123-4)")
    
    if st.button("거리 계산 시작"):
        if address_input.strip():
            geocoded = geocode_address(address_input)
            if geocoded:
                user_location = (geocoded["위도"], geocoded["경도"])
                location_detail = geocoded["정확도"]
                st.success(f"📍 변환된 위치: {location_detail}")
                st.write(f"→ 위도: {user_location[0]:.6f}, 경도: {user_location[1]:.6f}")
                
                st.subheader("📌 거리 계산 결과 (최단 거리 기준)")
                distance_df = calculate_distances(filtered_df, user_location)
                if not distance_df.empty:
                    st.dataframe(distance_df[["업소명", "업종", "도로명주소", "전화번호", "거리_km"]].reset_index(drop=True))
                else:
                    st.info("선택된 업종에서 거리를 계산할 수 있는 업소가 없습니다.")
            else:
                st.error("주소 변환에 실패했습니다. 더 정확한 주소를 입력해주세요.")
        else:
            st.warning("주소를 입력해주세요.")

# 사이드바에 추천 시스템 정보 추가
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🤖 AI 추천 시스템")
    st.info("""
    **순수 벡터 DB 기반 추천**
    - 🎯 착한가격업소 & 모범음식점 정보
    - ⚡ 빠른 응답 속도
    - 📊 실제 데이터 기반 추천
    - 🔍 업종/지역별 맞춤 필터링
    """)
    
    # 추천 시스템 통계
    total_restaurants = len(df)
    total_categories = len(df['업종'].dropna().unique())
    st.metric("총 음식점 수", total_restaurants)
    st.metric("업종 수", total_categories)