from typing import TypedDict
from .Meta import ReadOnly


__all__ = (
    'Data',
    'AuthData',
    'UploadData',
    'ProcessData',
    'Score',
    'Task'
)


class Data(ReadOnly):
    token = 'https://www.ilovepdf.com/ru/ocr-pdf'
    upload = 'https://api42o.ilovepdf.com/v1/upload'
    process = 'https://api42o.ilovepdf.com/v1/process'
    download = 'https://api42o.ilovepdf.com/v1/download/'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }


class AuthData(TypedDict):
    taskId: str
    token: str


class UploadData(TypedDict):
    scanned: bool
    server_filename: str


class ProcessData(TypedDict):
    download_filename: str
    filesize: int
    output_extensions: list[str]
    output_filenumber: int
    output_filesize: int
    status: str
    timer: float


class Score(TypedDict):
    name: str
    score: str
    mark: str


class Task(TypedDict):
    file: str | bytes
    filename: str
