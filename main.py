import pandas as pd
import numpy as np
import plotly.graph_objects as go 
import plotly.express as px 
import streamlit as st 
from datetime import datetime

#define functions
def neg_style(v, props=''):
    #style negative values
    try:
        return props if v < 0 else None
    except:
        pass
    
def pos_style(v, props=''):
    #style positive values
    try:
        return props if v > 0 else None
    except:
        pass
    
def audience_simple(country):
    #shows top countries
    if country == 'US':
        return 'USA'
    elif country == 'IN':
        return 'India'
    else:
        return 'Other'
    
def load_data():
    df_agg = pd.read_csv("Aggregated_Metrics_By_Video.csv").iloc[1:,:] #skip first row of totals
    df_agg.columns = ['Video','Video title','Video publish time',
                    'Comments added','Shares','Dislikes','Likes','Subscribers lost',
                    'Subscribers gained','RPM (USD)','CPM (USD)','Average percentage viewed (%)',
                    'Average view duration','Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)',
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
    df_time['Date'] = df_time['Date'].str.replace('Sept', 'Sep')
    df_time['Date'] = pd.to_datetime(df_time['Date'])
    
    return df_agg, df_agg_subs, df_comments, df_time

def main():
    #create dataframes from load function
    df_agg, df_agg_subs, df_comments, df_time = load_data()
    
    #engineer data
    df_agg_diff = df_agg.copy()
    metric_date_12mo = df_agg_diff['Video publish time'].max() - pd.DateOffset(months =12)
    median_agg = df_agg_diff[df_agg_diff['Video publish time'] >= metric_date_12mo].median(numeric_only=True)
    numeric_cols = np.array((df_agg_diff.dtypes == 'float64') | (df_agg_diff.dtypes == 'int64'))
    df_agg_diff.iloc[:, numeric_cols] = (df_agg_diff.iloc[:, numeric_cols] - median_agg).div(median_agg) #gives % differences

    #merge daily data with publish data to get delta 
    df_time_diff = pd.merge(df_time, df_agg.loc[:,['Video','Video publish time']], left_on ='External Video ID', right_on = 'Video')
    df_time_diff['Days published'] = (df_time_diff['Date'] - df_time_diff['Video publish time']).dt.days
    
    #last 12 months of data
    date_12mo = df_agg['Video publish time'].max() - pd.DateOffset(months=12)
    df_time_diff_year = df_time_diff[df_time_diff['Video publish time'] >= date_12mo]
    
    #daily view day for first 30 days, median, percentiles
    views_days = pd.pivot_table(df_time_diff_year, index='Days published', values='Views', aggfunc=[np.mean, np.median, lambda x: np.percentile(x, 75), lambda x: np.percentile(x, 25)]).reset_index()
    views_days.columns = ['Days published', 'Mean views', 'Median views', '75th percentile views', '25th percentile views']
    views_days = views_days[views_days['Days published'].between(0,30)]
    views_cumulative = views_days.loc[:,['Days published','Median views', '75th percentile views', '25th percentile views']]
    views_cumulative.loc[:, ['Median views', '75th percentile views', '25th percentile views']] = views_cumulative.loc[:, ['Median views', '75th percentile views', '25th percentile views']].cumsum()
    
    #build dashboard
    add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics', 'Individual Video Metrics'))
    
    if add_sidebar == 'Aggregate Metrics':
        df_agg_metrics = df_agg[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM (USD)','Average percentage viewed (%)',
                             'Average_duration_sec', 'Engagement ratio','Views/Subs gained']]
        metric_date_6mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =6)
        metric_date_12mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =12)
        metric_medians6mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_6mo].median(numeric_only=True)
        metric_medians12mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_12mo].median(numeric_only=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        columns = [col1, col2, col3, col4, col5]
        
        count = 0
        for i in metric_medians6mo.index:
            with columns[count]:
                delta = (metric_medians6mo[i] - metric_medians12mo[i]) / metric_medians12mo[i]
                st.metric(label = i, value = round(metric_medians6mo[i],1), delta = "{:.2%}".format(delta))
                count+=1
                if count >= 5:
                    count = 0
        df_agg_diff['Publish date'] = df_agg_diff['Video publish time'].apply(lambda x: x.date())
        df_agg_diff_final = df_agg_diff.loc[:, ['Video title','Publish date','Views','Likes','Subscribers','Shares','Comments added','RPM (USD)','Average percentage viewed (%)',
                             'Average_duration_sec', 'Engagement ratio','Views/Subs gained']]
        
        df_agg_numeric_cols_as_list = df_agg_diff_final.median(numeric_only=True).index.tolist()
        df_to_pct = {}
        for i in df_agg_numeric_cols_as_list:
            df_to_pct[i] = '{:.1%}'.format
            
        st.dataframe(df_agg_diff_final.style.applymap(neg_style, props='color:red').applymap(pos_style, props='color:green').format(df_to_pct))
    if add_sidebar == 'Individual Video Metrics':
        videos = tuple(df_agg['Video title'])
        video_select = st.selectbox('Pick a Video', videos)
        
        #bar chart of views by country and subscription status
        agg_filtered = df_agg[df_agg['Video title'] == video_select]
        agg_sub_filtered = df_agg_subs[df_agg_subs['Video Title'] == video_select]
        agg_sub_filtered['Country'] = agg_sub_filtered['Country Code'].apply(audience_simple)
        agg_sub_filtered.sort_values('Is Subscribed', inplace=True)
        
        fig = px.bar(agg_sub_filtered, x = 'Views', y = 'Is Subscribed', color = 'Country', orientation= 'h') 
        st.plotly_chart(fig)
        
        #line chart compare views over first 30 days
        agg_time_filtered = df_time_diff[df_time_diff['Video Title'] == video_select]
        first_30 = agg_time_filtered[agg_time_filtered['Days published'].between(0,30)]
        first_30 = first_30.sort_values('Days published')
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=views_cumulative['Days published'], y=views_cumulative['25th percentile views'], 
                                  mode='lines', 
                                  name='25th Percentile', line=dict(color='purple', dash = 'dash')))
        
        st.plotly_chart(fig2)
    
main()