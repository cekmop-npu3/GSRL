from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from typing import Self

from .Utils import Singleton


__all__ = (
    'Excel',
)


class Excel(Workbook, metaclass=Singleton):
    activeWrite: bool = True

    def __init__(self, filename: str = 'results.xlsx') -> None:
        super().__init__()
        self.filename = filename

    def save(self, filename: str = None) -> None:
        super().save(filename if filename else self.filename)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.save()

    @staticmethod
    def header(ws: Worksheet) -> Worksheet:
        ws.append(l := ['Фамилия, имя, отчество учащегося', 'Количество баллов', 'Отметка'])
        for index, text in zip(['A', 'B', 'C'], l):
            ws.column_dimensions[index].width = len(text) + 5
        return ws

    def create_sheet(self, title: str = None, index: int = None) -> Worksheet:
        if self.activeWrite:
            self.active.title = title
            self.activeWrite = False
            ws: Worksheet = self.active
        else:
            ws: Worksheet = super().create_sheet(title, index)
        return self.header(ws)
