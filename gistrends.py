#-------------------------------------------------------------------------------
# Name:        Generate GIS Software and tool catalogue, and Google Trend analysis
# Purpose:     This script can be used to generate and publish an RDF based catalogue of GIS software, tools and websites together wit their hyperlinks.
#              Furthermore, it contains methods to query Google Trends for keywords based on this catalogue.
#
# Author:      Simon Scheider
#
# Created:     25/11/2017
# Copyright:   (c) simon 2017
# Licence:
#-------------------------------------------------------------------------------

import pytrends

from pytrends.request import TrendReq

import csv

import json
import re
import urllib
import rdflib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import math



from altair import *
from IPython.display import display
import pandas

from SPARQLWrapper import SPARQLWrapper, JSON

import requests
from bs4 import BeautifulSoup


######## Methods to gather Google trend data and visualize it

"""This class is used to gather Googe Trends for an arbitrary list of keywords (about tools). It is inititalized with a reference keyword to compare relative popularity against"""
class GatherTools():
    def __init__(self, referencekeyword, unsaferun=False):
         self.results = {}
         self.kw = referencekeyword
         self.currenttools= [referencekeyword]
         self.toolboxes =[]
         self.unsaferun =unsaferun


    def reset(self):
        self.currenttools= [self.kw]
        self.toolboxes =[]

    def add(self,tool, toolbox=''):
        self.currenttools.append(tool)
        if toolbox != '': self.toolboxes.append(toolbox)
        if len(self.currenttools)>=5:
            res = self.queryGTrends(self.currenttools)
            self.store(res)
            self.reset()



    def store(self,res):
        for id,t in enumerate(self.currenttools):
            if not t == self.kw:
                #make sure trends are within plausible limits
                B = res[t] < res[self.kw] and res[t] >0
                if self.unsaferun: B = True
                if B:
                    if self.toolboxes!= []:
                        if self.toolboxes[id] not in self.results.keys():
                            self.results[self.toolboxes[id]]={t:str(res[t])}
                        else:
                            self.results[self.toolboxes[id]][t]=str(res[t])
                    else:
                        self.results[t]=str(res[t])


    def dump(self,res = 'GoogleTrends\\GTresults.json'):
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


def normalizeArcpyToolString(tool):
        #ex = 'CreateSchematicFolder_schematics'
        #Get the actual toolname (without toolbox and splitting at upper case letters)
        return ' '.join(re.findall('[A-Z][A-Z]*[a-z]*[0-9]*', tool.partition('_')[0]))


def normalizeGRASSToolString(tool):
    return tool.split("/")[-1]


def readToolBoxes(tooldictfile, listoftoolboxes=[]):
    tdict = {}
    with open(tooldictfile) as tooldictf:
        tooldict = json.load(tooldictf)
        if listoftoolboxes != []:
            for t in listoftoolboxes:
               tdict[t]=tooldict[t]
        else:
            tdict = tooldict
    tooldictf.close
    return tdict

"""Trends for tools"""
def getTrends4Tools(tooldict,referencekeyword, normalize=normalizeArcpyToolString):
    gt = GatherTools(referencekeyword)
    count = 0
    for k,v in tooldict.items():
        for tool in v:
            count+=1
            ntool = normalize(tool)
            gt.add(ntool,k)
    print 'Tool count '+str(count)
    gt.dump('GoogleTrends\\GTresults_kw'+referencekeyword+'.json')


def readSoft(softdictfile):
    with open(softdictfile) as softdictf:
        softdict = json.load(softdictf)
    softdictf.close
    return softdict

"""Trends for Software"""
def getTrends4Soft(softdict,referencekeyword):
    gt = GatherTools(referencekeyword, True)
    count = 0
    for k,v in softdict.items():
        count+=1

        if v['name']!= 'AutoCAD': gt.add(v['name'])
    print 'software count '+str(count)
    gt.dump('GoogleTrends\\Softresults_kw'+referencekeyword+'.json')

