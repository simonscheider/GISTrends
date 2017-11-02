#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      simon
#
# Created:     26/10/2017
# Copyright:   (c) simon 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pytrends

from pytrends.request import TrendReq

import csv


def main():

    google_username = "smionscheider@web.de"
    google_password = "5z4cxCbN"
    pytrends = TrendReq(hl='en-US')

    kw_list = []#['zonal', 'areal interpolation', 'raster calculator', 'ArcGIS' ]

    with open('spatialanalysttools.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        i =0
        for row in spamreader:
            print row[0]
            kw_list.append('GIS '+row[0])
            i+=1
            if i ==5: break


    #kw_list = ['zonal', 'areal interpolation', 'raster calculator', 'ArcGIS' ]

    pytrends.build_payload(kw_list, timeframe='all')
    #pytrends.build_payload(kw_list)

    # Interest over time
    time = pytrends.interest_over_time()
    #time.mean()
    print(time.mean())

    # Related Queries, returns a dictionary of dataframes
    #related_queries_dict = pytrends.related_queries()
    #print(related_queries_dict)

    #related_topics_dict = pytrends.related_topics()
    #print(related_topics_dict)

    # Get Google Hot Trends data
   # trending_searches_df = pytrends.trending_searches()
   # print(trending_searches_df.head())


    # Get Google Keyword Suggestions
    #suggestions_dict = pytrends.suggestions(keyword='GIS')
   # print(suggestions_dict)

if __name__ == '__main__':
    main()
