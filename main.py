import pandas as pd
import numpy as np
import plotly.graph_objects as go 
import plotly.express as px 
import streamlit as st 
from datetime import datetime

""""define functions"""

def main():
    """Load data"""
    df_agg = pd.read_csv("Aggregated_Metrics_By_Video.csv").iloc[1:,:] #skip first row of totals
    df_agg.columns = ['Video','Video title','Video publish time',
                    'Comments added','Shares','Dislikes','Likes','Subscribers lost',
                    'Subscribers gained','RPM (USD)','CPM (USD)','Average percentage viewed (%)',
                    'Average view duration','Views','Watch time (hours)','Subcribers','Your estimated revenue (USD)',
                    'Impressions','Impressions click-through rate (%)']
    df_agg['Video publish time'] = pd.to_datetime(df_agg['Video publish time'], format="%b %d, %Y")
    df_agg['Average view duration'] = df_agg['Average view duration'].apply(lambda x: datetime.strptime(x, '%H:%M:%S'))
    df_agg['Average_duration_sec'] = df_agg['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)
    df_agg['Engagement ratio'] = (df_agg['Comments added'] + df_agg['Shares'] + df_agg['Dislikes'] + df_agg['Likes']) / df_agg.Views
    df_agg['Views/Subs gained'] = df_agg['Views'] / df_agg['Subscribers gained']
    df_agg.sort_values('Video publish time', ascending=False, inplace=True)
    
    df_agg_subs = pd.read_csv("Aggregated_Metrics_By_Country_And_Subscriber_Status.csv")
    df_comments = pd.read_csv("All_Comments_Final.csv")
    
    df_time = pd.read_csv("Video_Performance_Over_Time.csv")
    df_time['Date'] = pd.to_datetime(df_time['Date'], format='mixed', dayfirst=True)
    
    print("done")
    
"""engineer data"""


"""build dashboard"""
    
main()