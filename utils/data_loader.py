import pandas as pd
import streamlit as st

@st.cache_data
def load_data(filepath='datas/merged_data.csv'):
    df = pd.read_csv(filepath)
    df.dropna(subset=['위도', '경도'], inplace=True)
    return df