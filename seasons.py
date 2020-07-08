#!/bin/env python3
'''Retrieve and summarize which crags are best for a given month.'''

import os
import json
import requests
from argparse import ArgumentParser

#from bs4 import BeautifulSoup
from geohelper.distance import get_distance

REMOTE_DATA = 'https://www.mountainproject.com/files/seasons/MP_area_latlong_pop_season_data.json'
LOCAL_DATA = '.cache/data.json'
# Data is a list of json records with the following fields:
# - title: the name of the crag, not necesarily unique.
# - lat, lon: coordinates in floating points
# - season_1, season_2, ..., season_12: 0-1000 monthly quality. 1=jan, 12=dec
# - popularity: 0-4462 overal popularity of the crag, anything below 50 is fairly unknown
# - total: ??? how many routes there are in the area? 
# Notably missing is a unique ID.  We have to search MP with title to gather 
# more info on a particular area.

def fetch_data():
    '''Fetch the data UNLESS we have a recent copy already.  

    Return the data or raise if we can't retreive it.'''
    #TODO: see if the file is recent enough

    if os.path.isfile(LOCAL_DATA):
        data = open(LOCAL_DATA, 'r').read()
    else:
        resp = requests.get(REMOTE_DATA)
        data = resp.text

        dirname = os.path.dirname(LOCAL_DATA)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        open(LOCAL_DATA, 'w').write(data)

    return data


def cluster_recs(recs, radius=30000):
    '''Group crags in clusters no further than 'radius' meters apart from one another'''
    groups = []
    def cluster(rec):
        for group in groups:
            dist = get_distance(rec['lon'], rec['lat'], 
                                group[0]['lon'], group[0]['lat'])
            if dist < radius:
                group.append(rec)
                # can only be part of one cluster
                return
        # didn't match any cluter, start a new one
        groups.append([rec])

    for rec in recs:
        cluster(rec)
    return groups


def summarize_area(area):
    '''Return a dict summarizing all the crags in one area.'''
    summary = dict(nb_crags=len(area), 
                   nb_routes=0,
                   title=None,
                   avg_pop=None,
                   max_pop=0)
    tot_pop = 0
    title_pop = 0
    for rec in area:
        summary['nb_routes'] += rec['total']
        tot_pop += rec['popularity']
        if rec['popularity'] > title_pop:
            summary['title'] = rec['title']
            title_pop = rec['popularity']
        if rec['popularity'] > summary['max_pop']:
            summary['max_pop'] = rec['popularity']
    summary['avg_pop'] = tot_pop / len(area)
    return summary


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--min-popularity', type=int,
                        help='ignore crags less popular than MIN_POPULARITY')
    args = parser.parse_args()

    data = fetch_data()
    recs = json.loads(data)

    groups = cluster_recs(recs)
    from pprint import pprint 
    pprint(list(map(summarize_area, groups)))

    # TODO: filter out low popularity crags
    # TODO: filter by month


if __name__ == '__main__':
    main()
