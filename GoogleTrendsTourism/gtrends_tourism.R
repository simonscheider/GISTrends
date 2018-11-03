# Andrea Ballatore
# 2018
rm(list = ls())

library(pacman)

#devtools::install_github("PMassicotte/gtrendsR") # not working
#devtools::install_github('diplodata/gtrendsR') # fix that also doesn't work
pacman::p_load(readr,rvest,urltools,uuid,RSQLite,rjson,rgdal,curl,gtrendsR)

RANDOM_PAUSE_MIN_S = 1
RANDOM_PAUSE_MAX_S = 5
CUR_DATE = substr(as.character(Sys.time()),0,10)

# Utils ---------------------------------

load_res_table <- function( fn, quot="" ){
  df <- read.table(file=fn, header=TRUE, sep="\t", stringsAsFactors=T, #fileEncoding="UTF-8",
                   fill = TRUE, quote = quot, comment.char = "", na.strings = "<NA>" )
  print(paste("Loaded",fn,"> rows=",nrow(df)))
  return(df)
}

sort_df <- function( df, col, asc=T ){
  sdf = df[ with(df, order(df[,c(col)], decreasing = !asc)), ]
  return(sdf)
}

save_obj_bin <- function( obj, obj_name ){
  #print(paste("save_obj_bin",get_bin_file_name(obj_name)))
  saveRDS( obj, file = get_bin_file_name(obj_name), compress=T )
  print(paste("save_obj_bin:",obj_name))
}

load_obj_bin <- function( obj_name ){
  print(paste("load_obj_bin:",obj_name))
  return( readRDS( get_bin_file_name(obj_name) ) )
}

get_bin_file_name <- function( obj_name ){
  print("get_bin_file_name")
  fn = file.path(BIN_DIR_, paste( obj_name, ".rds", sep=""))
  print(fn)
  return(fn)
}

random_pause <- function( min_seconds, max_seconds ){
  stopifnot(min_seconds <= max_seconds)
  secs = runif(1, min_seconds, max_seconds)
  print(paste("random_pause seconds =",round(secs,1)))
  Sys.sleep(secs)
}

write_text_file <- function( contents, fn ){
  print(paste("write_text_file",nchar(contents)))
  #sink(fn)
  write(contents,file = fn)
  #sink()
}

# Datasets ---------------------------------

# load datasets here


# Scraper ---------------------------------
get_url = function( url ){
  library(httr)
  r = GET(url)
  status = status_code(r)
  if (status == 200) return( content(r,encoding = 'utf8') )
  return(r)
}

# get URL from random VPN node. Linked to AB's PIA account.
get_url_piavpn = function( url ){
  library(RCurl)
  #print(paste('get_url_piavpn',url))
  pia_socks5 = 'socks5h://x1936726:RYWxEUiy6N@proxy-nl.privateinternetaccess.com:1080'
  #pia_socks5 = 'socks5://x1936726:RYWxEUiy6N@proxy-nl.privateinternetaccess.com:1080'
  options(RCurlOptions = list(proxy = pia_socks5,
                              #useragent = "Mozilla",
                              followlocation = TRUE,
                              verbose = F,
                              referer = "",
                              cookiejar = "tmp/_piavpn.cookies.txt"
  ))
  html <- RCurl::getURL(url=url, curl=RCurl::getCurlHandle())
  return(html)
}

# Google Search utils ---------------------------------
load_google_domains <- function(){
  google_domains = scan('data/google/google_supported_domains.txt',sep = '\n',what = "character")
  stopifnot(length(google_domains)==193)
  google_domains = data.frame(DOMAIN = google_domains)
  google_domains$DOMAIN = as.character(google_domains$DOMAIN)
  google_domains$TOPDOMAIN = substr( google_domains$DOMAIN, nchar(google_domains$DOMAIN)-2, nchar(google_domains$DOMAIN) )
  google_domains$TOPDOMAIN = gsub('\\.','',google_domains$TOPDOMAIN)
  return(google_domains)
}
#google_domains = load_google_domains()

#google_languages = scan('data/google/google_supported_languages.txt',sep = '\n',what = "character")
#stopifnot(length(google_languages)==45)

#google_country_langs = read.table('data/google/google_country_langs.txt', header = F, sep = '\t', na.strings = '')
#names(google_country_langs) = c('COUNTRY','LANGS')
#google_country_langs$LANGS = as.character(google_country_langs$LANGS)

