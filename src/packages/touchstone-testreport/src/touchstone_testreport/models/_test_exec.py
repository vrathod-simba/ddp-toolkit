import re
from pathlib import Path
from typing import Self

from pydantic.fields import Field

from touchstone_testreport.models._base import BaseTestEntityModel


class TestExecutionModel(BaseTestEntityModel):
    """
    Parses the logs (_verbose.log) file to extract the test execution details
    """
    datetime: str = Field(
        default='Unknown',
        description='Date and time of test execution'
    )

    ts_ver: str = Field(
        default='Unknown',
        description='Touchstone Version'
    )

    ts_pid: int = Field(
        default=-1,
        description='Touchstone Process ID for a given test suite execution',
        gt=0
    )

    @classmethod
    def from_file(cls, in_file: Path) -> Self:
        """
        Parses the logs (_verbose.log) file to extract Touchstone and test artifacts details
        """
        if not (in_file and in_file.exists() and in_file.is_file() and in_file.name.endswith('_verbose.log')):
            raise ValueError(f'Invalid File: {in_file}, MUST be an existing file with suffix "_verbose.log"')

        file_content: str
        with in_file.open(mode='r', encoding='utf-8') as file:
            file_content = file.read().strip()

        return cls.from_str(file_content)

    @classmethod
    def from_str(cls, in_content: str) -> Self:
        """
        Parses the logs (_verbose.log) file to extract Touchstone and test artifacts details
        """
        pat_datetime = re.compile(r'Simba Test Verbose Log Started on (.+?)\r?$')
        pat_ts_ver = re.compile(r'Version:\s+(.+)\r?$')
        pat_ts_pid = re.compile(r'touchstone.getpid=(\d+)\r?$')

        datetime: str = None
        ts_ver: str = None
        ts_pid: int = -1
        for line in in_content.splitlines():
            if (match := pat_datetime.match(line)) and match.groups() and len(match.groups()) == 1:
                datetime = match.group(1)
                continue
            elif (match := pat_ts_ver.match(line)) and match.groups() and len(match.groups()) == 1:
                ts_ver = match.group(1)
                continue
            elif (match := pat_ts_pid.match(line)) and match.groups() and len(match.groups()) == 1:
                ts_pid = int(match.group(1))
                continue
            elif 'touchstone: starting to run tests' in line:
                # Extraction completed
                break

        return cls(datetime=datetime, ts_ver=ts_ver, ts_pid=ts_pid)
