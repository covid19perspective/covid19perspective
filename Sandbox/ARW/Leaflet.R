library(leaflet)
library(tidyverse)
library(leaflet.extras)

mydata<-read.csv("/Users/andywilson1/Documents/GitHub/covid19perspective/Sandbox/MWK/Combined.csv")
#BRFSS
brfss <- read.csv("/Users/andywilson1/Desktop/Weight/behavioral-risk-factor-surveillance-system-brfss-prevalence-data-2011-to-present.csv")
brfss$State <- brfss$locationabbr
brfss_trim <- brfss %>%
  filter(year == 2018) %>% 
  filter(break_out =="Overall") %>%
  filter(question == "Health Status (variable calculated from one or more BRFSS questions)") %>%
  filter(response == "Fair or Poor Health") %>%
  select(State, data_value)

mydata <- merge(mydata, brfss_trim, by="State", all=F)

## Velocities
CovJHU_3.28 <- read.csv(url("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/03-28-2020.csv"))
CovJHU_3.27 <- read.csv(url("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/03-27-2020.csv"))

#Get cases by state

CovJHU_3.28_sum <- CovJHU_3.28 %>%
  filter(Country_Region =="US") %>%
  group_by(Province_State) %>%
  summarise(total_confirmed28 = sum(Confirmed), total_deaths28= sum(Deaths))

CovJHU_3.27_sum <- CovJHU_3.27 %>%
  filter(Country_Region =="US") %>%
  group_by(Province_State) %>%
  summarise(total_confirmed27 = sum(Confirmed), total_deaths27= sum(Deaths))

COV27_28 <-merge(CovJHU_3.28_sum, CovJHU_3.27_sum)

COV27_28$confirm_change <-((COV27_28$total_confirmed28-COV27_28$total_confirmed27)/COV27_28$total_confirmed27)*100
COV27_28$deaths_change <-((COV27_28$total_deaths28-COV27_28$total_deaths27)/COV27_28$total_deaths27)*100
COV27_28$State_Name <- COV27_28$Province_State

Updated<- merge(COV27_28, mydata, by="State_Name", all=F)


states <- geojsonio::geojson_read("/Users/andywilson1/Desktop/Leaflet/gz_2010_us_040_00_500k.json", what = "sp")
mydata$NAME<-mydata$State_Name

mydf <- sp::merge(states, Updated, by="NAME", all=F)

mydf$CovRisk <- log(round((mydf$Covid19Positive/mydf$Pop)*100000))*(mydf$data_value/100)*(mydf$confirm_change/12)

summary(mydf$CovRisk)

labels <- paste("<b>", mydf$State_Name,"</b>",
                "<br/>",
                "Risk score = ", round(mydf$CovRisk,3),
                "<br/>",
                "COVID confirmed cases per 100k :", round((mydf$Covid19Positive/mydf$Pop)*100000),
                "<br/>",
                "Percent in poor or fair health (BRFSS) = ", mydf$data_value, "%",
                "<br/>",
                "Percent daily change = " , round(mydf$confirm_change, 2) , "%")

m <- leaflet(mydf)%>%
  setView(-96, 37.8, 5) %>%
  addProviderTiles("MapBox", options = providerTileOptions(
    id = "mapbox.light",
    accessToken = Sys.getenv('MAPBOX_ACCESS_TOKEN')))


pal <- colorNumeric(palette = "RdYlBu", domain = c(0:2), reverse =TRUE)


mm<- m %>% addPolygons(
  fillColor = pal(mydf$CovRisk),
  weight = 2,
  opacity = 1,
  color = "black",
  dashArray = "1",
  fillOpacity = 0.3,
  label = mydf$State_Name,
  popup  = labels,
  highlight = highlightOptions(
    weight = 2,
    color = "#666",
    dashArray = "",
    fillOpacity = 0.6,
    bringToFront = TRUE))%>%
  addResetMapButton() %>%
  addLegend(title = "COVID Risk score", 
                                position = "bottomleft",
                                pal=pal,
                                values = c(0:2))
mm

library(htmlwidgets)

saveWidget(mm, file = "/Users/andywilson1/Documents/GitHub/covid19perspective/Sandbox/ARW/myMap.html")



write.csv(brfss_trim, "/Users/andywilson1/Documents/GitHub/covid19perspective/RawData/BRFSS data descriptions/brfss Fair or Poor Health by state.csv")




write.csv(Updated, "/Users/andywilson1/Documents/GitHub/covid19perspective/RawData/BRFSS data descriptions/Updated.csv")
