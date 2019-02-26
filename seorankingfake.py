import json
import urllib3
import requests
import time

env='staging'
max_iterations = 500

environments={
    'qa': {
        'webservice': 'http://lebqapp01.localedge.com:8082/seoranker-services/',
        'apiKey': 'n5x4A0im1QiIvB4D76pn2ec8a562979671e1ebdc7ad7f1a4bf63'
    },
    'staging': {
        'webservice': 'http://lecsawsapp03.localedge.com:8080/seoranker-services/',
        'apiKey': 'pNGBRdk1WbieaZdeuRme2ec8a562979671e1ebdc7ad7f1a4bf63'
    }
}
apikey=environments[env]['apiKey']
webservice=environments[env]['webservice']

endpoint=webservice+'ranking'
process_name='eja-pythonclient'

def getKeyword():
    payload={'processName':process_name, 'apiKey':apikey}
    r = requests.get(endpoint, params=payload)
    response = r.json();
    rank_id = response['identifier']
    return response

def createSearchResult(url_fragment_identifier, search_phrase_identifier):
    return {
        "numberOfRequests": 1,
        "rank": 1,
        "totalResults": 311,
        "urlFragmentIdentifier": url_fragment_identifier,
        "searchPhraseIdentifier": search_phrase_identifier,
        "rankAttemptDetails": [
            {
            "detail": None,
            "html": "",
            "code": 0,
            "type": "SUCCESS"
            }
        ]
    }

def createRankOperationResult(rank_operation):
    url_fragment_identifier = rank_operation['urlFragmentsToMatch'][0]['identifier']
    operation_identifier = rank_operation['identifier']
    search_engine_identifier = rank_operation['searchEngine']['identifier']

    payload = {
        "returnNextRankOperation": True,
        'searchResults':[],
        "operationIdentifier": operation_identifier,
        "processName": process_name,
        "searchEngineIdentifier": search_engine_identifier
    }

    search_terms = rank_operation['searchTerms']
    for term in search_terms:
        payload['searchResults'].append(createSearchResult(url_fragment_identifier, term['identifier']))

    return payload

def postRanking(rank_operation):
    payload = createRankOperationResult(rank_operation)
    params = {'apiKey':apikey}
    r = requests.post(endpoint, json=payload, params=params)
    response = r.json()
    return response

    
def exitCriteria(rank_operation):
    if rank_operation['searchEngine']['identifier'] == 7 or counter >= max_iterations:
        return True
    else:
        return False

rank_operation = getKeyword()

print(rank_operation)

counter=0

while exitCriteria(rank_operation) == False:
    time.sleep(0.25)
    rank_operation = postRanking(rank_operation)
    print(rank_operation)
    counter++