get_google_languages_for_country <- function(country_code){
  stopifnot(nchar(country_code)==2)
  print(paste('get_google_languages_for_country',country_code))
  langs = strsplit( subset(google_country_langs, google_country_langs$COUNTRY==country_code)$LANGS, ',')[[1]]
  return(langs)
}

get_google_baseurl_country <- function( country_code ){
  stopifnot(nchar(country_code)==2)

  # handle exceptions
  res = ''
  if (country_code == "US") res = "http://www.google.com"
  if (country_code == "GB") res = "http://www.google.co.uk"
  if (country_code == "UK") res = "http://www.google.co.uk"
  if(nchar(res)>0) return(res)

  res = subset(google_domains, toupper(google_domains$TOPDOMAIN) == country_code)$DOMAIN
  #print(res)
  stopifnot(length(res)==1)

  res = paste0("http://www",res)
  return(res)
}

parse_google_serp = function( df, html ){
  # Based on https://github.com/hadley/rvest
  require(rvest)
  stopifnot(nrow(df)==1)
  serp_page = read_html(html)

  # get basic Google SERP
  serp_urls = serp_page %>%
    html_nodes(xpath = "//div[@id='search']//h3/a") %>%
    html_attr("href")
  serp_titles = serp_page %>%
    html_nodes(xpath = "//div[@id='search']//h3/a") %>%
    html_text()
  if (length(serp_urls)==0) print(">>> Possible crawler detection <<<")
  else print("> SERP found <")
  stopifnot(length(serp_urls)>0)
  stopifnot(length(serp_titles)>0)

  serpdf = data.frame( FULL_RESULT=serp_urls, SEARCH_UID=df$SEARCH_UID )
  serpdf$TITLE = serp_titles
  serpdf = build_serp_df(serpdf)
  serpdf$ORGANIC = NULL
  serpdf$RES_TYPE = 'core'
  serpdf$DESC = NA
  stopifnot(nrow(serpdf)>0)

  cols = c("SEARCH_UID","RES_TYPE","RANK","RESULT_URL","TITLE","DESC","FULL_RESULT")
  allserpdf = serpdf[,cols]

  # NEWS
  serp_urls = serp_page %>%
    html_nodes(xpath = "//div[@id='search']//td[@valign='top']/div/a") %>%
    html_attr("href")

  if (length(serp_urls)>0){
    serp_titles = serp_page %>%
      html_nodes(xpath = "//div[@id='search']//td[@valign='top']/div/a") %>%
      html_text()
    #print(paste("news serp_urls",length(serp_urls)))
    #print(paste("news serp_urls",length(serp_urls)))

    serpnewsdf = data.frame(FULL_RESULT=serp_urls, TITLE=serp_titles, SEARCH_UID=df$SEARCH_UID)
    serpnewsdf = build_serp_df(serpnewsdf)
    serpnewsdf$ORGANIC = NULL
    serpnewsdf$RES_TYPE = 'news'
    serpnewsdf$DESC = NA

    allserpdf = rbind(allserpdf, serpnewsdf[,cols])
  }

  # IMAGES
  image_query = "//div[@id='search']//img[@align]"
  titles = serp_page %>% html_nodes(xpath = image_query) %>% html_attr('title')
  urls = serp_page %>% html_nodes(xpath = image_query) %>% html_attr('src')
  alts = serp_page %>% html_nodes(xpath = image_query) %>% html_attr('alt')
  images_found = F
  if (length(titles)>0){
    imgdf = data.frame(TITLE = titles, RESULT_URL = urls, FULL_RESULT = urls, DESC = alts, SEARCH_UID=df$SEARCH_UID )
    imgdf$RANK = seq(nrow(imgdf))
    imgdf$RES_TYPE = 'images'
    images_found = T

    allserpdf = rbind(allserpdf, imgdf[,cols])
  }
  rm(titles,urls,alts)

  # RELATED SEARCHES
  relsearch_query = "//td//p[@class='aw5cc']"
  queries = serp_page %>% html_nodes(xpath = relsearch_query) %>% html_text()
  urls = serp_page %>% html_nodes(xpath = "//td//p[@class='aw5cc']//a") %>% html_attr('href')
  if (length(urls)>0){
    # related researches found
    reldf = data.frame(TITLE = queries, RESULT_URL = NA, FULL_RESULT = urls, DESC = NA, SEARCH_UID=df$SEARCH_UID )
    reldf$RANK = seq(nrow(reldf))
    reldf$RES_TYPE = 'related_search'
    baseurl = get_google_baseurl_country( as.character(unique(df$QUERY_BASECOUNTRY)) )
    reldf$RESULT_URL = paste0( baseurl, sapply( reldf$FULL_RESULT, clean_google_url ) )
    #View(reldf)
    allserpdf = rbind(allserpdf, reldf[,cols])
  }
  rm(queries)
  rm(urls)

  # ADS
  #ad_query = "//div[@id='tads']//li"
  #ads = serp_page %>% html_nodes(xpath = ad_query) %>% html_text()

  #serpimgdf = build_serp_df(serp_urls)

  # SEMANTIC LINKS
  sem_query_poi = "//div[@class='dXAUyb']//a" # POINTS of INTERESTS
  #sem_query2 = "//a[@class='FEM55']//img"
  urls = serp_page %>% html_nodes(xpath = sem_query_poi) %>% html_attr('href')
  if (length(urls)>0){
    stopifnot(!is.na(urls))
    alts = serp_page %>% html_nodes(xpath = sem_query_poi) %>% html_text()
    #alts = serp_page %>% html_nodes(xpath = sem_query2) %>% html_attr('title')
    semdf = data.frame(TITLE = trimws(alts), RESULT_URL = NA, FULL_RESULT = urls, DESC = NA )
    semdf = subset(semdf, semdf$TITLE!='')
    semdf$SEARCH_UID=unique(df$SEARCH_UID)
    semdf$RANK = seq(nrow(semdf))
    semdf$RES_TYPE = 'semantic_link'
    baseurl = get_google_baseurl_country( as.character(unique(df$QUERY_BASECOUNTRY)) )
    semdf$RESULT_URL = paste0( baseurl, sapply( semdf$FULL_RESULT, clean_google_url ) )
    #View(semdf)

    # SEMANTIC DESCRIPTIONS
    sem_query = "//div[@class='V7Q8V']"
    sem_desc = serp_page %>% html_nodes(xpath = sem_query) %>% html_text(trim = T)
    sem_desc = gsub('\t','  ',sem_desc)
    sem_desc = gsub('\n','  ',sem_desc)
    semdescdf = data.frame(TITLE = NA, RESULT_URL = NA, FULL_RESULT = NA, DESC = sem_desc )
    semdescdf = subset(semdescdf, semdescdf$DESC!='')
    stopifnot(nrow(semdescdf)>0)
    semdescdf$SEARCH_UID=unique(df$SEARCH_UID)
    semdescdf$RANK = seq(nrow(semdescdf))
    semdescdf$RES_TYPE = 'semantic_desc'
    #View(semdescdf)
    stopifnot(nrow(semdescdf)>0)
    allserpdf = rbind(allserpdf, semdf[,cols])
    allserpdf = rbind(allserpdf, semdescdf[,cols])
  }
  return(allserpdf)
}

