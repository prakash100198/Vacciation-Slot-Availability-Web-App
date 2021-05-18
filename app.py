import datetime
import json
import numpy as np
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
from fake_useragent import UserAgent
import webbrowser
from footer_utils import image, link, layout, footer



temp_user_agent = UserAgent()
browser_header = {'User-Agent': temp_user_agent.random}

st.title("Vacciation Slot Availability Web-App")

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def import_dataset():
    df = pd.read_csv("https://raw.githubusercontent.com/prakash100198/Vaccination-Slot-Availability-Web-App/master/Combined_List.csv")
    return df

def district_mapping(state_inp,df):
    return list(df[df['State_Name']==state_inp]['District_Name'])

def column_mapping(df,col,value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def availability_check(df,col,value):
    df_temp2 = deepcopy(df.loc[df[col]>value, :])
    return df_temp2

@st.cache(allow_output_mutation=True)
def Pageviews():
    return []

mapping_df= import_dataset()
state_name = list((mapping_df['State_Name'].sort_values().unique()))
district_name = list((mapping_df['District_Name'].sort_values().unique()))
age = [18,45]

date_input = st.sidebar.slider('Select Date Range', min_value=0, max_value=50)
state_input = st.sidebar.selectbox('Select State',state_name)
district_input = st.sidebar.selectbox('Select District',district_mapping(state_input,mapping_df))
age_input = st.sidebar.selectbox('Select Minimum Age',[""]+age)
fee_input = st.sidebar.selectbox('Select Free or Paid',[""]+['Free','Paid'])
vaccine_input = st.sidebar.selectbox("Select Vaccine",[""]+['COVISHIELD','COVAXIN'])
available_input = st.sidebar.selectbox("Select Availability",[""]+['Available'])


col_rename = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'vaccine': 'Vaccine',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'block_name': 'Block Name',
    'fee_type' : 'Fees'
    }

url = 'https://www.cowin.gov.in/home'
if st.button('Book Slot'):
    webbrowser.open_new_tab(url)

DIST_ID = mapping_df[mapping_df['District_Name']==district_input]['District_ID'].values[0]

base_date = datetime.datetime.today()
date_list = [base_date+ datetime.timedelta(days = x) for x in range(date_input+1)]
date_string = [i.strftime('%d-%m-%y') for i in date_list]

final_df =None
for INP_DATE in date_string:
    URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_ID, INP_DATE)
    data = requests.get(URL,headers = browser_header)
    if (data.ok) and ('centers' in data.json()):
        data_json = data.json()['centers']
        if data_json is not None:
            data_df = pd.DataFrame(data_json)
            if len(data_df):
                data_df = data_df.explode('sessions')
                data_df['date']= data_df.sessions.apply(lambda x: x['date'])
                data_df['available_capacity']= data_df.sessions.apply(lambda x: x['available_capacity'])
                data_df['min_age_limit']= data_df.sessions.apply(lambda x: x['min_age_limit'])
                data_df['vaccine']= data_df.sessions.apply(lambda x: x['vaccine'])
                data_df = data_df[["date","state_name", "district_name", "name", "block_name", "pincode", "available_capacity", "min_age_limit", "vaccine", "fee_type"]]

                if final_df is not None:
                    final_df = pd.concat([final_df,data_df])
                else:
                    final_df = deepcopy(data_df)

        else:
            st.error('Nothing extracted from the API')
if (final_df is not None) and (len(final_df)):
    final_df.drop_duplicates(inplace=True)
    final_df.rename(columns = col_rename,inplace=True)

    if age_input != "":
        final_df = column_mapping(final_df,'Minimum Age Limit',age_input)

    if fee_input != "":
        final_df = column_mapping(final_df,'Fees',fee_input)

    if vaccine_input != "":
        final_df = column_mapping(final_df,'Vaccine',vaccine_input)

    if available_input != "":
        final_df = availability_check(final_df,'Available Capacity',0)

    pincodes = list(np.unique(final_df["Pincode"].values))
    pincode_inp = st.sidebar.selectbox('Select Pincode', [""] + pincodes)
    if pincode_inp != "":
            final_df = column_mapping(final_df, "Pincode", pincode_inp)

    final_df['Date'] = pd.to_datetime(final_df['Date'],dayfirst=True)
    final_df = final_df.sort_values(by='Date')
    final_df['Date'] = final_df['Date'].apply(lambda x:x.strftime('%d-%m-%y'))
    table = deepcopy(final_df)
    table.reset_index(inplace=True, drop=True)
    st.table(table)

else:
        st.error("Unable to fetch data currently, please try after sometime")
st.subheader('Chaos is a part of evolution!')
pageviews=Pageviews()
pageviews.append('dummy')
pg_views = len(pageviews)
footer(pg_views)
