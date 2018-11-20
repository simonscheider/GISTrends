#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Schei008
#
# Created:     20-11-2018
# Copyright:   (c) Schei008 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pytrends
import pandas

from pytrends.request import TrendReq

import csv

import json
import re

"""This class is used to gather Googe Trends for an arbitrary list of keywords (about tools). It is inititalized with a reference keyword to compare relative popularity against"""
class GatherInterest():
    def __init__(self, referencekeyword, unsaferun=False):
         self.results = {}
         self.kw = referencekeyword
         self.currentkw= [referencekeyword]
         self.unsaferun =unsaferun


    def reset(self):
        self.currentkw= [self.kw]

    def add(self,kw):
        self.currentkw.append(kw)
        if len(self.currentkw)>=5:
            res = self.queryGTrends(self.currentkw)
            self.store(res)
            self.reset()

    def store(self,res):
        for id,t in enumerate(self.currentkw):
            if not t == self.kw:
                #make sure trends are within plausible limits
                B = res[t] < res[self.kw] and res[t] >0
                if self.unsaferun: B = True
                if B:  self.results[t]=str(res[t])


    def dump(self,res = 'data\\targetqueries\\GTresults.json'):
        print "dumped items: "+str(len(self.results))
        with open(res, 'w') as fp:
            json.dump(self.results, fp)
        fp.close

    def queryGTrends(self,kw_list):
        google_username = "simonscheider@web.de"
        google_password = "5z4cxCbN"
        pytrends = TrendReq(hl='en-US')

        pytrends.build_payload(kw_list, timeframe='all')
        #pytrends.build_payload(kw_list)

        # Interest over time
        time = pytrends.interest_over_time()
        #time.mean()
        #print(time.mean())


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
        return time.mean()

"""Trends for tools"""
def getTrends4Regions(regioncsv,referencekeyword):
    gt = GatherInterest(referencekeyword)
    count = 0
    pd = pandas.read_csv(regioncsv)
    pd = pd[pd['QUERY_BASETERM'] == False]
    print "ready to query over "+str(pd.size) + ' regions!'
    print pd
    for index, row in pd.iterrows():
        count+=1
        print row['safe_keyword']
        #gt.add()
    print 'Regions queried '+str(count)
    gt.dump('data\\targetqueries\\GT'+referencekeyword+'.json')

def main():
    getTrends4Regions('geodata\\GMsearchterms.csv','Amsterdam')

if __name__ == '__main__':
    main()