# Google Trends ---------------------------------

# Based on https://cran.r-project.org/web/packages/gtrendsR/gtrendsR.pdf

# load Google Trends categories
data("categories") 
nrow(categories)
summary(categories)

get_gtrends_results <- function( base_term, terms ){
  print(paste("get_gtrends_results", base_term, terms))
  all_terms = c( base_term, terms )
  #print(all_terms)
  trial_i = 0
  found = F
  while(!found){
    tryCatch( {
      # call Google Trends API through gtrendsr
      # set proxy
      #   pia_socks5 = 'socks5h://x1936726:RYWxEUiy6N@proxy-nl.privateinternetaccess.com:1080'
      #setHandleParameters(user = 'x1936726', password = 'RYWxEUiy6N', domain = NULL,
      #                    proxyhost = 'proxy-nl.privateinternetaccess.com', proxyport = 1080 ) #, proxyauth = 15
      #pia_socks5 = 'socks5h://x1936726:RYWxEUiy6N@proxy-nl.privateinternetaccess.com:1080'
      #pia_socks5 = 'socks5://x1936726:RYWxEUiy6N@proxy-nl.privateinternetaccess.com:1080'
      #options(RCurlOptions = list(proxy = pia_socks5,
                                  #useragent = "Mozilla",
      #                            followlocation = TRUE,
       #                           verbose = F,
        #                          referer = "",
         #                         cookiejar = "tmp/_piavpn.cookies.txt"
      #))
      res = gtrends(all_terms)
      found = T
      print('> Gtrends data found <')
    },
    error = function(e) {
      trial_i=trial_i+1
      print(e)
      traceback(e)
      #stop("Problem detected") # DEBUG
      #found=T # debug
      print(paste("Problem detected. Trying again, i =", trial_i));
      found = F
      random_pause(RANDOM_PAUSE_MIN_S,RANDOM_PAUSE_MAX_S)
    },
    finally = {})
  }
  random_pause(RANDOM_PAUSE_MIN_S,RANDOM_PAUSE_MAX_S)
  return(res)
}

