import argparse
import os
from pathlib import Path
from typing import Any

from touchstone_testreport._error_info import ErrorInfo
from touchstone_testreport._test_template import TouchstoneTestTemplate
from touchstone_testreport.models import TestCaseResult, TestExecutionModel, TestSuiteModel


def main(in_test_output_dir: str):
    test_output_dir: Path = Path(in_test_output_dir).resolve().absolute()

    if not (test_output_dir.exists() and test_output_dir.is_dir()):
        # TODO: Add logging
        return

    suites: dict[str, TestSuiteModel] = {}
    exec_info: TestExecutionModel
    template: TouchstoneTestTemplate = TouchstoneTestTemplate(
        in_template_dir=Path(__file__).parent / 'templates',
        in_out_dir=test_output_dir / 'reports'
    )

    for file_path in test_output_dir.glob('*_verbose.log'):
        file_path: Path = Path(file_path).resolve().absolute()

        # 1. Extract the error diagnostics from '_verbose.log' files for each test suites
        try:
            exec_info = TestExecutionModel.from_file(file_path)
            ErrorInfo.parse(file_path, test_output_dir / 'failures')
        except ValueError as error:
            # print(error)
            continue

        # 2. Parse '_summary.csv' files for each test suites
        test_suite: TestSuiteModel
        summary_file_path: Path = file_path.parent / (
            file_path.name
            .replace('__verbose.log', '__summary.csv')
            .replace('_verbose.log', '_summary.csv')
        )
        try:
            test_suite = TestSuiteModel.from_csv(summary_file_path)
            suites[test_suite.name] = test_suite
        except ValueError as error:
            # print(f'{str(file_path)} failed validation')
            continue

        # 3. Generate Test reports
        count_excluded: int = test_suite.test_results[TestCaseResult.EXCLUDED] + test_suite.test_results[
            TestCaseResult.SUSPENDED]
        rate_excluded: float = (count_excluded / test_suite.total_cases_count) * 100
        count_success: int = test_suite.test_results[TestCaseResult.SUCCEED] + test_suite.test_results[
            TestCaseResult.RESULT_IGNORED]
        rate_success: float = (count_success / test_suite.total_cases_count) * 100

        template.to_html(
            in_template_name='report_template.html',
            in_out_filename=f'{test_suite.name}.html',
            suite_name=test_suite.name,
            touchstone_v=exec_info.ts_ver,
            execution_date=exec_info.datetime,
            total_cases=test_suite.total_cases_count,
            success_cases=str(count_success),
            success_rate=f'{rate_success:.2f}',
            excluded_cases=str(count_excluded),
            skipped_rate=f'{rate_excluded:.2f}',
            pipeline_overhead='',
        )

    artifact_suites: list = list()
    for name, suite in suites.items():
        artifact: dict[str, Any] = {
            'name': name.upper(),
        }
        artifact['artifacts'] = list()
        for file_path in test_output_dir.glob(f'*{suite.name}*'):
            file_path: Path = file_path.resolve().absolute()
            label: str = file_path.name.replace(name, '').replace('_', ' ').replace(file_path.suffix, '').strip()
            artifact['artifacts'].append(
                {
                    'label'   : f'{label.capitalize()} ({file_path.suffix.upper()})',
                    'filename': file_path.name,
                    'href'    : file_path.as_posix(),
                }
            )
        artifact_suites.append(artifact)

    template.to_html(
        in_template_name='artifact_explorer.html',
        in_out_filename='artifact_explorer.html',
        exec_time=exec_info.datetime,
        ts_ver=exec_info.ts_ver,
        pipeline_url=os.getenv('PIPELINE_URL', ''),
        artifact_suites=artifact_suites
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extracts Touchstone tests diagnostics and generates HTML reports."
    )

    parser.add_argument(
        '--test-output-dir',
        dest='test_output_dir',
        help="Path to the Touchstone tests execution output directory.",
    )

    args = parser.parse_args()

    try:
        main(args.test_output_dir)
    except Exception as error:
        print(error)
