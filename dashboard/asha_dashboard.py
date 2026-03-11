import plotly.express as px
import pandas as pd
import streamlit as st

def show_dashboard():

    data = pd.DataFrame({
        "Risk":["Green","Yellow","Red"],
        "Cases":[30,10,3]
    })

    fig = px.bar(data, x="Risk", y="Cases")

    st.plotly_chart(fig)