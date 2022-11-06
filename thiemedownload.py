import os
import sys
import requests
import urllib.request as urlrequest
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileMerger

# Constants
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36'}
# BUG: urllib3 http muss statt https genutzt werden
proxies = {'https': 'http://proxy.charite.de:8080',
           'http': 'http://proxy.charite.de:8080'}
URL = 'https://eref.thieme.de/ebooks/'
InputFormater = '\n\n\t ==>  '
DefaultPath = r'C:\Users\pedRam\Documents\Medizin'
UseDefault = True


# Die Buch ID ist die eindeutige Indentifikationszeichenkette im Link zum E-Book
bookID = input('\nGib nun bitte die ID der Eref-Seite ein, während du mit deinem VPN-Dienst verbunden bist. \n'
               + f'Eref Seiten haben das folgende Format: https://eref.thieme.de/ebooks/<ErefID>{InputFormater}')


# If there is no such folder, the script will create one automatically
if UseDefault:
    folderLocation = input(
        f'\nGib nun einen Namen für den gewünschten Ablage-Ordner an.{InputFormater}')
    folderLocation = os.path.join(DefaultPath, folderLocation)
else:
    folderLocation = input(
        f'\nGib nun einen Pfad für den gewünschten Ablage-Ordner an.{InputFormater}')
if not os.path.exists(folderLocation):
    os.mkdir(folderLocation)


answer = ''
while answer != 'J' and answer != 'N' and answer != 'A':
    answer = input(
        '\nSollen die PDFs zu einer PDF vereint werden? (J)a / (N)ein / (A)brechen' + InputFormater)


merge = False
if answer.lower() == 'j':
    merge = True
elif answer.lower() == 'n':
    merge = False
else:
    sys.exit('Prozess abgebrochen.')

session = requests.Session()
session.proxies.update(proxies)
session.headers.update(headers)

print('\n')
response = session.get(f'{URL}pdf-toc/{bookID}')

print('Parsing URL text...')
soup = BeautifulSoup(response.text, "html.parser")
print('Parsing done.\n')

links = soup.select("a[class='tocPdfContainer']")
print(f'Starte Download von {len(links)} PDF(s).\n')
for i in range(len(links)):
    downloadLink = urljoin(URL, links[i]['data-pdf-link'])

    filename = ''
    if merge:
        filename = os.path.join(folderLocation, f'merge{i}.pdf')
    else:
        filename = os.path.join(
            folderLocation, links[i]['data-pdf-link'].split('/')[-1])

    print(f'Downloadpfad: {filename}')
    print(f'\t Versuche herunterzuladen: {downloadLink} ...')

    with open(filename, 'wb') as f:
        r = session.get(downloadLink)
        status = ''
        if r.status_code == 200:
            status = 'Download erfolgreich.'
        else:
            status = 'Download fehlgeschlagen.'
        print(f'\t{status}\n')
        f.write(r.content)

print('Download abgeschlossen.\n')

if (merge):
    merger = PdfFileMerger()

    print(f'Starte Vereinigung von {len(links)} PDF(s).\n')
    for i in range(len(links)):
        merger.append(os.path.join(folderLocation, f'merge{i}.pdf'))
        if i != 0:
            print(f'PDF {i} und PDF {i+1} vereinigt.')

    print('\nWarte auf den letzten Schritt der Vereinigung...')
    with open(os.path.join(folderLocation, 'result.pdf'), 'wb') as f:
        merger.write(f)
    merger.close()
    print('Vereinigung abgeschlossen.')
