from PyPDF2 import PdfReader
from re import finditer
from functools import reduce
from typing import Iterator

from .Utils import Score

__all__ = (
    'Extract',
)


class Extract(PdfReader):
    def __init__(self, filename: str) -> None:
        super().__init__(filename)

    def __iter__(self) -> Iterator[Score]:
        return iter(
            sorted(
                reduce(
                    lambda x, y: x + y,
                    map(
                        lambda page: list(
                            map(
                                lambda match: match.groupdict(),
                                finditer(
                                    r'\d+\.\s+(\|\s)?(?P<name>\w+\s\w+\s\w+)\s(?P<score>\d+(,\d)?)\s(?P<mark>\d+)',
                                    page.extract_text()
                                )
                            )
                        ),
                        self.pages
                    )
                ),
                key=lambda x: float(x.get('score').replace(',', '.')),
                reverse=True
            )
        )
