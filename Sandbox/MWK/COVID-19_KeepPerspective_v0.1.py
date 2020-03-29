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

def formatNumber(i,fld,incBar = True):
    perc = (Combined.iloc[i][fld] / Combined.iloc[i]['Pop']) * 100
    if incBar:
        return str("{:,}".format(Combined.iloc[i][fld]))+'</td><td class="bar bar'+str(int(round(perc)+1))+'">'+str(round(perc,3))+'%'
    else:
        return str("{:,}".format(Combined.iloc[i][fld]))+'&nbsp;&nbsp;&nbsp;'+str(round(perc,3))+'%'

url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
state_geo = f'{url}/us-states.json'
state_unemployment = f'{url}/US_Unemployment_Oct2012.csv'
state_data = pd.read_csv(state_unemployment)

folium.Choropleth(
    geo_data=state_geo,
    name='choropleth',
    data=Combined,
    columns=['State', 'Covid19Positive'],
    key_on='feature.id',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Number of People Tested Positive for COVID-19'
).add_to(m)

folium.LayerControl().add_to(m)

for i in range(0, len(Combined)-1):
#    folium.Circle(
#        location=[Combined.iloc[i]['Lat'], Combined.iloc[i]['Long']],
#        color='crimson', 
#        tooltip =   '<style>.graph-cont{   width: calc(100% - 40px);   width: 100%;   max-width: 800px;   margin: 0 auto; } .bar{   height: 30px;   max-width: 800px;   margin: 0 auto 10px auto;   line-height: 30px;   font-size: 16px;   color: white;   padding: 0 0 0 10px;   position: relative; } .bar::before{   content: "";   width: 100%;   position: absolute;   left: 0;   height: 30px;   top: 0;   z-index: -2;   background: #ecf0f1; } .bar::after{   content: "";   background: #2ecc71;   height: 30px;   transition: 0.7s;   display: block;   width: 100%;   -webkit-animation: bar-before 1 1.8s;   position: absolute;   top: 0;   left: 0;   z-index: -1; }  @-webkit-keyframes bar-before{   0%{     width: 0px;   }   100%{     width: 100%;   } }  .bar1::after{ max-width: 1%; } .bar2::after{ max-width: 2%; } .bar3::after{ max-width: 3%; } .bar4::after{ max-width: 4%; } .bar5::after{ max-width: 5%; } .bar6::after{ max-width: 6%; } .bar7::after{ max-width: 7%; } .bar8::after{ max-width: 8%; } .bar9::after{ max-width: 9%; } .bar10::after{ max-width: 10%; } .bar11::after{ max-width: 11%; } .bar12::after{ max-width: 12%; } .bar13::after{ max-width: 13%; } .bar14::after{ max-width: 14%; } .bar15::after{ max-width: 15%; } .bar16::after{ max-width: 16%; } .bar17::after{ max-width: 17%; } .bar18::after{ max-width: 18%; } .bar19::after{ max-width: 19%; } .bar20::after{ max-width: 20%; } .bar21::after{ max-width: 21%; } .bar22::after{ max-width: 22%; } .bar23::after{ max-width: 23%; } .bar24::after{ max-width: 24%; } .bar25::after{ max-width: 25%; } .bar26::after{ max-width: 26%; } .bar27::after{ max-width: 27%; } .bar28::after{ max-width: 28%; } .bar29::after{ max-width: 29%; } .bar30::after{ max-width: 30%; } .bar31::after{ max-width: 31%; } .bar32::after{ max-width: 32%; } .bar33::after{ max-width: 33%; } .bar34::after{ max-width: 34%; } .bar35::after{ max-width: 35%; } .bar36::after{ max-width: 36%; } .bar37::after{ max-width: 37%; } .bar38::after{ max-width: 38%; } .bar39::after{ max-width: 39%; } .bar40::after{ max-width: 40%; } .bar41::after{ max-width: 41%; } .bar42::after{ max-width: 42%; } .bar43::after{ max-width: 43%; } .bar44::after{ max-width: 44%; } .bar45::after{ max-width: 45%; } .bar46::after{ max-width: 46%; } .bar47::after{ max-width: 47%; } .bar48::after{ max-width: 48%; } .bar49::after{ max-width: 49%; } .bar50::after{ max-width: 50%; } .bar51::after{ max-width: 51%; } .bar52::after{ max-width: 52%; } .bar53::after{ max-width: 53%; } .bar54::after{ max-width: 54%; } .bar55::after{ max-width: 55%; } .bar56::after{ max-width: 56%; } .bar57::after{ max-width: 57%; } .bar58::after{ max-width: 58%; } .bar59::after{ max-width: 59%; } .bar60::after{ max-width: 60%; } .bar61::after{ max-width: 61%; } .bar62::after{ max-width: 62%; } .bar63::after{ max-width: 63%; } .bar64::after{ max-width: 64%; } .bar65::after{ max-width: 65%; } .bar66::after{ max-width: 66%; } .bar67::after{ max-width: 67%; } .bar68::after{ max-width: 68%; } .bar69::after{ max-width: 69%; } .bar70::after{ max-width: 70%; } .bar71::after{ max-width: 71%; } .bar72::after{ max-width: 72%; } .bar73::after{ max-width: 73%; } .bar74::after{ max-width: 74%; } .bar75::after{ max-width: 75%; } .bar76::after{ max-width: 76%; } .bar77::after{ max-width: 77%; } .bar78::after{ max-width: 78%; } .bar79::after{ max-width: 79%; } .bar80::after{ max-width: 80%; } .bar81::after{ max-width: 81%; } .bar82::after{ max-width: 82%; } .bar83::after{ max-width: 83%; } .bar84::after{ max-width: 84%; } .bar85::after{ max-width: 85%; } .bar86::after{ max-width: 86%; } .bar87::after{ max-width: 87%; } .bar88::after{ max-width: 88%; } .bar89::after{ max-width: 89%; } .bar90::after{ max-width: 90%; } .bar91::after{ max-width: 91%; } .bar92::after{ max-width: 92%; } .bar93::after{ max-width: 93%; } .bar94::after{ max-width: 94%; } .bar95::after{ max-width: 95%; } .bar96::after{ max-width: 96%; } .bar97::after{ max-width: 97%; } .bar98::after{ max-width: 98%; } .bar99::after{ max-width: 99%; } .bar100::after{ max-width: 100%; } </style>'+
#                    '<span class="graph-cont'+str(i)+'"></span>'+
#                    'State : '+str(Combined.iloc[i]['State_Name'])+'<br/>'+
#                    'Population : '+str("{:,}".format(Combined.iloc[i]['Pop']))+'<br/>'+
#                    'Total Deaths per year: '+formatNumber(i,'AllDeaths',False)+'<br/>'+
#                    '<br/>This is made up of (inc %age of State population):<table>'+
#                    '<tr><td>Cancer Deaths:</td><td>'+formatNumber(i,'CancerDeaths')+'</td></tr>'+
#                    '<tr><td>Heart Disease Deaths:</td><td>'+formatNumber(i,'HeartDiseaseDeaths')+'</td></tr>'+
#                    '<tr><td>Accidental Deaths:</td><td>'+formatNumber(i,'AccidentsDeaths')+'</td></tr>'+
#                    '<tr><td>Motor Vehicle Deaths:</td><td>'+formatNumber(i,'MotorVehicleDeaths')+'</td></tr>'+
#                    '<tr><td>Poisoning Deaths:</td><td>'+formatNumber(i,'PoisoningDeaths')+'</td></tr>'+
#                    '<tr><td>Suicide Deaths:</td><td>'+formatNumber(i,'SuicideDeaths')+'</td></tr>'+
#                    '<tr><td>Homicide Deaths:</td><td>'+formatNumber(i,'HomicideDeaths')+'</td></tr>'+
#                    '</table><br/>COVID-19 risk:<table>'+                  
#                    '<tr><td>Tested Positive:</td><td>'+formatNumber(i,'Covid19Positive')+'</td></tr>'+
#                    '<tr><td>Tested Negatives:</td><td>'+formatNumber(i,'Covid19Negative')+'</td></tr>'+
#                    '<tr><td>Hospitalised:</td><td>'+formatNumber(i,'Covid19Hospitalized')+'</td></tr>'+
#                    '<tr><td>Deaths:</td><td>'+formatNumber(i,'Covid19Death')+'</td></tr></table>',
#        radius=int(Combined.iloc[i]['Covid19Positive'])+int(Combined.iloc[i]['Covid19Negative'])).add_to(m)
    
    folium.Marker(
        [Combined.iloc[i]['Lat'], Combined.iloc[i]['Long']],
        popup='Camp Muir'
    ).add_to(m)
    
    m.add(folium.ClickForMarker(popup='Waypoint'))

    pass
    
# Open this HTML page to see the interactive map so far
m.save("samplemap.html")



