

parse_time <- function(comdf){
  require(parsedate)
  print('parse_time')
  # eg: 27/02/2016 20:56
  comdf$TIMESTAMPD = parse_date(comdf$Month)
  comdf$TIMESTAMP_YM = as.factor( format(comdf$TIMESTAMPD, "%Y-%m") )
  comdf$TIMESTAMP_YEAR = as.numeric( format(comdf$TIMESTAMPD, "%Y") )
  #comdf$TIMESTAMP_WEEKDAY = as.factor(weekdays(comdf$TIMESTAMPD))
  comdf$TIMESTAMP_MONTH = as.factor(paste(months(comdf$TIMESTAMPD)))
  #comdf$TIMESTAMP_DATE = as.factor(as.Date(comdf$TIMESTAMPD))
  #comdf$TIMESTAMP_H = as.factor( format(comdf$TIMESTAMPD, "%H") )
  comdf$TIMESTAMP_QUARTER = as.factor(quarters(comdf$TIMESTAMPD))
  #comdf$TIMESTAMP_DAYNIGHT = as.factor(sapply( comdf$TIMESTAMPD, get_daily_category ))
  #comdf$TIMESTAMP_CAT3 = as.factor(sapply( comdf$TIMESTAMPD, get_time_category ))
  print( comdf[sample(nrow(comdf), 10),] )
  return(comdf)
}


library(readxl)
require(xlsx)
library("reshape2")

df <- unique(read_excel("data/google_trends/trendtimeline_tools.xlsx"))
df <- melt(df, id="Month",measure.vars = c("ArcGIS","MapInfo","QGIS","PostGIS")) 

df = parse_time(df)

print(nrow(df))
print(summary(df))

library(ggplot2)

p = ggplot(data=df, aes(x=TIMESTAMPD, y=value, group=variable, color=variable)) + theme_bw() + 
  scale_x_datetime(name = "Year", date_breaks = "1 year", date_labels = "%Y") +
  stat_smooth(inherit.aes = TRUE) + geom_line(alpha=0.4) + #+  +
  ylab("Google Trends index") 

ggsave("data/google_trends/gtrends_tools_time.pdf", p, width = 7, height = 5)

print('OK')