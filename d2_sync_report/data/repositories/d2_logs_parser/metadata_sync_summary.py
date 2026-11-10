"""
Example of DHIS2 logs Metadata Sync Summary, logged after the import of each metadata version.

(originally, it's a single-line in logs, but formatted here for clarity):

MetadataSyncSummary{
    importReport=ImportReport{
        stats=Stats{created=0, updated=0, deleted=0, ignored=21},
        typeReports=[TypeReport{
            klass=class org.hisp.dhis.user.User,
            stats=Stats{created=0, updated=0, deleted=0, ignored=3},
            objectReports=[ObjectReport{
                klass=class org.hisp.dhis.user.User,
                index=1,
                uid=xE7jOejl9FI,
                errorReports=[PreheatErrorReport{
                    message=Invalid reference [OI69n5Ig2Tw] (FileResource) on object [...],
                    errorCode=E5002,
                    mainKlass=class org.hisp.dhis.user.User,
                    errorKlass=null,
                    value=null
                }]
            }]
        }]
    },
    importSummary=null,
    metadataVersion=MetadataVersion{importDate=null, type=ATOMIC, name='Version_19', [...]}
}

The same error reports have a different outcome depending on the version type: an ATOMIC
version is not imported (status ERROR, the sync is aborted), while a BEST_EFFORT version is
imported without the offending objects or fields (status WARNING, the sync goes on). So error
reports are errors for ATOMIC versions, and warnings for BEST_EFFORT versions.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from d2_sync_report.data.repositories.d2_logs_parser.import_summaries import parse_with_brackets


@dataclass
class MetadataErrorReport:
    message: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class MetadataSyncSummary:
    version: Optional[str] = None
    version_type: Optional[str] = None
    error_reports: List[MetadataErrorReport] = field(default_factory=list)

    def format_errors(self) -> List[str]:
        return [] if self.is_best_effort() else self._format_error_reports()

    def format_warnings(self) -> List[str]:
        return self._format_error_reports() if self.is_best_effort() else []

    def is_best_effort(self) -> bool:
        return self.version_type == "BEST_EFFORT"

    def _format_error_reports(self) -> List[str]:
        return [
            " ".join(
                [
                    f'version="{self.version}"',
                    f'error_code="{error_report.error_code}"',
                    f'message="{error_report.message}"',
                ]
            )
            for error_report in self.error_reports
        ]


def parse_metadata_sync_summary(line: str) -> MetadataSyncSummary:
    version_match = re.search(r"metadataVersion=MetadataVersion\{.*?name='(.*?)'", line)
    version_type_match = re.search(r"metadataVersion=MetadataVersion\{.*?type=(\w+)", line)

    error_reports: List[MetadataErrorReport] = []

    # Matches any error report class (ErrorReport, PreheatErrorReport, ...)
    for block in parse_with_brackets("ErrorReport", line):
        message_match = re.search(r"message=(.*?), errorCode=", block)
        error_code_match = re.search(r"errorCode=(\w+)", block)

        error_report = MetadataErrorReport(
            message=message_match.group(1) if message_match else None,
            error_code=error_code_match.group(1) if error_code_match else None,
        )

        error_reports.append(error_report)

    return MetadataSyncSummary(
        version=version_match.group(1) if version_match else None,
        version_type=version_type_match.group(1) if version_type_match else None,
        error_reports=error_reports,
    )
