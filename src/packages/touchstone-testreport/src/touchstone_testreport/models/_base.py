from enum import Enum, auto

from pydantic import BaseModel, ConfigDict
# For Python backward compatibility (3.11 and below)
from typing_extensions import Self


class TestCaseResult(Enum):
    """
    Consolidated test case execution results for ODBC and JDBC Touchstone
    TODO: Add missing JTS result
    """
    CLEANUP_FAILED = auto()
    CRASHED = auto()
    EXCLUDED = auto()
    FAILED = auto()
    FAILED_STARTUP = auto()
    NOT_FOUND = auto()
    RESULT_IGNORED = auto()
    SUCCEED = auto()
    SUSPENDED = auto()
    UNKNOWN = auto()

    @property
    def is_failure(self) -> bool:
        """
        Denotes if the given test case execution result is a failure
        """
        return self in [
            TestCaseResult.CLEANUP_FAILED,
            TestCaseResult.CRASHED,
            TestCaseResult.FAILED,
            TestCaseResult.FAILED_STARTUP
        ]

    @property
    def is_success(self):
        return self in [
            TestCaseResult.RESULT_IGNORED,
            TestCaseResult.SUCCEED
        ]

    @classmethod
    def get(cls, in_value: str) -> Self:
        """
        Uniformal getter

        :param in_value: The requested test case result value to validate and convert
        """
        return cls(cls._member_map_.get(str(in_value).strip().upper(), cls.UNKNOWN))

    @classmethod
    def to_normalized(cls, in_results: dict[Self, int]) -> dict[str, int]:
        normalized: dict[str, int] = {
            TestCaseResult.FAILED.name  : 0,
            TestCaseResult.SUCCEED.name : 0,
            TestCaseResult.EXCLUDED.name: 0,
            'OTHER'                     : 0
        }
        for result, count in in_results.items():
            if result.is_failure:
                normalized[TestCaseResult.FAILED.name] += count
            elif result.is_success:
                normalized[TestCaseResult.SUCCEED.name] += count
            elif result == TestCaseResult.EXCLUDED:
                normalized[TestCaseResult.EXCLUDED.name] += count
            else:
                normalized['OTHER'] += count
        return normalized


class BaseTestEntityModel(BaseModel):
    """
    Represents the base data model for Test entities/primitives
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        cache_strings=True,
        extra='ignore',
        frozen=True,
        str_strip_whitespace=True,
    )
