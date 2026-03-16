from pymongo import MongoClient
import streamlit as st

@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGO_URI"])

client = init_connection()
db = client["mydatabase"]
collection = db["users"]