"""Bar chart visualization"""
def visualize(resultdump, twolayered =True, index ='ArcGIS Tools'):
    result = []
    fig, ax = plt.subplots(figsize=(15,8))

    with open(resultdump) as res:
        ress = json.load(res)
    if twolayered:
        for k,v in ress.items():
            for kk,vv in v.items():
                result.append({index:kk, 'Box':k,'GT Popularity':float(vv)})
    else:
        for k,v in ress.items(): #(math.log(float(v)+1) if float(v) != 0 else 0)
            value =(math.log(float(v)+1) if float(v) != 0 else 0)
            result.append({index:' '+k+' ', 'GT Popularity':value})

    df = pandas.DataFrame.from_dict(result)
    df =df.sort_values(by='GT Popularity', ascending=[False]).set_index(index)
    print df
    if twolayered:
        colors = {'Spatial Analyst Tools(sa)': 'c', 'Conversion Tools(conversion)': 'b'}
        pl = df['GT Popularity'].plot(kind='bar', width=1, fontsize=12, color=[colors[i] for i in df['Box']], figsize=(12,8))
        red_patch = mpatches.Patch(color='cyan', label='Spatial Analyst')
        blue_patch= mpatches.Patch(color='blue', label='Conversion Tools')
        lines = [blue_patch, red_patch]
        labels = [line.get_label() for line in lines]
        pl.legend(lines, labels)
    else:
        pl = df.plot(kind='bar', width=1, fontsize=17, colormap='Paired',zorder=3,#logy = True,#rot=80,
         legend=False, ax=ax)


    plt.tight_layout()

    ax.yaxis.grid(zorder=0, linestyle='dashed', color ='gray')
    ax.tick_params(axis='x', pad=8)
    #ax.bar(log=True)
    plt.ylabel('log (Google Trends Popularity index)', fontsize=18)
    plt.xlabel('GIS Software', fontsize=18)
    plt.show()



################ Methods to gather tools and software information from the web and integrate it

def getDBpediaCompany(url):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    query = """
    Select ?f WHERE {
    <"""+url+ """> <http://dbpedia.org/ontology/developer> ?f
    }
            """
    sparql.setQuery(query)  # the previous query as a literal string

    return sparql.query().convert()

def getGISSoftwareList():
    results = {}
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

    outf = 'ResourceCatalogue\\GISSoftdict.json'

    with open(outf, 'w') as fp:
        json.dump(results, fp)
    fp.close
    return outf


def buildArcToolList():
    print ('Number of Tools '+str(len(arcpy.ListTools())))
    toolboxes = arcpy.ListToolboxes()
    out = {}
    outf = 'ResourceCatalogue\\ArcGIStooldict.json'
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


def buildGRASSToolList(outf):
    results = {}
    WIKI_URL = "https://grass.osgeo.org/grass72/manuals/keywords.html"
    req = requests.get(WIKI_URL)
    soup = BeautifulSoup(req.content, 'lxml')
    wikitables = soup.findAll("dl")
    #print wikitables
    for table in wikitables:
        for cat in table.findAll("dt"):
            catname = cat.find('a').get('name') #This is a toolbox
            tools = []
            for url in cat.find_next_sibling('dd').findAll('a', href=True):
                tool = 'https://grass.osgeo.org/grass72/manuals/'+url.getText()
                tools.append(tool)
            results[catname]=tools
    with open(outf, 'w') as fp:
        json.dump(results, fp)
    fp.close
    return outf





###### Methods to generate RDF data from tools, software and the crawled network information

"""Given a csv file of tool webpages, links them to the tools in the tool dictionary"""
def readtoolpages(toolpf):
    output = {}
    with open('ResourceCatalogue\\ArcGIStooldict.json', 'rb') as fp:
        tooldict = json.load(fp)
    fp.close
    with open(toolpf) as toolf:
     reader = csv.reader(toolf, delimiter=',')
     next(reader) #skip the first line
     for row in reader:
            pagename= row[0]
            p = pagename.split('/')
            toolb = ' '.join([word.title() for word in (p[1].split('-')) if word.lower() != 'toolbox'])
            #print toolb
            tooln = ''.join([word.title() for word in(p[2].split('-'))])
            #print tooln
            website = row[2]
            res = {}
            for k,v in tooldict.items():
                mytoolb = k.split('Tools')[0].split('(')[0].split('_')[0].strip()
                #print mytoolb + ' : '+toolb.strip()
                if (mytoolb).lower() == toolb.strip().lower():
                    for t in v:
                        mytool = (t.split('_')[0].strip())
                        if mytool == tooln.strip():
                            print mytool +' : '+tooln
                            output[t]={'website':website,'toolbox':k, 'pagename':pagename}
                            break
                    break

     with open('ResourceCatalogue\\ArcGIStoolwebsites.json', 'w') as fp:
        json.dump(output, fp)
     fp.close
    toolf.close

"""Gets the homepages of a list of dbpedia entities"""
def getWebsite(urllist):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    tl ='<'+'>, <'.join(urllist)+'>'
    query = """
    Select ?f ?tool WHERE {
    ?tool <http://xmlns.com/foaf/0.1/homepage> ?f.
    FILTER(?tool in ("""+tl+"""))
    }
            """
    sparql.setQuery(query)  # the previous query as a literal string

    r = sparql.query().convert()
    com = []
    for f in r['results']['bindings']:
                    com.append((f['f']['value'],f['tool']['value']))
    return com


