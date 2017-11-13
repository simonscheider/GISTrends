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
#import arcpy
import json
import re
import urllib3
import rdflib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
##from matplotlib import rcParams
##rcParams['xtick.direction'] = 'out'
##rcParams['ytick.direction'] = 'out'
import operator

from altair import *
from IPython.display import display
import pandas

import requests
from bs4 import BeautifulSoup

class GatherTools():
    def __init__(self, referencekeyword, unsaferun=False):
         self.results = {}
         self.kw = referencekeyword
         self.currenttools= [referencekeyword]
         self.toolboxes =['']
         self.unsaferun =unsaferun


    def reset(self):
        self.currenttools= [self.kw]
        self.toolboxes =['']

    def add(self,tool, toolbox=''):
        self.currenttools.append(tool)
        self.toolboxes.append(toolbox)
        if len(self.currenttools)>=5:
            res = self.queryGTrends(self.currenttools)
            self.store(res)
            self.reset()



    def store(self,res):
        for id,t in enumerate(self.currenttools):
            if not t == self.kw:
                #make sure trends are within plausible limits
                B = res[t] < res[self.kw] and res[t] >0
                if self.unsaferun == True: B = True
                if B:
                    if self.toolboxes[id] not in self.results.keys():
                        self.results[self.toolboxes[id]]={t:str(res[t])}
                    else:
                        self.results[self.toolboxes[id]][t]=str(res[t])


    def dump(self,res = 'GTresults.json'):
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


def getGISSoftwareList():
    #results = rdflib.Graph()
    results = {}
    #from rdflib import Namespace
    #dbo = Namespace("http://dbpedia.org/ontology/")
    WIKI_URL = "https://en.wikipedia.org/wiki/Comparison_of_geographic_information_systems_software"
    req = requests.get(WIKI_URL)
    soup = BeautifulSoup(req.content, 'lxml')
    table_classes = {"class": ["sortable", "plainrowheaders"]}
    wikitables = soup.findAll("table", table_classes)
    for table in wikitables:
        for row in table.findAll("tr"):
            cells = row.findAll(["th", "td"])
            for url in cells[0].findAll('a', href=True):
                name = url.getText()
                dom = url.get('href').split("/")[-1]
                dbp= urllib.basejoin('http://dbpedia.org/resource/',dom)
                wkp= urllib.basejoin('https://en.wikipedia.org/wiki/',dom)
                r = getDBpediaCompany(dbp)
                comp = []
                for f in r['results']['bindings']:
                    comp.append(f['f']['value'])
                results[dbp]={'website': wkp, 'name':name, 'companies':comp}

    outf = 'GISSoftdict.json'

    with open(outf, 'w') as fp:
        json.dump(results, fp)
    fp.close
    return outf
                #c= getDBpediaCompany(dbp)
                #print c
                #results.add((dbp,dbo.developer, c))
    #print results.serialize(format='turtle')






def getDBpediaCompany(url):
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    query = """
    Select ?f WHERE {
    <"""+url+ """> <http://dbpedia.org/ontology/developer> ?f
    }
            """
    sparql.setQuery(query)  # the previous query as a literal string

    return sparql.query().convert()







def buildArcToolList():
    print ('Number of Tools '+str(len(arcpy.ListTools())))
    toolboxes = arcpy.ListToolboxes()
    out = {}
    outf = 'ArcGIStooldict.json'
    for toolbox in toolboxes:
        print toolbox
        out[toolbox]=[]
        tools = arcpy.ListTools('*_'+toolbox[toolbox.index('(')+1:toolbox.index(')')])
        for tool in tools:
            #print tool
            out[toolbox].append(tool)
    with open(outf, 'w') as fp:
        json.dump(out, fp)
    fp.close
    return outf

def readToolBoxes(tooldictfile, listoftoolboxes):
    tdict = {}
    with open(tooldictfile) as tooldictf:
        tooldict = json.load(tooldictf)
        for t in listoftoolboxes:
           tdict[t]=tooldict[t]
    tooldictf.close
    return tdict

def getTrends4Tools(tooldict,referencekeyword):
    gt = GatherTools(referencekeyword)
    for k,v in tooldict.items():
        for tool in v:
            ntool = normalizeArcpyToolString(tool)
            gt.add(ntool,k)
    gt.dump('GTresults_kw'+referencekeyword+'.json')


