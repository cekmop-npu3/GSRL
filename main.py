from requests import Session
from time import sleep
from zipfile import ZipFile
from typing import Union
from os import PathLike, mkdir, remove, listdir
from shutil import rmtree
from re import findall
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
            self.stats[path.split('.')[0]] = stats.get_stats()
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
            'OCREngine': 3
        }

    def get_stats(self) -> dict:
        s = []
        for filename in listdir('PDF'):
            file = {'file': (f'PDF/{filename}', open(f'PDF/{filename}', 'rb').read())}
            response = self.session.post(self.url, data=self.data, files=file)
            page = response.json().get('ParsedResults')[0].get('ParsedText')
            results = findall(r'(\w+\s\w+\s\w+)\r\n([\d+,]+)\r\n(\d+)\r\n\d+', page)
            s.extend([(v1, float(v2.replace(',', '.')), int(v3)) for v1, v2, v3 in results])
        rmtree('PDF')
        return dict(
            {key: [val1, val2] for key, val1, val2 in sorted(s, key=lambda x: x[1], reverse=True)}
        )


class Excel(Workbook):
    def __init__(self, stats_rows: dict):
        super().__init__()
        self.stats_rows = stats_rows
        self._create()

    @staticmethod
    def _header(ws: Worksheet):
        ws.append(l := ['Фамилия, имя, отчество учащегося', 'Количество баллов', 'Отметка'])
        for index, text in zip(['A', 'B', 'C', 'D'], l):
            ws.column_dimensions[index].width = len(text) + 5

    def _create(self):
        for index, items in enumerate(self.stats_rows.items()):
            if not bool(index):
                ws: Worksheet = self.active
                ws.title = items[0]
            else:
                ws: Worksheet = self.create_sheet(items[0])
            self._header(ws)
            for item in items[1].items():
                ws.append((item[0], *item[1]))
        if len(self.stats_rows) > 1:
            ws: Worksheet = self.create_sheet('results')
            s1 = {}
            for key in self.stats_rows:
                for key1, value1 in self.stats_rows.get(key).items():
                    s1[key1] = value1 if key1 not in s1 else list(map(sum, zip(s1.get(key1), value1)))
            self._header(ws)
            for item in sorted(s1.items(), key=lambda x: x[1], reverse=True):
                ws.append((item[0], *item[1]))


if __name__ == '__main__':
    pdf = Pdf(['https://gsrl.by/images/2023/protokol_en_2023.pdf', 'https://gsrl.by/images/2023/protokol_matematika_2023.pdf'])
