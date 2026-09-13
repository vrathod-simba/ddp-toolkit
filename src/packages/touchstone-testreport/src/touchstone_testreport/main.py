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
        normalized = TestCaseResult.to_normalized(test_suite.test_results)
        cases: list[dict[str, Any]] = []
        test_set_results: list[dict[str, Any]] = []
        for ident, test_set in test_suite.test_sets.items():
            test_set_result: dict[str, Any] = {'name': test_set.name.upper()}
            test_set_result.update(TestCaseResult.to_normalized(test_set.test_results))
            test_set_results.append(test_set_result)

            for case in test_set.test_cases:
                case: dict[str, Any] = {
                    'id'         : case.id,
                    'test_set'   : test_set.name.upper(),
                    'name'       : case.internal_id,
                    'result'     : case.result.name,
                    'description': case.description,
                    'elapse_ms'  : case.elapsed_time,
                    'failure_url': f'../failures/{test_suite.name}--{test_set.name.upper()}--{case.internal_id.upper()}--'
                                   f'{case.id}.txt'
                }
                cases.append(case)

        template.to_html(
            in_template_name='testsuite.html',
            in_out_filename=f'{test_suite.name}.html',
            suite_name=test_suite.name.upper(),
            exec_time=exec_info.datetime,
            ts_ver=exec_info.ts_ver,
            pipeline_url=os.getenv('PIPELINE_URL', ''),
            total_cases=test_suite.total_cases_count,
            succeed_count=normalized[TestCaseResult.SUCCEED.name],
            failed_count=normalized[TestCaseResult.FAILED.name],
            excluded_count=normalized[TestCaseResult.EXCLUDED.name],
            testset_breakdown=test_set_results,
            test_cases=cases
        )

    artifact_suites: list = list()
    for name, suite in suites.items():
        artifact: dict[str, Any] = {
            'name'         : name.upper(),
            'url'          : f'{suite.name}.html',
            'result_counts': TestCaseResult.to_normalized(suite.test_results),
            'artifacts'    : list()
        }
        for file_path in test_output_dir.glob(f'*{suite.name}*'):
            file_path: Path = file_path.resolve().absolute()
            label: str = file_path.name.replace(name, '').replace('_', ' ').replace(file_path.suffix, '').strip()
            artifact['artifacts'].append(
                {
                    'label'   : f'{label.capitalize()} ({file_path.suffix.upper()})',
                    'filename': file_path.name,
                    'href'    : f'../{file_path.name}',
                }
            )
        artifact_suites.append(artifact)

    template.to_html(
        in_template_name='home.html',
        in_out_filename='home.html',
        exec_time=exec_info.datetime,
        ts_ver=exec_info.ts_ver,
        pipeline_url=os.getenv('BUILD_URL', ''),
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
        test_output_dir: str = r'C:\Users\vipul.rathod\Downloads\TS-Logs\log\test_output'
        # test_output_dir: str = r'C:\Users\vipul.rathod\Downloads\Touchstone--w2016--vs2022--64\Logs'
        main(args.test_output_dir or test_output_dir)
        # main(args.test_output_dir)
    except Exception as error:
        print(error)
