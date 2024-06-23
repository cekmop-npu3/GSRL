from aiohttp import ClientSession, FormData
from aiofiles import open
from os import PathLike
from re import search
from typing import overload, TypeVar, Generic

from .Utils import Data, AuthData, UploadData, ProcessData


__all__ = (
    'PdfFormatter',
)


FileName = TypeVar('FileName', bound=str)


class PdfFormatter(Generic[FileName]):
    @overload
    def __init__(self, url: str, filename: FileName = 'filename.pdf') -> None: ...

    @overload
    def __init__(self, path: str, filename: FileName = 'filename.pdf') -> None: ...

    @overload
    def __init__(self, file: bytes, filename: FileName = 'filename.pdf') -> None: ...

    def __init__(self, obj, filename='filename.pdf') -> None:
        self.obj = obj
        self.cookies = dict()
        self.filename = filename

    async def getCred(self) -> AuthData:
        async with ClientSession() as session:
            async with session.get(
                url=Data.token,
                headers=Data.headers
            ) as response:
                self.cookies.update(response.cookies)
                return {
                    'taskId': search(r"ilovepdfConfig\.taskId\s=\s'(.+?)'", text := await response.text()).groups()[0],
                    'token': search(r'"token":"(.+?)"', text).groups()[0]
                }

    async def uploadFile(self, file: bytes, data: AuthData) -> UploadData:
        async with ClientSession() as session:
            async with session.post(
                url=Data.upload,
                data=(
                        (formData := FormData(
                            fields={
                                'task': data.get('taskId'),
                                'name': self.filename,
                                'chunk': '0',
                                'chunks': '1',
                                'preview': '1',
                                'pdfinfo': '0',
                                'pdfforms': '0',
                                'pdfresetforms': '0',
                                'v': 'web.0'
                            }
                        )
                        ).add_field(name='file', content_type='application/pdf', filename=self.filename, value=file),
                        formData
                )[1],
                headers={
                    'authorization': f'Bearer {data.get("token")}'
                } | Data.headers
            ) as response:
                self.cookies.update(response.cookies)
                return await response.json()

    async def processFile(self, fileData: UploadData, data: AuthData) -> ProcessData:
        async with ClientSession() as session:
            async with session.post(
                url=Data.process,
                data=FormData(
                    fields={
                        'files[0][server_filename]': fileData.get('server_filename'),
                        'files[0][filename]': self.filename,
                        'task': data.get('taskId'),
                        'convert_to': 'pdf',
                        'ocr_languages[0]': 'rus',
                        'tool': 'pdfoffice',
                        'output_filename': '{filename}',
                        'packaged_filename': 'ilovepdf_ocr'
                    }
                ),
                headers={
                    'authorization': f'Bearer {data.get("token")}'
                } | Data.headers
            ) as response:
                self.cookies.update(response.cookies)
                return await response.json()

    async def downloadFile(self, data: AuthData) -> bytes:
        async with ClientSession() as session:
            async with session.get(
                url=f'{Data.download}{data.get("taskId")}',
                headers=Data.headers,
                cookies=self.cookies
            ) as response:
                return await response.content.read()

    @staticmethod
    async def loadFile(dest: str | PathLike) -> bytes:
        if dest.startswith('http'):
            async with ClientSession() as session:
                async with session.get(
                    url=dest,
                    headers=Data.headers
                ) as response:
                    return await response.content.read()
        async with open(dest, 'rb') as file:
            return await file.read()

    async def format(self) -> FileName:
        if isinstance(self.obj, str):
            self.obj = await self.loadFile(self.obj)
        data = await self.getCred()
        await self.processFile(await self.uploadFile(self.obj, data), data)
        async with open(self.filename, 'wb') as file:
            await file.write(await self.downloadFile(data))
        return self.filename
