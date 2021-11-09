import requests
from time import sleep
from urllib.request import urlopen
import re
from bs4 import BeautifulSoup
from ukgwa_view import UKGWAView
from ukgwa_textindex import UKGWATextIndex
import random
from operator import itemgetter


class DiscoSearch(UKGWAView):

    def __init__(self, page_limit=100, search_limit=1000, randomised=False):

        super().__init__()
        field_list = ["id", "description", "startDate", "endDate", "urlParameters", "adminHistory",
                           "context", "taxonomies", "reference"] # Discovery fields
        self.set_fields(field_list)
        #self.field_list = ["id","coveringDates","coveringFromDate","coveringToDate","recordOpeningDate",["scopeContent","description"],
        #                   "closureType","citableReference","isParent"]
        self.page_limit = page_limit
        self.randomised = randomised
        self.ABSOLUTEMAX = 10000
        #self.fields = {"IAID" : 0, "Description" : 1, "StartDate": 2, "EndDate": 3, "Path": 4, "Admin": 5,
        #               "Context": 6, "Taxonomy": 7}
        self.sample_pct = 0.01
        self.min_sample = 10
        self.max_sample = 500
        self.search_limit = search_limit

    def add_entry(self, search_string, start_series=[]):

        for rec in self._page_iterator(search_string, start_series):
            super().add_entry(rec[0], rec)

    def set_random(self, randomised):

        self.randomised = randomised

    def _do_search(self, search_string, departments, page_number = 1, page_size=15):

        headers={"Accept": "application/json"}; #we want the API to return data in JSON format
        url="http://discovery.nationalarchives.gov.uk/API/search/v1/records?sps.recordCollections=Records&sps.heldByCode=TNA&sps.searchQuery=" + \
             search_string + "&sps.page=" + str(page_number) + "&sps.resultsPageSize=" + str(page_size)
        for d in departments:
            url += "&sps.departments=" + d
        s=requests.Session(); #creating a session just groups the set of requests together
        #myparams={"resultsPageSize": page_size}
        myparams = {}
        r=s.get(url, headers=headers, params=myparams); #send the url with our added parameters, call the response "r"
        r.raise_for_status(); #This checks that we received an http status 200 for the server response
        #print(len(r.json()["records"]),url)

        return r.json()

    def _prep_record(self, record):

         out_fields = []
         for f in self.field_list:
            if isinstance(f,str):
                field_value = record[f]
            elif isinstance(f,list):
                field_value = record[f[0]][f[1]] # could be recursive but for now it is only for the scope content description
                field_value = self._clean_scope(field_value)
            out_fields.append(field_value)
         return out_fields

    def _page_iterator(self,search_string, departments = []):

        rjson = self._do_search(search_string, departments)
        searches = []
        #print("Record count:", rjson["count"])
        if rjson["count"] <= self.search_limit:
            # TODO: There's a bug here because this bit should loop through pages as below
            # want to choose the right way to do it and avoid duplicating code.
            # Maybe rename this function to department_iterator and have a separate one for iterating the actual pages?
            # Not urgent for now.
            searches.append([])
            for rec in rjson["records"]:
                fields = self._prep_record(rec)
                yield fields

        else:
            departments = rjson["departments"][:]
            remaining = self.search_limit
            dep_list = []
            dep_pos = 0
            added = 0
            while len(departments) > 0:
                if departments[0]["count"] >= self.search_limit:
                    dep = departments.pop(0)
                    searches.append([dep])
                    #print("Adding",dep)
                    added += 1
                    continue

                if departments[dep_pos]["count"] <= remaining:
                    dep_list.append(departments[dep_pos])
                    remaining -= departments[dep_pos]["count"]
                    del departments[dep_pos]
                    continue
                if dep_pos == len(departments)-1 or remaining == 0:
                    #print("Adding",dep_list, remaining)
                    searches.append(dep_list)
                    added += len(dep_list)
                    remaining = self.search_limit
                    dep_list = []
                    dep_pos = 0
                    continue
                dep_pos += 1
            if len(dep_list) > 0:
                searches.append(dep_list)
                #print("Adding:", len(dep_list),"deps")
                added += len(dep_list)
            #print("Added:",added)

            while len(searches) > 0:
                next_search = searches.pop(0)
                total_count = sum([x["count"] for x in next_search])
                codes = [x["code"] for x in next_search]
                #print("Searching for", codes,"Records:",total_count)
                if total_count > self.search_limit:
                    total_count = self.search_limit
                pages = total_count / self.page_limit
                if int(pages) != pages:
                    pages = int(pages) + 1
                for p in range(1,int(pages)+1):
                    records = self._do_search(search_string, codes, page_number=p, page_size=self.page_limit)
                    for rec in records["records"]:
                        fields = self._prep_record(rec)

                        yield fields



    def _clean_text(self, text):
        new_text = text.replace("."," ").replace(","," ").replace("'","").replace(":"," ") \
                       .replace(";"," ").replace("-"," ").replace("("," ").replace(")"," ") \
                       .replace("["," ").replace("]"," ").replace("\n"," ")
        new_text = new_text.replace("`"," ")
        len_now = len(new_text)
        go = True
        while go:
            new_text = new_text.replace("  ", " ")
            if len_now == len(new_text):
                go = False
            else:
               len_now = len(new_text)
        return new_text

    def _clean_scope(self, scope):

        if scope is None:
            return ""
        soup = BeautifulSoup(scope, "html.parser")
        C = True
        while C:
            if soup.extref is None:
                C = False
                continue
            soup.extref.decompose()
        text = soup.findAll("p")
        this_text = ''
        for t in text:
            #print("\t",t.text)
            #print("\t\t",t)
            this_text += " " + t.text
        this_text = self._clean_text(this_text)

        return this_text


