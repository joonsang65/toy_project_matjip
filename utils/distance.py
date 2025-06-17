from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic

def geocode_address(address: str):
    """
    주소를 위도/경도로 변환하고 주소 상세 정보 반환
    """
    geolocator = Nominatim(user_agent="suwon-map-app")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return {
                "위도": location.latitude,
                "경도": location.longitude,
                "정확도": location.address
            }
        else:
            return None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None

def calculate_distances(df, user_location: tuple):
    """
    위경도를 기준으로 각 업소까지의 거리(km)를 계산
    """
    distance_df = df.copy()
    distance_df["거리_km"] = distance_df.apply(
        lambda row: geodesic(user_location, (row["위도"], row["경도"])).km,
        axis=1
    )
    distance_df.sort_values("거리_km", inplace=True)
    return distance_df