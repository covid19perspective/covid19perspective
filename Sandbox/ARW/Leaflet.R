library(leaflet)
library(tidyverse)
library(leaflet.extras)

mydata<-read.csv("/Users/andywilson1/Documents/GitHub/covid19perspective/Sandbox/MWK/Combined.csv")
states <- geojsonio::geojson_read("/Users/andywilson1/Desktop/Leaflet/gz_2010_us_040_00_500k.json", what = "sp")
mydata$NAME<-mydata$State_Name

mydf <- sp::merge(states, mydata, by="NAME", all=F)

mydf$CovProp100k <- round((mydf$Covid19Positive/mydf$Pop)*100000)

head(mydf$State_Name)

labels <- paste("<b>", mydf$State_Name,"</b>",
                "<br/>",
                "3/xx/2020 Count per 100,000 = ", mydf$CovProp100k,
                "<br/>",
                "Percent change from prior day = ", "will calculate", "%")

m <- leaflet(mydf)%>%
  setView(-96, 37.8, 5) %>%
  addProviderTiles("MapBox", options = providerTileOptions(
    id = "mapbox.light",
    accessToken = Sys.getenv('MAPBOX_ACCESS_TOKEN')))


pal <- colorNumeric(palette = "Reds", domain = mydf$CovProp100k)


mm<- m %>% addPolygons(
  fillColor = pal(mydf$CovProp100k),
  weight = 2,
  opacity = 1,
  color = "black",
  dashArray = "1",
  fillOpacity = 0.7,
  label = mydf$State_Name,
  popup  = labels,
  highlight = highlightOptions(
    weight = 2,
    color = "#666",
    dashArray = "",
    fillOpacity = 0.7,
    bringToFront = TRUE))%>%
  addSearchOSM() %>%
  addResetMapButton() %>%
  addLegend(title = "COVID cases per 100,000 pop", 
                                position = "bottomleft",
                                pal=pal,
                                values = c(0:max(mydf$CovProp100k)))


library(htmlwidgets)

saveWidget(mm, file = "/Users/andywilson1/Documents/GitHub/covid19perspective/Sandbox/ARW/myMap.html")


