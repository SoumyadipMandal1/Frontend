import pymongo
import streamlit as st

@st.cache_resource
def get_db():
    connection_string = "mongodb+srv://vemsaiprathikreddy_db_user:PrAtHiK123@cluster0.ktpsj2n.mongodb.net/clinical_db?appName=Cluster0"
    client = pymongo.MongoClient(connection_string)
    db = client["clinical_db"]
    return db
