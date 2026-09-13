import re
from pathlib import Path

from touchstone_testreport.models import TestCaseResult


class ErrorInfo:
    """
    Parses the logs (_verbose.log) file to extract the error diagnostics for failed test cases
    """

    @classmethod
    def parse(cls, in_file: Path, in_out_dir: Path):
        """
        Parses the logs (_verbose.log) file to extract the error diagnostics for failed test cases
        """
        if not (in_file and in_file.exists() and in_file.is_file() and in_file.name.endswith('_verbose.log')):
            raise ValueError(f'Invalid File: {in_file}, MUST be an existing file with suffix "_verbose.log"')

        out_dir: Path = Path(in_out_dir).resolve().absolute()
        out_dir.mkdir(parents=True, exist_ok=True)

        file_content: str
        with in_file.open(mode='r', encoding='utf-8') as file:
            file_content = file.read()

        pattern_str: str = r'^.*?--(.+?)--(.+?)--(.+?)--(\d+).*\r?$'
        test_case_pattern = re.compile(pattern_str, re.MULTILINE)
        status_pattern = re.compile(r'^Status:\s*(.+?)\r?$', re.MULTILINE)

        case_sep: str = '----------------------------------------------------------------------'
        for case_info in file_content.split(case_sep):
            status_match = status_pattern.search(case_info)
            if not (status_match and TestCaseResult.get(status_match.group(1)).is_failure):
                # TODO: Add logging
                continue

            test_match = test_case_pattern.search(case_info)
            if not (test_match and len(test_match.groups()) == 4):
                # TODO: Add logging
                continue

            suite_name, set_name, test_name, test_id = test_match.groups()
            err_file: Path = Path(
                out_dir / f'{suite_name}--{set_name}--{test_name}--{test_id}.txt'
            ).resolve().absolute()

            with err_file.open(mode='w', encoding='utf-8') as efw:
                efw.write(case_info.strip())
