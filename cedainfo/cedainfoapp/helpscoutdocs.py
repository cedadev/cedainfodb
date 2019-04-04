#
# Contains routines for accessing documentation in Helpscout
#
import os
import requests
import sys
import re
import time

AUTH = ('47ff11d6d6207a05189271b8805a8b888533a49a', 'X')
SERVICES_COLLECTION_ID = '59b25ba1042863033a1caf8f'
SERVICES_DOCUMENTATION_CATEGORY_ID = '5ca5d2b82c7d3a154461c260'



def get_collection (collection_id=SERVICES_COLLECTION_ID):

    """Returns the whole of the given collection as an array of json articles"""

    collection = []
    
    #
    # Get number of pages of the articles index
    #
    list_url = 'https://docsapi.helpscout.net/v1/collections/%s/articles' % collection_id
    r = requests.get(list_url, auth=AUTH)
    pages =  r.json()["articles"]["pages"]
    
    #
    # Now get each index page
    #
    for page in range(1, pages+1):
	params = {"sort": "name", "page": page}
	r = requests.get(list_url, auth=AUTH, params=params)

	items =  r.json()["articles"]["items"]
    #
    #   Fetch and process each article on this index page
    #
	for i in items:
	
	    try:
		article_url = 'https://docsapi.helpscout.net/v1/articles/%s' % i["id"]
		a = requests.get(article_url, auth=AUTH)
		
		collection.append(a)
		 
	    except Exception as e: print(e)	    
    
    return collection


def get_article_urls (collection_id=SERVICES_COLLECTION_ID):
#
#  Returns lists of urls of documents in given collection
#
	
    collection = get_collection(collection_id)
#
#   Make a list of helpscout article urls from this collection
#    
    helpscout_urls = []

    for article in collection:
        helpscout_urls.append(article.json()["article"]["publicUrl"])
	
    return helpscout_urls
    		   
    
def get_categories (collection):
#
#  Return dictionary of category names by id for the given collection
#
    categories = {}
    
    list_url = 'https://docsapi.helpscout.net/v1/collections/%s/categories' % '59b25ba1042863033a1caf8f'
    r = requests.get(list_url, auth=AUTH)

    ncategories = len(r.json()["categories"]["items"])


    for n in range(0, ncategories):
        category_id   = r.json()["categories"]["items"][n]["id"]
	category_name = r.json()["categories"]["items"][n]["name"]
	
	categories[category_id] = category_name

    return categories



def get_articles_in_category (collection, categoryid):
    """
    Filters the given collection and returns all articles that have the given categoryid
    """
    
    filtered_articles = []
    
    for article in collection:
        
        ncategories = len (article.json()["article"]["categories"])
		
	for n in range(0, ncategories):
	    catid = article.json()["article"]["categories"][n]
	    
	    if catid == categoryid:
	        filtered_articles.append(article)

    return filtered_articles

    
 
    

