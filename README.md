# GISTrends
GIS software, tools and methods on the web

This repository contains code and data used to collect, integrate and analyse Web resources about GIS software, tools and related topics on the Web.

=================================

*Abstract:* Every day, practitioners, researchers, and students consult the Web to meet their information needs about GIS concepts and tools. How do we improve GIS in terms of conceptual organisation, findability, interoperability, relevance for user needs? So far, efforts have been mainly top-down, overlooking the actual usage of software and tools.
In this article, we critically explore the potential of Web science to gain knowledge about tool usage and public interest in GIScience concepts. First, we analyse behavioural data from Google Trends, showing clear patterns in searches for GIS software.
Second, we analyse the visits to GIScience-related websites, highlighting the continued dominance of ESRI, but also the rapid emergence of Web-based new tools and services. We then study the views of Wikipedia articles to enable the quantification of methods and tools' popularity. Fourth, we deploy web crawling and network analysis on the ArcGIS documentation to observe the relevance and conceptual associations among tools. Finally, in order to facilitate the study of GIS usage across the Web, we propose a linked-data catalogue to identify Web resources related to GI concepts, methods, and tools. This catalogue will also enable researchers, practitioners, and students to find what methods are available across software packages, and where to find information about them.

*Keywords:* GIS; Geographic information science; GIScience; GIS operations; Web science; Google Trends; Wikipedia; ArcGIS; Linked data
Members & contributors:
* Dr. **Simon Scheider** ([home](http://geographicknowledge.de))
* Dr. **Andrea Ballatore** ([home](http://sites.google.com/site/andreaballatore))
* Dr. **Rob Lemmens** ([home](http://www.itc.nl/resumes/lemmens))


Compare the article (under review): https://www.overleaf.com/read/cqbfdckkxcvc

Data and code resources (corresponding to sections in this article):

* [gistrends.py](gistrends.py): Python code containing methods for [/GoogleTrends](/GoogleTrends) and [/ResourceCatalogue](/ResourceCatalogue)
* [/GoogleTrends](/GoogleTrends)  (section 3): Contains resources to compare relative popularity among tool/software keywords on Google Trends
* [/GIScienceWebsites](/GIScienceWebsites) (section 4): Contains resources to measure popularity of GIScience related websites (about software and companies)
* [/GIScienceWikipedia](/GIScienceWikipedia) (section 5): Contains resources to measure popularity of Wikipedia pages about GIScience related themes
* [/Arcgis10_network](/Arcgis10_network) (section 6): Contains resources to crawl, scrape and analyse network links for ArcGIS help pages
* [/ResourceCatalogue](/ResourceCatalogue) (section 7): Contains resources for integrating and publishing all information as a linked data file