if __name__ == "__main__":

    import csv
    from bs4 import BeautifulSoup as BS

    quotes = "&#34"
    start_tag = "<extref href=" + quotes
    end_tag = "</extref>"
    ukgwa = "webarchive.nationalarchives.gov.uk"
    cat_file = open("8_Catalogue_Descriptions.csv","r", encoding = 'latin1')
    cat_desc = csv.reader(cat_file)
    out_file = open("web_catrefs.txt","w")
    for row in cat_desc:
        catref = row[0]
        desc = row[7]
        text = desc

        extref_start = text.find(start_tag)
        gotone = False
        while extref_start >= 0:
            extref_end = text.find(end_tag)
            extref = text[extref_start+len(start_tag):extref_end]
            web = text.find(ukgwa)
            #if web >= 0:
            #    print(web, extref_start, extref_end)
            if web >= 0:
                if extref_start < text.find(ukgwa) < extref_end:
                    quote_pos = extref.find(quotes)
                    if quote_pos > 0:
                        extref = extref[:quote_pos]
                        print(catref,extref)
                        out_file.write(catref + "|" + extref + "\n")
                        gotone = True
                    else:
                        print("No end quote:", extref)
            text = text[extref_end+len(end_tag):]
            extref_start = text.find(start_tag)
            #if extref_start >= 0:
            #    print("S:",extref_start, "T:",text, "E:",extref_end)
        #if gotone:
        #    break

    out_file.close()

    ref_file = open("web_catrefs.txt","r")
    lookup = {}
    for row in ref_file:
        fields = row[:-1].split("|")
        if fields[0] in lookup:
            lookup[fields[0]].append(fields[1])
        else:
            lookup[fields[0]] = [fields[1]]
    ref_file.close()
        
    cat_file.close()

    D = DiscoSearch()

    D.add_entry("web AND snapshots", [])

    c = 0
    for d in D:
        print(D.lookup(d))
        c += 1
        if c == 5:
            break


    exit()
    c = 0
    taxonomies = {}
    for d in D:
        c += 1
        #if len(D.get_field(d, "Admin")) == 0:
        #    c += 1
        #    continue
        #    #print(d, D.lookup(d))
        tax = D.get_field(d, "taxonomies")
        for t in tax:
            if t == 'C10004 Archives and libraries':
                print(D.get_field(d, "context"))
            if t in taxonomies:
                taxonomies[t] += 1
            else:
                taxonomies[t] = 1
    print(c)
    exit()

    print(taxonomies)
    print(sum([v for k,v in taxonomies.items() if k != 'C10136 Official publications']))

    T = UKGWATextIndex(stop_words = ["", "and", "of", "the", "in", "a", "by", "which", "their","as","an",
                                     "for","to","if","be","this","on","are","at","were","it","is","that",
                                     "from","been","has","have","or","there","was","they","with","these"])
    c = 0
    for d in D:
        a = D.get_field(d, "adminHistory")
        if len(a) > 0:
            c += 1
            T.add_entry(d, a.split(" "))
    print("Admins:",c)

    P = [p for p in T.get_phrases(min_count=20, min_length=2, max_length=3)]
    P.sort(key=itemgetter(1), reverse=False)
    for p in P:
        print(" ".join(p[0]), p[1])