"""Method to integrate tool list, software list and websites into a single RDF file"""
def generateRDF(outf, softuri, tooldictf, softdictf=None, tooluris = True, normalize=normalizeArcpyToolString, toolwebsites='ResourceCatalogue\\ArcGIStoolwebsites.json'):
    from rdflib import URIRef, BNode, Literal, Namespace, Graph
    from rdflib.namespace import RDF, FOAF, RDFS

    dbo = Namespace("http://dbpedia.org/ontology/")
    dbp = Namespace("http://dbpedia.org/resource/")
    dc = Namespace("http://purl.org/dc/elements/1.1/")
    dct = Namespace("http://purl.org/dc/terms/")
    wf = Namespace("http://geographicknowledge.de/vocab/Workflow.rdf#")
    gis = Namespace("http://geographicknowledge.de/vocab/GISConcepts.rdf#")
    tools = Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")


    tdict = readToolBoxes(tooldictf)
    g = Graph()


    if softdictf != None:
        softdict = readSoft(softdictf)
        softwarelist = []
        for software,v in softdict.items():
            softwarelist.append(software)
            g.add((URIRef(software), RDF.type, dbo.Software))
            if 'name' in v.keys():      g.add((URIRef(software), FOAF['name'], Literal(v['name'])))
            if 'website' in v.keys():   g.add((URIRef(software),FOAF['isPrimaryTopicOf'], URIRef(v['website'])))
            if v['companies']!= []:     g.add((URIRef(software), dbo.developer, URIRef(v['companies'][0])))
        w = getWebsite(softwarelist)
        if w != []:
            for ww in w:
                g.add((URIRef(ww[1]),FOAF['homepage'],URIRef(ww[0])))
    else: #there is already some software tools, then load them
        g.parse(outf, format='turtle')

    toolws = readSoft(toolwebsites)

    #Now add the tools of some software softuri
    if URIRef(softuri) in g.all_nodes():
        for toolbox, toollist in tdict.items():
            tb = urllib.pathname2url(toolbox)
            g.add((tools[tb], RDF.type, gis.Toolbox))
            g.add((tools[tb], dct.isPartOf, URIRef(softuri)))
            g.add((tools[tb], FOAF.name, Literal(toolbox)))
            for t in toollist:
                toolst = (URIRef(t) if tooluris else tools[t])
                if t in toolws: g.add((toolst, FOAF['homepage'], URIRef(toolws[t]['website'])))
                g.add((toolst, RDF.type, gis.Tool))
                g.add((toolst, dct.isPartOf, tools[tb]))
                g.add((toolst, FOAF.name, Literal(normalize(t))))

    g.bind('dbo', URIRef("http://dbpedia.org/ontology/"))
    g.bind('dbp', URIRef("http://dbpedia.org/resource/"))
    g.bind('dc', URIRef("http://purl.org/dc/elements/1.1/"))
    g.bind('dct', URIRef("http://purl.org/dc/terms/"))
    g.bind('wf', URIRef("http://geographicknowledge.de/vocab/Workflow.rdf#"))
    g.bind('gis', URIRef("http://geographicknowledge.de/vocab/GISConcepts.rdf#"))
    g.bind('tools', URIRef("http://geographicknowledge.de/vocab/GISTools.rdf#"))
    g.bind('foaf',FOAF)
    g.bind('rdf',RDF)
    g.bind('rdfs', RDFS)
    print 'number of triples generated: '+str(len(g))
    g.serialize(destination=outf, format='turtle')


