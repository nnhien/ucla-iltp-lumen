import requests
import os
import csv
import time
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
print(f'Querying page 1')
r = requests.get(CPJ_BASE_URL).json()
populate_orgs(r)
print(f'Querying page 2')

try:
    while r['meta']['next']:
        print(f'Querying page {r["meta"]["pageNum"]}')
        r = requests.get(r['meta']['next']).json()
        populate_orgs(r)
except KeyError:
    pass

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
    print(f'Querying Lumen for {org}...')
    params = {'recipient_name': org, 'recipient_name-require-all': True }
    r = requests.get(LUMEN_BASE_URL, params=params, headers=headers).json()
    notices[org].extend(r['notices'])
    time.sleep(1)

print(f'Found {len(notices)} DMCA notices from Lumen!')

# Print notices just in case so we don't have to fetch it again
with open('notices.txt', 'w') as txt_file:
    json.dump(notices, txt_file)

print(f'Writing to CSV...')
with open('notices.csv', 'wb') as csv_file:
        wr = csv.DictWriter(csv_file, fieldnames=list(notices[0].keys()))
        wr.writeheader()
        wr.writerows(notice)
print('Done!')