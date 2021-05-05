"""parse_thesaurus.py: parse Max object thesaurus

see: https://docs.cycling74.com/max8/vignettes/thesaurus

"""

from bs4 import BeautifulSoup
from pprint import pformat



# eg: https://docs.cycling74.com/max8/refpages/qlist
PREFIX = "https://docs.cycling74.com/max8"

# objects.html is downloaded from 
# https://docs.cycling74.com/max8/vignettes/thesaurus
with open('objects.html') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

db = soup.find_all('div')


def grouped():
    result = []
    for i in range(len(db)):
        entry = db[i]
        text = entry.h2.text
        links = entry.table.find_all('a')
        group = [(link.text, link['href'], text.strip()) for link in links]
        result.append(group)
    return result

def flat():
    result = []
    for i in range(len(db)):
        entry = db[i]
        text = entry.h2.text
        links = entry.table.find_all('a')
        group = [(link.text, link['href'], text.strip()) for link in links]
        result.extend(group)
    return result

def dual_dicts():
    descriptions = {}
    result = {}
    for i in range(len(db)):
        entry = db[i]
        text = entry.h2.text
        descriptions[i] = text.strip()
        links = entry.table.find_all('a')
        for link in links:
            result[link.text] = (link['href'], i)
    return descriptions, result


def dual_items():
    descriptions = {}
    result = []
    for i in range(len(db)):
        entry = db[i]
        text = entry.h2.text
        descriptions[i] = text.strip()
        links = entry.table.find_all('a')
        group = [(link.text, (link['href'], i)) for link in links]
        result.extend(group)
    return descriptions, result


def output_dual(descriptions, result, fname='objects.py'):
    with open(fname, 'w') as f:
        f.write(pformat(descriptions))
        f.write('/n/n')
        f.write(pformat(result))

if __name__ == '__main__':
    desc, res = dual_dicts()
    output_dual(desc, res, fname='registry.py')
