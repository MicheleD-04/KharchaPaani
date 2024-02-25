#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pymongo
import pandas as pd
from datetime import datetime
import time

# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://db:UDb7KayB6eTqLMcd@hackathon.a83vwgw.mongodb.net/?retryWrites=true&w=majority")
db = client["hackathon"]
transactions_db = db["transactions"]

# Set page configuration including the website icon
st.set_page_config(
    page_title="KharchaPaani",
    page_icon="💰",  # Rupee emoji
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display your JPG logo
st.image("KharchaPaani.jpg", width=200)  # Adjust width as needed

# Function to query MongoDB for new data
def get_new_data():
    return list(transactions_db.find())

# Title and Description
st.title("KharchaPaani")
st.markdown(
    """
    Welcome to **KharchaPaani**, your Personal Money Manager!
    """
)

# Set budget for the month
st.sidebar.header("Set Budget")
budget = st.sidebar.number_input("Enter Budget for the Month", min_value=0.0, step=100.0)

# Main loop for polling MongoDB and updating the app
while True:
    # Retrieve expenses from MongoDB
    expenses_data = get_new_data()
    expenses_df = pd.DataFrame(expenses_data)

    # Display expenses data in a table
    st.header("Expenses Data")
    if not expenses_df.empty:
        st.dataframe(expenses_df)
    else:
        st.write("No expenses logged yet.")

    # Delay for a specified interval before polling again
    time.sleep(60)  # Polling interval: 60 seconds (adjust as needed)

