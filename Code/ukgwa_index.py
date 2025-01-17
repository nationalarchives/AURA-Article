from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
from ukgwa_view import UKGWAView
from ukgwa_query import QueryEngine
from ukgwa_url import UKGWAurl

class UKGWAIndex(UKGWAView):

    def __init__(self, ukgwa_prefix = "https://webarchive.nationalarchives.gov.uk/",
                       index_url = "http://www.nationalarchives.gov.uk/webarchive/atoz/",
                       id_prefix = "UKGWA",
                       file_delimiter = "|"):

        field_list = ['REF','TEXT','CAT','URL','CATREF']
        super().__init__()
        self.set_fields(field_list)
        # self.add_entry(reference, [reference, link.text.replace("\n"," ").strip(), category, href, 'N'])
        self.discoverylookup = {}
        self.filedelimiter = file_delimiter
        self.ukgwa_prefix = ukgwa_prefix
        self.atoz_url = index_url
        self.id_prefix = id_prefix

    def indexfromfile(self, filepath):

        atozfile = open(filepath, 'r')
        for row in atozfile:
            fields = row[:-1].split(self.filedelimiter)
            self.index[fields[0]] = fields
        self.maxindex = len(self.index)
        atozfile.close()

    def indextofile(self, filepath):

        indexfile = open(filepath, 'w')
        for idx in self:
            indexfile.write(self.filedelimiter.join([str(x) for x in self.index[idx]]))
            indexfile.write("\n")
        indexfile.close()

    def discoveryfromfile(self, filepath, update=True):

        discoveryfile = open(filepath, 'r')
        for row in discoveryfile:
            fields = row[:-1].split(self.filedelimiter)
            url = fields[1]
            #star_pos = url.find("/*/")
            #if star_pos > 0:
            #    url = url[star_pos+3:]
            url = UKGWAurl(url)
            self.discoverylookup[url] = fields[0]
        discoveryfile.close()
        for k,v in self.discoverylookup.items():
            break

        if update:
            self._matchukgwatodiscovery()

    def _matchukgwatodiscovery(self):

        discovery_urls = [u for u in self.discoverylookup.keys()]
        for idx in self:
            url = self.get_field(idx, 'URL')
            found = False
            #print(url.get_url(prefix=False, snapshot=False))
            for i,u in enumerate(discovery_urls):
                #print("\t",u.get_url(prefix=False,snapshot=False))
                if url.equals(u):
                    found = True
                    break

            if found:
                discovery_urls.pop(i)

                self.update_field(idx, 'CATREF', self.discoverylookup[u])

    def indexfromweb(self):

        # Should read these from project parameters eventually

        html = urlopen(self.atoz_url)
        soup = BeautifulSoup(html, 'html.parser')

        links = soup.findAll("a", href=re.compile(self.ukgwa_prefix))

        row_id = 0
        for link in links:
            href = link['href']
            url = UKGWAurl(href)
            #href = href[len(self.ukgwa_prefix):]
            #category = href.split("/")[0]
            #href = href[len(category)+1:]
            #if len(href) == 0:
            #    continue
            #if href[:2] == "*/":
            #    href = href[2:]
            row_id += 1
            reference = self.id_prefix + "." + str(row_id)
            self.add_entry(reference, [reference, link.text.replace("\n"," ").strip(), url.collection, url, 'N'])
        self.maxindex = row_id

#    def __iter__(self):
#        self.iterindex = 1
#        return self
#
#    def __next__(self):
#        if self.iterindex > self.maxindex:
#            raise StopIteration
#
#        next_reference = self.id_prefix + "." + str(self.iterindex)
#        self.iterindex += 1
#        return self.index[next_reference]

if __name__ == "__main__":


    idx = UKGWAIndex()
    idx.indexfromweb()
    #idx.indextofile("testatozfile.txt")
    idx.discoveryfromfile("../Data/ukgwa_catrefs.txt")
    bis = 0
    for x in idx:
        catref = idx.get_field(x,'CATREF')
        if "BIS " in catref:
            bis += 1
    print("BIS:",bis)

    exit()
    print(idx.lookup("UKGWA.5"))
    idx.update_field("UKGWA.5", "CATREF", "HO 42")
    idx.update_field("UKGWA.9", "CATREF", "HO 47")
    print(idx.lookup("UKGWA.5"))

    Q = QueryEngine()
    Q.add_view("AtoZ", idx)
    filt = Q.filter_view("AtoZ","CATREF",'<>',"N")
    for f in filt:
        print("Match",f)
        break
