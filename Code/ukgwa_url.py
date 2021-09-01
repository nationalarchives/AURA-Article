from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlunsplit
from ukgwa_hash import Hasher

class UKGWAurl:

    def __init__(self, url, parent=None, hash_alg = Hasher('md5')):

        self.url = url
        self.hasher = hash_alg
        self.ukgwa_prefix = "webarchive.nationalarchives.gov.uk/ukgwa/"
        self.ukgwa_protocol = "https://"
        self.prefix_len = len(self.ukgwa_prefix)
        prefix_pos = self.url.find(self.ukgwa_prefix)
        if prefix_pos >= 0:
            next_prefix_pos = self.url.find(self.ukgwa_prefix, prefix_pos+1)
            if next_prefix_pos > 0:
                self.url = url[next_prefix_pos + self.prefix_len:]
            else:
                self.url = url[prefix_pos + self.prefix_len:]
        if len(self.url) > 0:
            if self.url[0] == "/":
                self.url = self.url[1:]
            self.snap_len = 14
            if self.url[:2] in ['20','19']:  # assume snapshot
                slash_pos = self.url.find("/")
                self.snapshot = self.url[:slash_pos]
                self.url = self.url[slash_pos+1:]
            else:
                self.snapshot = None
            if self.url.find("http") < 0:
                if self.url.find("/") > 0:
                    self.url = "//" + self.url
            #if "://" not in self.url and "/" in self.url:
            #    self.url = "//" + self.url
        else:
            self.snapshot = None
        if parent is not None:
            self.url = urljoin(parent.url, self.url)
            if self.snapshot is None:
                self.snapshot = parent.get_snapshot()
        self.parts = urlsplit(self.url)
        self.actual_url = self
        self.hash = None
        self.hash_partition = None

    def get_hash(self):
        if self.hash is None:
            self.hash = self.hasher.get_hash(self.url)
        return self.hash

    def get_hash_partition(self):
        if self.hash_partition is None:
            self.hash_partition = self.hasher.get_hash_partition(self.get_hash())
        return self.hash_partition

    def get_domain(self, www=True):
        if len(self.parts.netloc) == 0:
            return None
        if www:
            if self.parts.netloc[:4] != 'www.':
                return 'www.' + self.parts.netloc
        return self.parts.netloc

    def set_redirect(self, redirected_url):
        self.actual_url = UKGWAurl(redirected_url, hash_alg = self.hasher)

    def get_url(self, actual=True, snapshot=True, prefix=True):
        if actual:
            this_url = self.actual_url
        else:
            this_url = self

        out_url = this_url.url
        if snapshot:
            if this_url.snapshot is not None:
                out_url = this_url.snapshot + "/" + out_url
        if prefix:
            out_url = this_url.ukgwa_protocol + this_url.ukgwa_prefix + out_url

        return out_url

    def get_snapshot(self):
        return self.snapshot

    def __str__(self):
        return self.get_url(actual=False, snapshot=True)

    def __repr__(self):
        return self.get_url(actual=False, snapshot=True)

if __name__ == "__main__":

    parent_url = "http://www.sample.com/sample"
    U = UKGWAurl(parent_url)
    U2 = UKGWAurl("/example",U)
    U2 = UKGWAurl("www.sample.com/example/sample",U)
    U2 = UKGWAurl("www.example.com/example",U)
    U2 = UKGWAurl("sample.com/example",U)
    U2 = UKGWAurl("https://webarchive.nationalarchives.gov.uk/200101/sample.com/example",U)
    U2 = UKGWAurl("webarchive.nationalarchives.gov.uk/20150305164200///www.keepbritaintidy.org/fly-tipping/-1/20/1/1005/0/o/0c48dd94-9878-42d1-9c01-64f474ae2230")
    U2 = UKGWAurl("//webarchive.nationalarchives.gov.uk/20150305163947///www.keepbritaintidy.org/fly-tipping/-1/20/1/1005/0/o/0c48dd94-9878-42d1-9c01-64f474ae2230")
    U2 = UKGWAurl("https://webarchive.nationalarchives.gov.uk/20150305164356/http://www.keepbritaintidy.org/webarchive.nationalarchives.gov.uk/20150305164348///www.keepbritaintidy.org/fly-tipping/-1/20/1/1005/0/o/0c48dd94-9878-42d1-9c01-64f474ae2230")
    print(U2.get_domain())
    print(U2.get_snapshot())
    print(U2)
