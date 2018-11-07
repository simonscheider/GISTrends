# Andrea Ballatore
# 2018

library(pacman)

#devtools::install_github("PMassicotte/gtrendsR") # not working
#devtools::install_github('diplodata/gtrendsR') # fix that also doesn't work
pacman::p_load(readr,rvest,urltools,uuid,RSQLite,rjson,rgdal,curl,gtrendsR,dplyr)

CUR_DATE = substr(as.character(Sys.time()),0,10)

# Utils ---------------------------------

parse_gt_hits <- function( hits ){
  hits = replace(hits, hits=='<1', .5)
  return(as.numeric(hits))
}

# Datasets ---------------------------------

save_results <- function( df, filename ){
  fdir = paste0('tmp/amsterdam_gtrends_',CUR_DATE,'/')
  dir.create(fdir, showWarnings = FALSE)
  fn = paste0(fdir,filename,'.tsv')
  fnbin = paste0(fdir,filename,'.rds')
  saveRDS( df, file = fnbin, compress=T )
  print(paste('save_results',fn))
  write_tsv( df, fn, append = F, na = '')
}

# create outfolders
dir.create('tmp',showWarnings = F)
#dir.create('tmp/pages',showWarnings = F)

# Load Amsterdam data ---------------------------------
muni_sdf = readRDS( file = 'geodata/netherlands_municipalities_sdf.rds' )
quar_sdf = readRDS( file = 'geodata/netherlands_quarters_sdf.rds' )
neig_sdf = readRDS( file = 'geodata/netherlands_neighbourhoods_sdf.rds' )

# gtrends data
GT_DATA_FOLDER = 'data/amsterdam_gtrends/amsterdam_gtrends_2018-11-03/'

gt_time_df = readRDS( file = file.path(GT_DATA_FOLDER,'interest_over_time_df.rds') )
nrow(gt_time_df)
summary(gt_time_df)
gt_time_df$hits = parse_gt_hits(gt_time_df$hits)
gt_time_df$keyword = as.factor(gt_time_df$keyword)
gt_time_df$GEOUNIT_CODE = as.factor(gt_time_df$GEOUNIT_CODE)
gt_time_df$GEOUNIT_TYPE = as.factor(gt_time_df$GEOUNIT_TYPE)
summary(gt_time_df)

# Analyse Amsterdam data ---------------------------------
names(gt_time_df)
#
gt_time_df_summary = gt_time_df %>%
  group_by(GEOUNIT_CODE, QUERY_BASETERM, keyword, GEOUNIT_TYPE) %>%
  summarise(
    n = n(),
    hits_min = min(hits, na.rm = T),
    hits_mean = mean(hits, na.rm = T),
    hits_median = median(hits, na.rm = T),
    hits_max = max(hits, na.rm = T)
  )
gt_time_df_summary$hits_mean = round(gt_time_df_summary$hits_mean,1)
View(gt_time_df_summary)

write_tsv( gt_time_df_summary, 'tmp/gt_time_summary.tsv', append = F, na = '')

print("OK")
