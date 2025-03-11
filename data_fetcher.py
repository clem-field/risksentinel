### required libs
import requests
from bs4 import BeautifulSoup as bs
import urllib.request

##################################################
###             Get data from DISA             ###
##################################################

disa_url = "https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/"
disa_file = "U_SRG-STIG"

disa_page = requests.get(disa_url)

scrape = bs(disa_page, 'html.parser')
disa_link = [disa_url + '/' + node.get('fref') for node in scrape.find_all('a') if node.get('href').endswith('zip')]

for link in disa_link:
    print(link)
    filename = link.split('/')[-1]
    print(filename)
    # urllib.request.urlretrieve(link,filename)

