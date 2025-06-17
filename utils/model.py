import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import re

class RestaurantRecommender:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.vectordb = None
        self.retriever = None
        self.load_data()
        
    def load_data(self):
        """데이터 로딩 및 벡터 저장소 생성"""
        print("🔄 데이터 로딩 중...")
        df = pd.read_csv(self.csv_path)
        df = df.fillna('')
        print(f"📊 총 {len(df)}개 음식점 데이터 로드됨")
        
        documents = self.create_documents(df)
        self.vectordb = self.create_vectorstore(documents)
        self.retriever = self.vectordb.as_retriever(search_kwargs={"k": 20})
        print("✅ 벡터 저장소 준비 완료!")
        
    def create_documents(self, df):
        """문서 생성"""
        documents = []
        for _, row in df.iterrows():
            # 검색 최적화된 텍스트 구성
            업소명 = str(row['업소명'])
            업종 = str(row['업종']) 
            주소 = str(row['도로명주소'])
            전화번호 = str(row['전화번호'])
            
            # 지역 정보 추출
            지역_키워드 = self.extract_location_keywords(주소)
            
            text = f"""
            업소명: {업소명}
            업종: {업종} 음식점 식당 레스토랑
            주소: {주소}
            지역: {지역_키워드}
            전화번호: {전화번호}
            
            {업소명} {업종} {주소} {지역_키워드}
            """.strip()
            
            metadata = {
                "업소명": 업소명,
                "업종": 업종,
                "주소": 주소,
                "전화번호": 전화번호,
                "지역": 지역_키워드
            }
            documents.append(Document(page_content=text, metadata=metadata))
        return documents
    
    def extract_location_keywords(self, address):
        """주소에서 지역 키워드 추출"""
        keywords = []
        
        # 구 정보
        구_pattern = r'(장안구|권선구|팔달구|영통구)'
        구_match = re.search(구_pattern, address)
        if 구_match:
            keywords.append(구_match.group(1))
            
        # 동 정보  
        동_pattern = r'([가-힣]+동)'
        동_matches = re.findall(동_pattern, address)
        keywords.extend(동_matches)
        
        # 로 정보
        로_pattern = r'([가-힣]+로)'
        로_matches = re.findall(로_pattern, address)
        keywords.extend(로_matches[:2])  # 상위 2개만
        
        return ' '.join(set(keywords))
    
    def create_vectorstore(self, documents):
        """벡터 저장소 생성"""
        embedding_model = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask"
        )
        return FAISS.from_documents(documents, embedding_model)
    
    def expand_query(self, query):
        """쿼리 확장"""
        # 업종 매핑
        cuisine_mapping = {
            "한식": ["한식", "한국음식", "한국요리", "정식", "백반", "국밥", "찌개", "갈비", "불고기"],
            "중식": ["중식", "중국음식", "중국요리", "짜장면", "짬뽕", "탕수육", "마라탕"],
            "일식": ["일식", "일본음식", "일본요리", "초밥", "라멘", "돈까스", "우동", "스시"],
            "양식": ["양식", "서양음식", "파스타", "스테이크", "피자", "햄버거"],
            "카페": ["카페", "커피", "디저트", "음료", "베이커리", "빵집"],
            "치킨": ["치킨", "닭", "프라이드", "양념치킨", "후라이드"],
            "분식": ["분식", "떡볶이", "순대", "튀김", "김밥"],
            "술집": ["술집", "포장마차", "맥주", "소주", "안주"]
        }
        
        # 지역 매핑
        location_mapping = {
            "장안": ["장안구", "장안동", "정자동", "파장동", "영화동"],
            "권선": ["권선구", "권선동", "구운동", "금곡동"],
            "팔달": ["팔달구", "팔달동", "행궁동", "매교동"],
            "영통": ["영통구", "영통동", "매탄동", "원천동"]
        }
        
        expanded_terms = [query]
        
        # 업종 확장
        for cuisine, terms in cuisine_mapping.items():
            if any(term in query for term in terms):
                expanded_terms.extend(terms[:3])  # 상위 3개만
        
        # 지역 확장  
        for region, areas in location_mapping.items():
            if region in query:
                expanded_terms.extend(areas)
                
        return " ".join(set(expanded_terms))
    
    def filter_by_category(self, docs, query):
        """업종별 필터링"""
        category_keywords = {
            "한식": ["한식"],
            "중식": ["중식", "중국"],
            "일식": ["일식", "일본"],
            "양식": ["양식", "서양"],
            "카페": ["카페", "커피"],
            "치킨": ["치킨"],
            "피자": ["피자"],
            "분식": ["분식"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query for keyword in keywords):
                filtered = [doc for doc in docs 
                          if any(kw in doc.metadata.get("업종", "") for kw in keywords)]
                if filtered:
                    return filtered[:10]  # 최대 10개
        
        return docs[:10]
    
    def filter_by_location(self, docs, query):
        """지역별 필터링"""
        location_keywords = ["구", "동", "로", "길", "장안", "권선", "팔달", "영통"]
        
        query_locations = []
        for keyword in location_keywords:
            if keyword in query:
                # 더 구체적인 지역명 찾기
                if keyword == "장안":
                    query_locations.append("장안구")
                elif keyword == "권선":
                    query_locations.append("권선구")
                elif keyword == "팔달":
                    query_locations.append("팔달구")
                elif keyword == "영통":
                    query_locations.append("영통구")
                else:
                    query_locations.append(keyword)
        
        if query_locations:
            filtered = []
            for doc in docs:
                address = doc.metadata.get("주소", "")
                if any(loc in address for loc in query_locations):
                    filtered.append(doc)
            return filtered[:10] if filtered else docs[:10]
        
        return docs[:10]
    
    def create_response(self, query, docs):
        """템플릿 기반 응답 생성"""
        if not docs:
            return "죄송합니다. 검색 조건에 맞는 음식점을 찾을 수 없습니다."
        
        # 중복 제거 (업소명 기준)
        seen_names = set()
        unique_docs = []
        for doc in docs:
            name = doc.metadata.get("업소명")
            if name not in seen_names:
                seen_names.add(name)
                unique_docs.append(doc)
        
        # 최대 5개 추천
        top_docs = unique_docs[:5]
        
        response_parts = [f"'{query}' 검색 결과 ({len(top_docs)}개 추천):\n"]
        
        for i, doc in enumerate(top_docs, 1):
            name = doc.metadata.get("업소명", "정보없음")
            category = doc.metadata.get("업종", "정보없음")
            address = doc.metadata.get("주소", "정보없음") 
            phone = doc.metadata.get("전화번호", "정보없음")
            
            response_parts.append(
                f"{i}. 🍽️ {name} ({category})\n"
                f"   📍 {address}\n"
                f"   📞 {phone}\n"
            )
        
        return "\n".join(response_parts)
    
    def search(self, query):
        """음식점 검색 및 추천"""
        # 쿼리 확장
        expanded_query = self.expand_query(query)
        
        # 벡터 검색
        retrieved_docs = self.retriever.get_relevant_documents(expanded_query)
        
        if not retrieved_docs:
            return "관련된 음식점을 찾을 수 없습니다. 다른 검색어로 시도해보세요."
        
        # 업종별 필터링
        filtered_docs = self.filter_by_category(retrieved_docs, query)
        
        # 지역별 필터링  
        final_docs = self.filter_by_location(filtered_docs, query)
        
        # 응답 생성
        return self.create_response(query, final_docs)

def main():
    # 추천 시스템 초기화
    recommender = RestaurantRecommender("/content/drive/MyDrive/코드잇/스프린트 미션/미션_17/merged_data.csv")
    
    print("🍽️ 수원시 음식점 추천 시스템입니다!")
    print("💡 예시: '한식 맛집', '장안구 중식당', '영통동 카페', '권선구 치킨집'")
    print("🚪 종료: 'exit' 입력\n")
    
    while True:
        query = input("🔍 검색어: ").strip()
        
        if query.lower() in ['exit', 'quit', '종료']:
            print("👋 시스템을 종료합니다.")
            break
            
        if not query:
            print("⚠️ 검색어를 입력해주세요.")
            continue
            
        try:
            result = recommender.search(query)
            print(f"\n{result}\n")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ 오류: {str(e)}")
