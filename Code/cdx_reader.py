#!/usr/bin/python3

import urllib.request
from urllib.error import HTTPError
from ukgwa_view import UKGWAView
from bs4 import BeautifulSoup
import re
import json

class CDXReader(UKGWAView):

    def __init__(self, url):
        super().__init__()
        self.ukgwa_prefix = "https://webarchive.nationalarchives.gov.uk/ukgwa/"
        cdx_prefix = self.ukgwa_prefix + "cdx?url="
        cdx_options = "&output=json"
        self.url = url
        self.cdx_url = cdx_prefix + url + cdx_options
        self.fields['SNAPSHOT'] = 0
        self.fields['MIME'] = 1
        self.fields['CODE'] = 2
        self.fields['CHECKSUM'] = 3
        self.fields['CHANGED'] = 4
        self.min_snapshot = 90000000000000
        self.max_snapshot = 00000000000000
        self.snapshot_count = 0
        self.snapshot_list = []
        try:
            self.return_list =  urllib.request.urlopen(self.cdx_url)
            self.success = True
        except:
            self.success = False
        if not self.success:
            self.return_list = self.backup()
            self.success = True

    def backup(self):

        print("Using backup")
        url = self.ukgwa_prefix + "*/" + self.url
        version_list = []
        try:
            html = urllib.request.urlopen(url)
        except Exception as e:
            print(e)
            return
        soup = BeautifulSoup(html, 'html.parser')

        if url[len(self.ukgwa_prefix)-1:len(self.ukgwa_prefix)+2] != "/*/":
            print("Url problem")
            return
        domain = url[len(self.ukgwa_prefix)+2:]

        accordions = soup.findAll("div", {"class": "accordion"})
        for acc in accordions:
            year = acc.find("span", {"class" : "year"})
            # Not working for http://ukinholysee.fco.gov.uk/en/news/?view=News&id=791576182
            # Can't quite fathom why. "domain in" works fine further down
            #versions = acc.findAll("a", href=re.compile(".[1-2]*" + domain.replace("&","&amp;"), re.IGNORECASE))
            versions = acc.findAll("a")
            for v in versions:
                href = v['href']
                if domain not in href:
                    continue
                snapshot = v['href'][1:15]
                entry = ["","","",snapshot,"","","200","0","","",""]
                version_list.append(" ".join(entry))

        return version_list

    def add_to_dict_list(self, D, key, value):
        if key in D:
            D[key].append(value)
        else:
            D[key] = [value]

    def read_cdx(self, returncodes = ['200','301']):

        if not self.success:
            return

        prev_checksum = '0'
        for row in self.return_list:
            dictionary = json.loads(row)
            if dictionary['status'] not in returncodes:
                continue
            entry = [int(dictionary["timestamp"]), dictionary["mime"], dictionary["status"], dictionary["digest"], prev_checksum != dictionary["digest"]]
            prev_checksum = dictionary["digest"]
            self.min_snapshot = min(self.min_snapshot, entry[self.fields['SNAPSHOT']])
            self.max_snapshot = max(self.max_snapshot, entry[self.fields['SNAPSHOT']])
            self.snapshot_count += 1
            self.add_entry(entry[self.fields['SNAPSHOT']], entry)

if __name__ == '__main__':
    #mycdx = CDXReader("www.hm-treasury.gov.uk/d/sanctionsconlist.txt")
    #mycdx = CDXReader("www.salt.gov.uk/industry_activity.html")
    #mycdx = CDXReader("http://ukinholysee.fco.gov.uk/en/news/?view=News&id=791576182")
    #mycdx = CDXReader("www.salt.gov.uk/index.shtml")
    #mycdx = CDXReader("www.salt.gov.uk")
    import requests
    prefix = "https://webarchive.nationalarchives.gov.uk/ukgwa/"
    start_url = "http://www.salt.gov.uk/"
    start_url = "http://www.eatwell.gov.uk/healthydiet/fss/salt/"
    start_url = "http://www.nhs.uk/Livewell/Goodfood/Pages/salt.aspx"
    start_url = "http://www.salt.gov.uk/index.html"
    mycdx = CDXReader(start_url)
    mycdx.read_cdx(['200','301','302','404'])
    for s in mycdx:
        status = mycdx.get_field(s, 'CODE')
        this_url = prefix + str(s) + "mp_/" + start_url
         
        this_request = requests.get(this_url, allow_redirects=False)
        print("\tUrl:", this_url)
        print("\tCode",this_request.status_code,"CDX code", status)  # 302
        print("\tUrl",this_request.url)  # http://github.com, not https.
        #print("Headers:",this_request.headers)
        #print("History:",this_request.history)

        #print("Content:",this_request.text[100:200])
        if this_request.status_code in [301,302]:
            print("Location",this_request.headers['Location'])  # https://github.com/ -- the redirect destination

        print(s, mycdx.get_field(s, 'CODE'))