"""Given a list of edges for weblinks between webpages, filters out those that are between the webpages of a given list of ArcGIS tools"""
def filterToolLinks(linklist, toolnodes='ResourceCatalogue\\ArcGIStoolwebsites.json'):
    outf = 'Arcgis10_network\\linklist.csv'
    with open(outf, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        with open(toolnodes, 'rb') as fp:
            toolnodes = json.load(fp)
            tooln = []
            for k, v in toolnodes.items():
                tooln.append(v['pagename'])

            with open(linklist) as linkf:
                reader = csv.reader(linkf, delimiter=',')

                header = reader.next() #skip the first line
                spamwriter.writerow(header)
                for row in reader:
                    if row[0] in tooln and row[1] in tooln:
                        spamwriter.writerow(row)
            linkf.close
        fp.close
    csvfile.close


"""Adding hyperlink network between tools to RDF file, based on a list of edges for hyperlinks between tools"""
def addWeblinks(outf, linklist = 'Arcgis10_network\\linklist2.csv',toolnodes='ResourceCatalogue\\ArcGIStoolwebsites.json'):
     from rdflib import URIRef, BNode, Literal, Namespace, Graph
     from rdflib.namespace import RDF, FOAF, RDFS
     tools = Namespace("http://geographicknowledge.de/vocab/GISTools.rdf#")
     sioc = Namespace("http://rdfs.org/sioc/ns#")
     g = Graph()
     g.parse(outf, format='turtle')
     with open(toolnodes, 'rb') as fp:
        tooldict = json.load(fp)
     fp.close

     with open(linklist) as llist:
         reader = csv.reader(llist, delimiter=',')
         next(reader) #skip the first line
         for row in reader:
             toolfrom = ''
             toolto = ''
             for k,v in tooldict.items():
                if v['pagename'] == row[0]:
                    toolfrom = tools[k]
                if v['pagename'] == row[1]:
                    toolto = tools[k]
             if toolfrom != '' and toolto != '':
                    g.add((toolfrom, sioc.links_to, toolto))
     llist.close

     g.bind('dbo', URIRef("http://dbpedia.org/ontology/"))
     g.bind('dbp', URIRef("http://dbpedia.org/resource/"))
     g.bind('dc', URIRef("http://purl.org/dc/elements/1.1/"))
     g.bind('dct', URIRef("http://purl.org/dc/terms/"))
     g.bind('wf', URIRef("http://geographicknowledge.de/vocab/Workflow.rdf#"))
     g.bind('gis', URIRef("http://geographicknowledge.de/vocab/GISConcepts.rdf#"))
     g.bind('tools', URIRef("http://geographicknowledge.de/vocab/GISTools.rdf#"))
     g.bind('sioc', URIRef("http://rdfs.org/sioc/ns#"))
     g.bind('foaf',FOAF)
     g.bind('rdf',RDF)
     g.bind('rdfs', RDFS)
     print 'number of triples generated: '+str(len(g))
     g.serialize(destination=outf, format='turtle')





def main():

    ##Building list of ArcGIS tools
    #outf = buildArcToolList()

    ##Getting  Google Trends for ArcGIS toollist and visualize them with bar chart
    #td = readToolBoxes('ResourceCatalogue\\ArcGISTooldict.json', ['Spatial Analyst Tools(sa)','Conversion Tools(conversion)','Analysis Tools(analysis)'])
    #res = getTrends4Tools(td,'ArcGIS')
    #visualize('GoogleTrends\\GTresults_kwArcGIS.json')

    ##Building list of GIS software tools
    #getGISSoftwareList()

    ##Getting Google Trends for software list and visualize them as bar chart
    #sd = readSoft('ResourceCatalogue\\GISSoftdict.json')
    #getTrends4Soft(sd, 'ArcGIS')
    visualize('GoogleTrends\\Softresults_kwArcGIS.json', twolayered=False, index='GIS Software')

    ##Getting tool websites for ArcGIS toollist and filter those that correspond to a tool, writing everything into a json file
    #readtoolpages("Arcgis10_network\\arcgis_tool_pages.csv")
    #filterToolLinks('Arcgis10_network\\arcgis_tool_links_orders.csv',toolnodes='ResourceCatalogue\\ArcGIStoolwebsites.json')

    ##Generate RDF from softwarelist, the ArcGIS toollist, and the tool websites
    #generateRDF('ResourceCatalogue\\GISTools.ttl','http://dbpedia.org/resource/ArcGIS','ResourceCatalogue\\ArcGISTooldict.json','ResourceCatalogue\\GISSoftdict.json', tooluris=False, toolwebsites='ResourceCatalogue\\ArcGIStoolwebsites.json')

    ##Building GRASS GIS toollist
    #buildGRASSToolList('ResourceCatalogue\\GRASSTooldict.json')

    ##Getting  Google Trends for GRASS list
    #td = readToolBoxes('ResourceCatalogue\\GRASSTooldict.json', ['NDVI','terrain','landscape structure analysis', 'diversity index'])
    #res = getTrends4Tools(td,'GRASS GIS', normalize=normalizeGRASSToolString)
    #visualize('ResourceCatalogue\\GTresults_kwArcGIS.json')

    ##Adding Grass tools to the RDF file
    #generateRDF('ResourceCatalogue\\GISTools.ttl','http://dbpedia.org/resource/GRASS','ResourceCatalogue\\GRASSTooldict.json',tooluris=True, normalize=normalizeGRASSToolString)


    ##Adding network (hyper-) links to ArcGIS tools in the RDF file
    #addWeblinks('ResourceCatalogue\\GISTools.ttl')



if __name__ == '__main__':
    main()
