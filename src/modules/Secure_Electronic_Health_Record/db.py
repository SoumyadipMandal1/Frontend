import pymongo
import streamlit as st

@st.cache_resource
def get_db():
    connection_string = 
    client = pymongo.MongoClient(connection_string)
    db = client["clinical_db"]
    return db
