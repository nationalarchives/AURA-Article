#!/usr/bin/python3

import urllib.request
from urllib.error import HTTPError
from ukgwa_view import UKGWAView
from bs4 import BeautifulSoup
import re
import json

class CDXReader(UKGWAView):

    def __init__(self, url, cdx_list=None):
        field_list = ['DOMAIN','SNAPSHOT','MIME','CODE','CHECKSUM','CHANGED']
        super().__init__()
        self.set_fields(field_list)
        self.ukgwa_prefix = "https://webarchive.nationalarchives.gov.uk/ukgwa/"
        cdx_options = "&output=json"
        # https://webarchive.nationalarchives.gov.uk/largefiles-cdx?
        self.min_snapshot = 90000000000000
        self.max_snapshot = 00000000000000
        self.snapshot_count = 0
        if cdx_list is None:
            cdx_prefix = self.ukgwa_prefix + "cdx?url="
            self.url = url
            self.cdx_url = cdx_prefix + url + cdx_options
            try:
                self.return_list =  urllib.request.urlopen(self.cdx_url)
                self.success = True
            except:
                self.success = False
            if not self.success:
                self.return_list = self.backup()
                self.success = True

        else:
            self.return_list = cdx_list
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
            #print("D",dictionary)
            if dictionary['status'] not in returncodes:
                continue
            entry = [dictionary["urlkey"], int(dictionary["timestamp"]), dictionary["mime"],
                     dictionary["status"], dictionary["digest"], prev_checksum != dictionary["digest"]]
            prev_checksum = dictionary["digest"]
            self.min_snapshot = min(self.min_snapshot, entry[self.fields['SNAPSHOT']])
            self.max_snapshot = max(self.max_snapshot, entry[self.fields['SNAPSHOT']])
            self.snapshot_count += 1
            self.add_entry(entry[self.fields['SNAPSHOT']], entry)

    def nearest_to(self, timestamp):

        if isinstance(timestamp, str):
            test_time = int(timestamp.ljust(14, '0'))
        else:
            test_time = timestamp

        best_diff = 999999999999
        nearest = 0
        for snap in self:
            this_diff = abs(test_time-snap)
            if this_diff < best_diff:
                best_diff = this_diff
                nearest = snap

        return nearest




if __name__ == '__main__':
    #mycdx = CDXReader("www.hm-treasury.gov.uk/d/sanctionsconlist.txt")
    mycdx = CDXReader("http://www.salt.gov.uk/industry_activity.html")
    #mycdx = CDXReader("http://ukinholysee.fco.gov.uk/en/news/?view=News&id=791576182")
    mycdx.read_cdx()
    for s in mycdx:
        print(s)

    print("Best:",mycdx.nearest_to("20081101"))
