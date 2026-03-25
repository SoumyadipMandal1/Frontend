import pymongo
import streamlit as st
import os

@st.cache_resource
def get_db():
    connection_string = os.getenv("MONGO_URI")

    if not connection_string:
        raise ValueError("MONGO_URI is not set in environment variables")

    client = pymongo.MongoClient(connection_string)
    db = client["clinical_db"]
    return db
