from urllib.error import HTTPError

from bs4 import BeautifulSoup
from urllib.request import (
    urlopen, urlparse, urlunparse, urlretrieve, Request)
import re
import logging
import sys
import csv
from urllib.parse import urljoin

from multiprocessing.dummy import Pool as ThreadPool
import csv
import multiprocessing
import threading

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class SwMatcher:

    def __init__(self, repoid, url):
        self.baseurl = ""
        self.soup = ""
        self.response = ""
        self.hints = []
        self.content = ""
        try:
            logging.info("Connecting to %s for repo %s", url, repoid)
            self.response = urlopen(url, context=ctx, timeout=5)
            self.baseurl = self.response.geturl()
            self.content = self.response.read()
            self.soup = BeautifulSoup(self.content, "html.parser")
            f = open("repo_pages/" + repoid + ".html", "wb")
            f.write(self.content)
            f.close()
        except HTTPError as e:
            # do something
            logging.error("HTTP Failed %s", e)
            raise e

        except Exception as e:
            # do something
            logging.error("Failed for other reasons %s", e)
            raise e

    def get_hint_in_html(self):
        matches = self.soup.findAll("meta", {"name": re.compile(r'.*(eprints_).*')})
        if matches:
            self.hints.append("META tag contains Eprints")
        matches = self.soup.findAll(re.compile(".*/handle/.*|.*/bitstream/.*"))
        if matches:
            self.hints.append("URL in the page contains Handle or Bitstream")
        matches = self.soup.findAll(re.compile(".*javax.*"))
        if matches:
            self.hints.append("Java Based application")
        matches = self.soup.select('div[class*="ep_"]')
        if matches:
            self.hints.append("Eprints HTML classes")
        matches = self.soup.select('div[class*="ds-"]')
        if matches:
            self.hints.append("DSpace HTML classes")
        matches = self.soup.find('a', href=re.compile(r'.*aspx'))
        if matches:
            self.hints.append("Aspx pages found")
        matches = self.soup.findAll("meta", {"name": "Opus - Version"})
        if matches:
            self.hints.append("Meta with Opus version:" + matches[0]["content"])
        return

    def get_generator_from_meta(self):
        matches = self.soup.findAll("meta", {"name": "Generator"})
        if matches and len(matches) > 0:
            return matches[0]["content"]
        matches = self.soup.findAll("meta", {"name": "generator"})
        if matches and len(matches) > 0:
            return matches[0]["content"]

    def get_hint_from_text(self):

        tag_re = re.compile(r'(<!--.*?-->|<[^>]*>|\\n|\\\\x[a-z])')
        text = str(self.content).lower()
        p = re.compile("built on (.*)(<\/a>|<br|<\/p>|\\n)")
        matches = p.findall(text)
        if matches:
            for m in matches:
                match = tag_re.sub('', m[0])
                self.hints.append("Built on " + match)
        p = re.compile("powered by (.*)(<\/a>|<br|<\/p>|\\n)")
        matches = p.findall(text)
        if matches:
            for m in matches:
                match = tag_re.sub('', m[0])
                self.hints.append("Powered by " + match)
        p = re.compile("based on (.*)(<\/a>|<br|<\/p>|\\n)")
        matches = p.findall(text)
        if matches:
            for m in matches:
                match = tag_re.sub('', m[0])
                self.hints.append("Based on " + match)
        if ".hosted.exlibrisgroup.com" in text:
            self.hints.append("Primo hosted URL")
        if "/dc-mobile/" in text:
            self.hints.append("Contains a digital commons library")
        if "dlibra" in text:
            self.hints.append("Mentions dlibra")
        if "fedora" in text:
            self.hints.append("Mentions fedora")
        if "ori-oai" in text:
            self.hints.append("Mentions ORI-OAI")
        if "diva-portal" in text:
            self.hints.append("Mentions DIVA Portal")
        if "opus" in text:
            self.hints.append("Mentions OPUS")
        if "ds-main" in text or "/xmlui" in text or "dspace" in text:
            self.hints.append("DSpace fragments in HTML")

    def get_hints_from_header(self):
        server = self.get_server_header()
        if "perl" in str(server).lower():
            self.hints.append("Server header mention Perl")
        powered_by = self.get_powered_by()
        if "php" in str(powered_by).lower():
            self.hints.append("Server header mention PHP")

    def get_server_header(self):
        server = self.response.info()["Server"]
        return server

    def get_powered_by(self):
        poweredBy = self.response.info()["X-Powered-By"]
        return poweredBy

    def get_hints(self):
        return self.hints

    def predict_sw(self):
        generator = self.get_generator_from_meta()
        result = ""
        if generator:
            result = self.convert_to_sw_and_version(str(generator))
        if not result:
            result = self.convert_to_sw_and_version(" | ".join(self.get_hints()))
        if result:
            return result
        else:
            return "na", "na"

    def convert_to_sw_and_version(self, sw_text):
        swregex = re.compile(
            "(dspace|eprints|digital commons|fedora|invenio|dlibra|opus|open journal systems|vufind)(\s?[0-9]+\.[0-9]+)?",
            re.IGNORECASE)
        swmatches = swregex.findall(sw_text)
        software = "na"
        version = "na"
        for m in swmatches:
            software = m[0]
            if len(m) > 1:
                version = m[1]
        return software.lower(), version


def run(row):
    current = threading.currentThread().getName()

    homepageurl = row[0]
    country_code = row[1]
    idcore = row[2]
    idopendoar = row[3]
    idroar = row[4]

    try:
        matcher = SwMatcher(idcore, homepageurl)
    except Exception as e:
        logging.error("Can't process this %s", e)
        with open('results/errors-' + current, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([homepageurl, country_code, idcore, idopendoar, idroar, e])
        return ""

    matcher.get_hint_in_html()
    matcher.get_hints_from_header()
    matcher.get_hint_from_text()
    predicted_software, predicted_version = matcher.predict_sw()

    with open('results/results-' + current, 'a') as csvfile:
        writer = csv.writer(csvfile)
        towrite = [homepageurl, country_code, idcore, idopendoar, idroar, predicted_software, predicted_version]
        logging.info(towrite)
        writer.writerow(towrite)
    return ""


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        reader = csv.reader(f)
        repo_list = list(reader)
        if sys.argv[2]:
            start = int(sys.argv[2])
            repo_list = repo_list[start:]
        pool = ThreadPool(20)
        results = pool.map(run, repo_list)
        counter = 0