def readSoft(softdictfile):
    with open(softdictfile) as softdictf:
        softdict = json.load(softdictf)
    softdictf.close
    return softdict

def getTrends4Soft(softdict,referencekeyword):
    gt = GatherTools(referencekeyword, True)
    count = 0
    for k,v in softdict.items():
        count+=1
        gt.add(v['name'])
    print 'count '+str(count)
    gt.dump('Softresults_kw'+referencekeyword+'.json')


def visualize(resultdump):
    result = []
    with open(resultdump) as res:
        ress = json.load(res)
    for k,v in ress.items():
        for kk,vv in v.items():
            result.append({'ArcGIS Tools':kk, 'Box':k,'GT Popularity':float(vv)})
    #print result
    #toolbox= 'Spatial Analyst Tools(sa)'
    #toolbox='Conversion Tools(conversion)'
##    c = Chart(Data(
##    values=result,
##    ),
##    description='A simple bar chart with embedded data.',
##    ).mark_bar().encode(
##    x=X(toolbox, sort=SortField(field='GT Popularity', op='values', order='descending')),
##    y=Y('GT Popularity')
    #x=toolbox+':O',
    #y='GT Popularity:Q'
    #)
    #c.savechart('plot.html')
    df = pandas.DataFrame.from_dict(result)
    df =df.sort_values(by='GT Popularity', ascending=[False]).set_index('ArcGIS Tools')
    print df
    colors = {'Spatial Analyst Tools(sa)': 'c', 'Conversion Tools(conversion)': 'b'}

    pl = df['GT Popularity'].plot(kind='bar', width=1, fontsize=9, color=[colors[i] for i in df['Box']], figsize=(12,5.8))
    red_patch = mpatches.Patch(color='cyan', label='Spatial Analyst')
    blue_patch= mpatches.Patch(color='blue', label='Conversion Tools')
    lines = [blue_patch, red_patch]
    labels = [line.get_label() for line in lines]
    pl.legend(lines, labels)


    #pl.set_xlabel("Tools", fontsize=9)
    plt.tight_layout()
    plt.show()






def normalizeArcpyToolString(tool):
        #ex = 'CreateSchematicFolder_schematics'
        #Get the actual toolname (without toolbox and splitting at upper case letters)
        return ' '.join(re.findall('[A-Z][^A-Z]*', tool.partition('_')[0]))






def main():

    #outf = buildArcToolList()
    #toolboxlist =['3D Analyst Tools(3d)','Analysis Tools(analysis)','Cartography Tools(cartography)','Conversion Tools(conversion)','Coverage_Tools(arc)', 'Data Interoperability Tools(interop)', 'Data Management Tools(management)', 'Editing Tools(edit)', 'Geocoding Tools(geocoding)', 'Geostatistical Analyst Tools(ga)', 'Linear Referencing Tools(lr)', 'Multidimension Tools(md)', 'Network Analyst Tools(na)', 'Parcel Fabric Tools(fabric)','Samples(samples)', 'Schematics Tools(schematics)','Server Tools(server)','Spatial Analyst Tools(sa)','Spatial Statistics Tools(stats)','Tracking Analyst Tools(ta)','Space Time Pattern Mining Tools(stpm)']

    #td = readToolBoxes('ArcGISTooldict.json', ['Spatial Analyst Tools(sa)','Conversion Tools(conversion)','Analysis Tools(analysis)'])
    #res = getTrends4Tools(td,'ArcGIS')
    #visualize('GTresults_kwArcGIS.json')
    #kw_list=['ArcGIS', 'GRASS GIS', 'QGIS', 'R studio', 'Interpolation']#'MapInfo']'ILWIS'
    #kw_list = ['ArcMap','Extract by Mask', 'Set Null', 'IDW', 'Raster calculator']#['zonal', 'areal interpolation', 'raster calculator', 'ArcGIS' ]

    #getGISSoftwareList()
    sd = readSoft('GISSoftdict.json')
    getTrends4Soft(sd, 'ArcGIS')
##    with open('spatialanalysttools.csv', 'rb') as csvfile:
##        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
##        i =0
##        for row in spamreader:
##            #print row[0]
##            #kw_list.append(row[1])
##            i+=1
##            if i ==4: break






if __name__ == '__main__':
    main()
