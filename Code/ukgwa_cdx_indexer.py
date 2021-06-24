#!/usr/bin/python3

import urllib.request
import gzip
from urllib.error import HTTPError
from ukgwa_cdx_reader import CDXReader
from ukgwa_view import UKGWAView

class TemporalIndexer(UKGWAView):

    def __init__(self):

        field_list = ['MIN','MAX','COUNT','CDX']
        super().__init__()
        self.set_fields(field_list)

    def add_entry(self, url, identifier=None, cdx_list = None):

        if identifier is None:
            identifier = url
        this_cdx = CDXReader(url, cdx_list)
        this_cdx.read_cdx()
        super().add_entry(identifier, [this_cdx.min_snapshot, this_cdx.max_snapshot, this_cdx.snapshot_count, this_cdx])

    def comparison(self, identifier, *args):

        if args[2] == self.fields['CDX']:
            this_cdx = self.index[identifier][self.fields['CDX']]
            matched = False
            for snap in this_cdx:
                this_comparison = this_cdx.comparison(snap, args[3:])
                if this_comparison:
                    matched = True
                    break
            return matched
        else:
            return super().comparison(identifier, *args)

    def load_from_gzip(self, gzip_file):
        # Big assumption that file is in url and date order
        this_url = ""
        return_list = []
        cdx_file = gzip.open(gzip_file, 'rb')
        for row in cdx_file:
            fields = row.decode('utf-8')[:-1].split(" ")
            if fields[2] != this_url:
                if len(return_list) > 0:
                    self.add_entry(this_url, cdx_list = return_list)
                this_url = fields[2]
                return_list = []
            return_list.append(row)
        if len(return_list) >= 0:
            self.add_entry(this_url, cdx_list=return_list)

        

if __name__ == '__main__':
    T = TemporalIndexer()
    T.add_entry("www.environment-agency.gov.uk")
    print(T.lookup("www.environment-agency.gov.uk"))
    #T.load_from_gzip("../Data/ukgwa_cdx_data.psv.gz")
    exit()

    T.add_entry("www.hm-treasury.gov.uk/d/sanctionsconlist.txt","E1")
    T.add_entry("www.salt.gov.uk/industry_activity.html","E2")
    print(T.comparison("E1", "MIN", ">", 20000101000000))
    print(T.comparison("E2", "MIN", ">", 20000101000000))
    print(T.comparison("E1", "MAX", ">", 20120101000000))
    print(T.comparison("E1", "MAX", ">", 20220101000000))
    print(T.comparison("E2", "MAX", ">", 20120101000000))
    print(T.comparison("E2", "MAX", ">", 20080101000000))
