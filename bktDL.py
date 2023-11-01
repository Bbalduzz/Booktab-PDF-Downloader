import requests
from bs4 import BeautifulSoup
import fitz

BASE_URL = "https://web-booktab.zanichelli.it/api/v1/resources_web"
class BookTab:
    def __init__(self, isbn):
        self.isbn = isbn
        self.session = requests.Session()
        self.cookies = self._load_cookies('cookies.txt')
        self._update_session_cookies()
        self.spine_data = self._fetch_spine_data()

    @staticmethod
    def _load_cookies(filepath):
        with open(filepath, 'r') as f:
            return dict(item.split('=') for item in f.readline().split('; '))

    def _update_session_cookies(self):
        self.session.cookies.update(self.cookies)

    def _fetch_spine_data(self):
        spine_url = f"{BASE_URL}/{self.isbn}/spine.xml"
        response = self.session.get(spine_url)
        return BeautifulSoup(response.content, 'xml')

    def get_toc(self):
        toc = []
        for u in self.spine_data.select('unit'):
            if u.find_all('h1') != []:
                toc.append([1,u.find('title').text, -1])
                for j in u.find_all('h1'):
                    if j.get('pageLabel').isnumeric():
                        toc.append([2, j.find('title').text, int(j.get('pageLabel'))])
                    elif isinstance(toc[-1][2], str):
                            del toc[-1]
        return toc

    def get_unit_info(self, unit):
        return {
            'id': unit.get('id'),
            'btbid': unit.get('btbid'),
            'page': unit.get('page'),
            'title': unit.find('title').contents
        }

    def _fetch_pdf_url(self, unit_btbid):
        unit_config_url = f"{BASE_URL}/{self.isbn}/{unit_btbid}/config.xml"
        response = self.session.get(unit_config_url)
        data = BeautifulSoup(response.content, 'xml')
        content_name = data.find('content').contents[0]
        for entry in data.find_all('entry'):
            if entry['key'] == f"{content_name}.pdf":
                return entry.contents[0]
        return None

    def download_unit_pdf(self, unit_btbid):
        pdf_name = self._fetch_pdf_url(unit_btbid)
        pdf_url = f"{BASE_URL}/{self.isbn}/{unit_btbid}/{pdf_name}.pdf"
        return self.session.get(pdf_url).content

    def download_book(self):
        title = self.spine_data.find('volumetitle').contents[0]
        units_pdfs = []
        for unit in self.spine_data.find_all('unit'):
            unit_info = self.get_unit_info(unit)
            pdf_data = self.download_unit_pdf(unit_info['btbid'])
            units_pdfs.append(pdf_data)
            print(f"Downloaded unit: {unit_info['title'][0]}")
        self._merge_and_save_pdfs(title, units_pdfs)

    def _merge_and_save_pdfs(self, title, units_pdfs):
        with fitz.Document() as pdf_document:
            for pdf_data in units_pdfs:
                pdf_document.insert_pdf(fitz.open(stream=pdf_data, filetype="pdf"))
            pdf_document.set_toc(self.get_toc())
            pdf_document.save(f"{title}.pdf")
        print(f"Downloaded: {title}")


def main():
    book_url = input('Enter the url of the book: \n')
    isbn = book_url.split('#')[1].split('/')[1]
    scraper = BookTab(isbn)
    scraper.download_book()


if __name__ == "__main__":
    main()
