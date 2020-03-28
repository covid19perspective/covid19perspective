# -*- coding: utf-8 -*-
"""

https://app.namara.io/#/organizations/5e7e1e40be428d1fd2318192/projects
https://github.com/namara-io/namara-python

https://systems.jhu.edu/research/public-health/ncov/ 
https://github.com/CSSEGISandData/COVID-19 

https://covid19api.com/

"""

from namara_local import Namara
import pandas as pd
import folium
import re # for regular expressions
import warnings
warnings.filterwarnings('ignore')

getFreshData = False # Toggle this to pull fresh data, else save the call and use an already prepared version

if getFreshData:
    namara = Namara('606734ad2c8e4078a7345e2ac501b63a58c57662d07fff48bd57fceaed95f08f')
    options = None
      
    # Data pulled from Namara, and cleaned a little    
    USData = namara.get('8e51bcce-80e3-4723-b1a0-9a0bfb665115', 'en-5', options, output_format='dataframe')
#    USData = namara.get('dd9b6bb0-88c8-48e2-a8af-ed3164858a55', 'en-0', options, output_format='dataframe')

    USData['date'] = pd.to_datetime(USData['date'])
#    yesterday = date.today() - timedelta(days = 1) 
#    USData = USData[USData['date'] == yesterday]
    USData = USData[USData['date'] == max(USData['date'])]

    # Finding the missing values 
    USData.isnull().sum()
    USData.info()
    # Replace nan with 0
    USData.fillna(0, inplace=True)
    USData.isnull().sum()
    USData.info()
    USData.to_csv('RawUSCovidData.csv', index=False)   
else:
    USData = pd.read_csv('RawUSCovidData.csv', parse_dates=['date'])

# Pulled a PDF from CDC, and used online tool to extract needed pages, and parse to Excel
# Then a little bit of data cleanup
# Rates are per 100,000 population; age-adjusted rates are per 100,000 US standard population
DeathData = pd.read_csv('nvsr68_09-508-pages-52-54-converted.csv')

# Finding the missing values 
#DeathData.isnull().sum()
#DeathData.info()
# That's ok as I would expect the US row to not have State ID etc

Combined = DeathData[['State_Name', 'State', 'Lat', 'Long']]
Combined['AllDeaths'] = DeathData['Number'].apply(lambda x: re.sub(",", "", x))
Combined['AllDeathsPer100k'] = DeathData['AgeAdjustedRate'].apply(lambda x: re.sub(",", "", x))
Combined['CancerDeaths'] = DeathData['Number.1'].apply(lambda x: re.sub(",", "", x))
Combined['CancerDeathsPer100k'] = DeathData['AgeAdjustedRate.1']
Combined['HeartDiseaseDeaths'] = DeathData['Number.2'].apply(lambda x: re.sub(",", "", x))
Combined['HeartDiseaseDeathsPer100k'] = DeathData['AgeAdjustedRate.2']
Combined['AccidentsDeaths'] = DeathData['Number.3'].apply(lambda x: re.sub(",", "", x))
Combined['AccidentsDeathsPer100k'] = DeathData['AgeAdjustedRate.3']
Combined['MotorVehicleDeaths'] = DeathData['Number.4'].apply(lambda x: re.sub(",", "", x))
Combined['MotorVehicleDeathsPer100k'] = DeathData['AgeAdjustedRate.4']
Combined['PoisoningDeaths'] = DeathData['Number.5'].apply(lambda x: re.sub(",", "", x))
Combined['PoisoninDeathsPer100k'] = DeathData['AgeAdjustedRate.5']
Combined['SuicideDeaths'] = DeathData['Number.6'].apply(lambda x: re.sub(",", "", x))
Combined['SuicideDeathsPer100k'] = DeathData['AgeAdjustedRate.6']
Combined['HomicideDeaths'] = DeathData['Number.7'].apply(lambda x: re.sub(",", "", x))
Combined['HomicideDeathsPer100k'] = DeathData['AgeAdjustedRate.7']

Combined = pd.merge(Combined, USData[['state', 'positive', 'negative', 'pending', 'hospitalized', 'death']], left_on='State', right_on='state', how='left').drop(['state'],axis=1)
Combined.rename(columns={'positive': 'Covid19Positive', 'negative': 'Covid19Negative','pending': 'Covid19Pending', 'hospitalized': 'Covid19Hospitalized', 'death': 'Covid19Death'}, inplace=True)

