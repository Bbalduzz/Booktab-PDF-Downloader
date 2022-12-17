import requests
from bs4 import BeautifulSoup
import numpy as np
import os, shutil

session = requests.Session()
book_url = input('Enter the url of the book: \n')
isbn = book_url.split('#')[1].split('/')[1]

def get_cookies():
    with open('cookies.txt', 'r') as f: string = f.readline()
    token, booktab_token = string.split(';')
    token_value = token.split('=')[1]
    booktab_token_value = booktab_token.split('=')[1]
    return {'token': token_value, 'booktab_token': booktab_token_value}
cookie = get_cookies()

spine_url = f'https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/spine.xml'
spine = session.get(spine_url, cookies=cookie)
soup = BeautifulSoup(spine.content, 'xml')
title = soup.find('volumetitle').contents[0]
print(title)
units = np.array(soup.find_all('unit'), dtype=object)

def get_toc(data): # un po' storto ma oh, meglio di niente
	soup = BeautifulSoup(data.content, 'xml')
	toc = []
	for u in soup.select('unit'):
		if u.find_all('h1') != []:
			toc.append([1,u.find('title').text, -1])
			for j in u.find_all('h1'):
				if j.get('pageLabel').isnumeric():
					toc.append([2, j.find('title').text, int(j.get('pageLabel'))])
				elif isinstance(toc[-1][2], str):
						del toc[-1]
	return toc

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
	import fitz
	pdffile = fitz.Document()
	for pdf in units_to_merge:
		with open(f'{title}.pdf', 'wb') as handler:
			handler.write(pdf)
		pdffile.insert_pdf(fitz.open(stream=pdf, filetype="pdf"))
	pdffile.set_toc(get_toc(spine))
	pdffile.save(f'{title}.pdf')
	print(f'	╚══ Downloaded: {title}')

for unit in units:
	unit_tilte = get_unit_info()['title']
	unit_btbid = get_unit_info()['btbid']
	unit_url = f"https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/{unit_btbid}/config.xml"
	part_info = session.get(unit_url, cookies=cookie)
	print(part_info.content)
	unit_pdf_name = get_unit_pdf(part_info)
	unit_url_pdf = f"https://web-booktab.zanichelli.it/api/v1/resources_web/{isbn}/{unit_btbid}/{unit_pdf_name}.pdf"
	pdfcontent = session.get(unit_url_pdf, cookies=cookie).content
	units_to_merge.append(pdfcontent)
	print(f'	╠══ {unit_tilte[0]}')

merge_pdfs(units_to_merge)
