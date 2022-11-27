import requests
from bs4 import BeautifulSoup
import numpy as np
import os, shutil

session = requests.Session()
book_url = input('Enter the url of the book: \n')
isbn = book_url.split('#')[1].split('/')[1]

def get_cookies():
    with open('cookies.txt', 'r') as f: string = f.readline()
    myz_session, myz_token, token, booktab_token = string.split(';')
    myz_token_value = myz_token.split('=')[1]
    myz_session_value = myz_session.split('=')[1]
    token_value = token.split('=')[1]
    booktab_token_value = booktab_token.split('=')[1]
    return {'myz_session': myz_session_value, 'myz_token': myz_token_value, 'token': token_value, 'booktab_token': booktab_token_value}
cookie = get_cookies()

spine_url = f'https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/spine.xml'
spine = session.get(spine_url, cookies=cookie)
soup = BeautifulSoup(spine.content, 'xml')
title = soup.find('volumetitle').contents[0]
print(title)
units = np.array(soup.find_all('unit'), dtype=object)
def get_unit_info() -> dict:
	unit_id = unit.get('id')
	unit_btdib = unit.get('btbid')
	unit_page = unit.get('page')
	unit_title = unit.find('title').contents
	return {
		'id': unit_id,
		'btbid': unit_btdib,
		'page': unit_page,
		'title': unit_title
	}

def get_unit_pdf(part_Info):
	soup = BeautifulSoup(part_Info.content, 'xml')
	part_name = soup.find('content').contents[0]
	part_entries = soup.find_all('entry')
	for pe in part_entries:
		if pe['key'] == f'{part_name}.pdf':
			return pe.contents[0]

units_to_merge = []
def merge_pdfs(units_to_merge):
	from PyPDF2 import PdfMerger, PdfWriter
	pdfs = [f'{pdf}' for pdf in units_to_merge]
	merger = PdfMerger()
	writer = PdfWriter()
	for pdf in pdfs:
		merger.append(pdf)
		#writer.addBookmark(get_unit_info()['title'][0], pdfs.index(pdf) , parent=None)
	merger.write(f'{title}.pdf')
	merger.close()
	print(f'	╚══ Downloaded: {title}')

for unit in units:
	unit_tilte = get_unit_info()['title']
	unit_btbid = get_unit_info()['btbid']
	unit_url = f"https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/{unit_btbid}/config.xml"
	part_info = session.get(unit_url, cookies=cookie)
	unit_pdf_name = get_unit_pdf(part_info)
	if os.path.isdir(f'{title.replace(" ", "_")}'):
		pass
	else:
		os.mkdir(f'{title.replace(" ", "_")}')
	units_to_merge.append(f'{title.replace(" ", "_")}/{unit_tilte[0]}.pdf')
	unit_url_pdf = f"https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/{unit_btbid}/{unit_pdf_name}.pdf"
	r = session.get(unit_url_pdf, cookies=cookie).content
	with open(f'{title.replace(" ", "_")}/{unit_tilte[0]}.pdf', 'wb') as pdf_writer:
		pdf_writer.write(r)
	print(f'	╠══ {unit_tilte[0]} ==> downloaded')

merge_pdfs(units_to_merge)
shutil.rmtree(f'{title.replace(" ", "_")}')
