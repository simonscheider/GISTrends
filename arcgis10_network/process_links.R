
library(readxl)
require(xlsx)
links <- unique(read_excel("arcgis_tool_links.xlsx"))

print(nrow(links))

links_2nd = merge( x = links, y = links, by.x = 'to', by.y = 'from' )
write.xlsx(links_2nd, 'arcgis_tool_links_2nd.xlsx', row.names = F)

#names(links_2nd) = c('from','to1','to2')

links_2nd = unique(links_2nd[ -1 ])
print(nrow(links_2nd))
links_2nd = subset(links_2nd, links_2nd$from != links_2nd$to)
print(nrow(links_2nd))

links$order = 1
links_2nd$order = 2

print(nrow(links))
print(nrow(links_2nd))

print(head(links_2nd))

df = rbind(links, links_2nd)

df$order = as.factor(df$order)

print(nrow(df))

print(summary(df))


write.xlsx(df, 'arcgis_tool_links_orders.xlsx', row.names = F)
write.csv(df, 'arcgis_tool_links_orders.csv', row.names = F, quote = F)

print('OK')