tag_results <- function(df, query_str, query_uid, geounit_code, geounit_name, geo_type ){
  df$GTREND_QUERY = query_str
  df$GEOUNIT_TYPE = geo_type
  df$GEOUNIT_CODE = geounit_code
  df$QUERY_UID = query_uid
  df$QUERY_BASETERM = df$keyword != geounit_name
  return(df)
}

save_results <- function( df, filename ){
  fdir = paste0('tmp/amsterdam_gtrends_',CUR_DATE,'/')
  dir.create(fdir, showWarnings = FALSE)
  fn = paste0(fdir,filename,'.tsv')
  fnbin = paste0(fdir,filename,'.rds')
  saveRDS( df, file = fnbin, compress=T )
  print(paste('save_results',fn))
  write_tsv( df, fn, append = F, na = '')
}

# Main ---------------------------------
#get_url_piavpn('https://github.com/curl/curl/issues/944')

# create outfolders
dir.create('tmp',showWarnings = F)
#dir.create('tmp/pages',showWarnings = F)

# Run GTrends queries

#res = get_gtrends_results('Amsterdam', c('Leiden','Rotterdam'))

#res$interest_by_city
#res$related_queries

# Get Amsterdam data ---------------------------------

get_gtrends_amsterdam <- function( base_term, shpdf, geo_type ){
  print(paste('>> get_gtrends_amsterdam N=',nrow(shpdf),'geo_type=',geo_type))
  shpdf$NAME = as.character(shpdf$NAME)
  for( i in seq(nrow(shpdf)) ) {
    print(paste('i =',i))
    code = as.character(shpdf@data[i,c("CODE")])
    name = as.character(shpdf@data[i,c("NAME")])
    uid = UUIDgenerate()
    print(paste("get_gtrends_amsterdam",uid,code,name))
    query_str = paste(base_term, name, sep = ';')
    #stopifnot(nchar(name)>2)
    gres = get_gtrends_results(base_term, name)
    
    # "interest_over_time"  "interest_by_country" "interest_by_region"  
    # "interest_by_dma"     "interest_by_city"    "related_topics"     
    # "related_queries"
    # --- interest_over_time ---
    df = gres$interest_over_time
    df = tag_results(df, query_str, uid, code, name, geo_type)
    interest_over_time_df <<- rbind( interest_over_time_df, df )
    #View(interest_over_time_df)
    
    # --- interest_by_country ---
    df = gres$interest_by_country
    df = tag_results(df, query_str, uid, code, name, geo_type)
    interest_by_country_df <<- rbind( interest_by_country_df, df )
    #View(interest_by_country_df)
    
    # --- interest_by_country ---
    df = gres$interest_by_city
    df = tag_results(df, query_str, uid, code, name, geo_type)
    interest_by_city_df <<- rbind( interest_by_city_df, df )
    #View(interest_by_city_df)
    
    rm(df)
  }
}

# municipalities (gm)
# wijken (wk) (="quarters")
# buurten (bu) (="neighborhoods') (highest resolution level)
muni = readOGR(dsn="geodata/MetropolregionA.shp")
cols = c("CODE","NAME")
names(muni)[1:2]=cols
qua = readOGR(dsn="geodata/MetrAWijk.shp")
names(qua)[1:2]=cols
nei = readOGR(dsn="geodata/MetrABuurt.shp")
names(nei)[1:2]=cols

# init data
interest_over_time_df = data.frame()
interest_by_country_df = data.frame()
interest_by_city_df = data.frame()

base_term = "Amsterdam"
get_gtrends_amsterdam(base_term, muni, 'municipality')
get_gtrends_amsterdam(base_term, qua, 'quarter')
#get_gtrends_amsterdam(base_term, nei, 'neighbourhood')

# save datasets
save_results(interest_over_time_df,'interest_over_time_df')
save_results(interest_by_country_df,'interest_by_country_df')
save_results(interest_by_city_df,'interest_by_city_df')

print("OK")
