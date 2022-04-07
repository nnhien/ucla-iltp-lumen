import requests
import os
import csv
import datetime
import json

LUMEN_BASE_URL="https://lumendatabase.org/notices/search"
CPJ_BASE_URL="https://api.cpj.org/v1/persons/"
LUMEN_KEY=os.getenv("LUMEN_KEY", None)

if LUMEN_KEY is None:
    print('You must provide an API key to the Lumen Database')
    exit(1)

organizations = set()

def populate_orgs(r):
    data = r['data']
    for person in data:
        for entry in person['entries']:
            org = entry['organizations']
            organizations.add(org)

# Get set of all organizations from CPJ

# See if we have a list already cached
print('Querying CPJ for list of organizations')
try:
    with open('orgs.json', 'r') as orgs_file:
        print('Found cached file!')
        organizations = set(json.loads(orgs_file.readline()))
except FileNotFoundError:
    r = requests.get(CPJ_BASE_URL).json()
    populate_orgs(r)

    try:
        while r['meta']['next']:
            print(f'Querying page {r["meta"]["pageNum"]}')
            r = requests.get(r['meta']['next']).json()
            populate_orgs(r)
    except KeyError:
        pass

    with open('orgs.json', 'w') as orgs_file:
        orgs_file.write(json.dumps(list(organizations)))

print(f'Found {len(organizations)} organizations from CPJ')

headers = \
{   
    'User-Agent': 'ucla-itlp',
    'X-Authentication-Token': LUMEN_KEY,
    'Accept': 'application/json',
    'Content-Type': 'application/json' 
}

notices = {}

for org in organizations:
    try:
        print(f'Querying Lumen for {org}...')
        if org not in notices:
            notices[org] = []
        params = {'recipient_name': org }
        r = requests.get(LUMEN_BASE_URL, params=params, headers=headers).json()
        notices[org].extend(r['notices'])

        # If there are more pages, grab those too
        if r['meta']['total_pages'] > 1:
            print(f'{org} has {r["meta"]["total_pages"]} pages of results')
            for page in range(2, r['meta']['total_pages'] + 1):
                print(f'Querying page {page}')
                params['page'] = page
                r = requests.get(LUMEN_BASE_URL, params=params, headers=headers).json()
                notices[org].extend(r['notices'])
    except KeyError:
        # Ignore any missing keys due to inconsistent API response (smh)
        pass

print(f'Found {len(notices)} DMCA notices from Lumen!')

# Print notices just in case so we don't have to fetch it again
with open('notices.json', 'w') as txt_file:
    json.dump(notices, txt_file)

print('Done!')