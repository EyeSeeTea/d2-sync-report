"""
Example of DHIS2 logs Import Summary

(originally, it's a single-line in logs, but formatted here for clarity):

ImportSummary{
    status=ERROR,
    description='Program is not assigned to this Organisation Unit: WA5iEXjqCnS',
    importCount=[imports=0, updates=0, ignores=1],
    conflicts={},
    dataSetComplete='null',
    reference='ZOkh9BeNXYF',
    href='null'
}
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ImportSummary:
    status: Optional[str] = None
    description: Optional[str] = None
    import_count: Optional[str] = None
    reference: Optional[str] = None
    conflicts: Optional[str] = None

    def format_summary(self) -> str:
        summary = self

        message_parts: List[str] = (
            [summary.description]
            if summary.status != "SUCCESS" and summary.description and summary.description != "null"
            else []
        ) + ([summary.conflicts] if summary.conflicts else [])

        message = " ".join(message_parts)

        return " ".join(
            [
                f'status="{summary.status}"',
                f'object_id="{summary.reference}"',
                f'message="{message}"',
            ]
        )


def parse_import_summaries(line: str) -> List[ImportSummary]:
    summary_blocks: List[str] = re.findall(r"ImportSummary\{(.*?)'\}", line)
    summaries: List[ImportSummary] = []

    for block in summary_blocks:
        # An orthodox parsing would use a proper grammar parser, let's keep it simple and use regexps.
        status_match = re.search(r"status=(\w+)", block)
        description_match = re.search(r"description='(.*?)'", block)
        import_count_match = re.search(r"importCount=\[(.*?)\]", block)
        reference_match = re.search(r"reference='(.*?)'", block)
        conflicts_match = re.search(r"conflicts=\{(.*?)\},", block, re.DOTALL)

        summary = ImportSummary(
            status=status_match.group(1) if status_match else None,
            description=description_match.group(1) if description_match else None,
            import_count=import_count_match.group(1) if import_count_match else None,
            reference=reference_match.group(1) if reference_match else None,
            conflicts=conflicts_match.group(1).strip() if conflicts_match else None,
        )

        summaries.append(summary)

    return summaries
