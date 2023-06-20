from requests import Session
from time import sleep
from zipfile import ZipFile
from typing import Union
from os import PathLike, mkdir, remove, listdir
from shutil import rmtree
from re import finditer, search
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


class Pdf:
    def __init__(self, urls: list):
        self.session = Session()
        self.urls = {
            'upload': 'https://filetools16.pdf24.org/client.php?action=upload',
            'split': 'https://filetools16.pdf24.org/client.php?action=splitPdf',
            'status': 'https://filetools16.pdf24.org/client.php?action=getStatus&jobId=',
            'download': 'https://filetools16.pdf24.org/client.php?mode=download&action=downloadJobResult&jobId='
        }
        self.stats = dict()
        for url in urls:
            self.file = {'file': (path := self._get_path(url), open(path, 'rb').read())}
            remove(path)
            self._download(self._get_job_id())
            stats = Stats()
            self.stats[path.split('.')[0]] = stats.get_page()
        excel = Excel(self.stats)
        excel.save('results.xlsx')

    def _get_path(self, url: str) -> Union[str, PathLike]:
        with open(url.split('/')[-1], 'wb') as file:
            file.write(self.session.get(url).content)
        return url.split('/')[-1]

    def _get_job_id(self) -> str:
        file_raw = self.session.post(self.urls.get('upload'), data={'action': 'upload'}, files=self.file).json()
        return self.session.post(self.urls.get('split'), json={'files': file_raw, 'mode': 'pagesPerPdf', 'pagesPerPdf': 1}).json().get('jobId')

    def _download(self, job_id: str):
        status = self.session.get(f"{self.urls.get('status')}{job_id}").json().get('status')
        while status != 'done':
            status = self.session.get(f"{self.urls.get('status')}{job_id}").json().get('status')
            sleep(1)
        with open('files.zip', 'wb') as file:
            file.write(self.session.get(f"{self.urls.get('download')}{job_id}").content)
        mkdir('PDF')
        with ZipFile('files.zip', 'r') as z:
            z.extractall('PDF')
        remove('files.zip')


class Stats:
    def __init__(self):
        self.session = Session()
        self.token = 'K82592607788957'
        self.url = 'https://api.ocr.space/parse/image'
        self.data = {
            'apikey': self.token,
            'language': 'rus',
            'scale': 'true',
        }

    @staticmethod
    def _get_stats(page: str, index: int) -> list:
        start = list(finditer(r'\d{,3}\.\r\n', page))[-1].end()
        end = search('\r\n.*\r\nКоличество\r\nбаллов', page).start()
        l = page[start:end].split('\r\n')
        names = l if not bool(index) else l[1:]

        start = search('Отметка,\r\nполученная на\r\nвступительном\r\nиспытании\r\n', page).end()
        marks = page[start:].split('\r\n')

        return list(zip(names, marks))

    def get_page(self) -> list:
        s = []
        for index, filename in enumerate(listdir('PDF')):
            file = {'file': (f'PDF/{filename}', open(f'PDF/{filename}', 'rb').read())}
            response = self.session.post(self.url, data=self.data, files=file)
            page = response.json().get('ParsedResults')[0].get('ParsedText')
            s.extend(self._get_stats(page, index))
        rmtree('PDF')
        return sorted([(name, float(v.replace(',', '.').replace('ll', '11').replace('З', '3'))) for name, v in s if v], key=lambda x: x[1], reverse=True)


class Excel(Workbook):
    def __init__(self, stats_rows: dict):
        super().__init__()
        self.stats_rows = stats_rows
        self._create()

    def _create(self):
        for index, items in enumerate(self.stats_rows.items()):
            if not bool(index):
                ws: Worksheet = self.active
                ws.title = items[0]
            else:
                ws: Worksheet = self.create_sheet(items[0])
            l = ['Фамилия, имя, отчество учащегося', 'Отметка']
            ws.append(l)
            for index, text in zip(['A', 'B', 'C'], l):
                ws.column_dimensions[index].width = len(text) + 5
            for student in items[1]:
                ws.append(student)


if __name__ == '__main__':
    pdf = Pdf(['https://gsrl.by/images/2023/protokol_matematika_2023.pdf'])