# Add in Population Data - downloaded from https://worldpopulationreview.com/states/
PopulationData = pd.read_csv('USPopulationData.csv')
Combined = pd.merge(Combined, PopulationData[['State','Pop']], left_on='State_Name', right_on='State', how='left').drop(['State_y'],axis=1)
Combined = Combined.dropna()
Combined['Pop'] = Combined['Pop'].astype(int)

convertToInt = ['AllDeaths', 'AllDeathsPer100k', 'CancerDeaths', 'CancerDeathsPer100k', 'HeartDiseaseDeaths', 'HeartDiseaseDeathsPer100k', \
                'AccidentsDeaths', 'AccidentsDeathsPer100k', 'MotorVehicleDeaths', 'MotorVehicleDeathsPer100k', 'PoisoningDeaths', 'PoisoninDeathsPer100k', \
                'SuicideDeaths', 'SuicideDeathsPer100k', 'HomicideDeaths', 'HomicideDeathsPer100k', 'Covid19Positive', 'Covid19Negative', \
                'Covid19Pending', 'Covid19Hospitalized', 'Covid19Death', 'Pop']
Combined[convertToInt] = Combined[convertToInt].astype(int)
Combined.rename(columns={'State_x': 'State'}, inplace=True)

# The resultant Combined DataFrame is an amalgamation of all the above
Combined.to_csv('Combined.csv', index=False)


m = folium.Map(location=[39.381266, -97.922211], tiles='cartodbpositron', min_zoom=3, max_zoom=7, zoom_start=5)

def formatNumber(i, fld):
    perc = (Combined.iloc[i][fld] / Combined.iloc[i]['Pop']) * 100
    return str("{:,}".format(Combined.iloc[i][fld]))+' ('+str(round(perc,3))+'%)'

for i in range(0, len(Combined)-1):
    folium.Circle(
        location=[Combined.iloc[i]['Lat'], Combined.iloc[i]['Long']],
        color='crimson', 
        tooltip =   'State : '+str(Combined.iloc[i]['State_Name'])+'<br/>'+
                    'Population : '+str("{:,}".format(Combined.iloc[i]['Pop']))+'<br/>'+
                    'Total Deaths per year: '+formatNumber(i,'AllDeaths')+'<br/>'+
                    '<br/><table>'+
                    '<br/>This is made up of (inc %age of State population):<table>'+
                    '<tr><td>Cancer Deaths:</td><td>'+formatNumber(i,'CancerDeaths')+'</td></tr>'+
                    '<tr><td>Heart Disease Deaths:</td><td>'+formatNumber(i,'HeartDiseaseDeaths')+'</td></tr>>'+
                    '<tr><td>Accidental Deaths:</td><td>'+formatNumber(i,'AccidentsDeaths')+'</td></tr>'+
                    '<tr><td>Motor Vehicle Deaths:</td><td>'+formatNumber(i,'MotorVehicleDeaths')+'</td></tr>'+
                    '<tr><td>Poisoning Deaths:</td><td>'+formatNumber(i,'PoisoningDeaths')+'</td></tr>'+
                    '<tr><td>Suicide Deaths:</td><td>'+formatNumber(i,'SuicideDeaths')+'</td></tr>'+
                    '<tr><td>Homicide Deaths:</td><td>'+formatNumber(i,'HomicideDeaths')+'</td></tr>'+
                    '</table><br/>COVID-19 risk:<table>'+                  
                    '<tr><td>Tested Positive:</td><td>'+formatNumber(i,'Covid19Positive')+'</td></tr>'+
                    '<tr><td>Tested Negatives:</td><td>'+formatNumber(i,'Covid19Negative')+'</td></tr>'+
                    '<tr><td>Hospitalised:</td><td>'+formatNumber(i,'Covid19Hospitalized')+'</td></tr>'+
                    '<tr><td>Deaths:</td><td>'+formatNumber(i,'Covid19Death')+'</td></tr></table>',
        radius=int(Combined.iloc[i]['Covid19Positive'])+int(Combined.iloc[i]['Covid19Negative'])).add_to(m)

# Open this HTML page to see the interactive map so far
m.save("samplemap.html")



