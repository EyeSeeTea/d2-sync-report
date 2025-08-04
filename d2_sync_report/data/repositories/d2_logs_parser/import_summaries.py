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
from typing import Iterator, List, Optional


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
    summary_blocks = parse_with_brackets("ImportSummary", line)
    summaries: List[ImportSummary] = []

    for block in summary_blocks:
        # An orthodox parsing would use a proper grammar parser, let's keep it simple and use regexps.
        status_match = re.search(r"status=(\w+)", block)
        description_match = re.search(r"description='(.*?)'", block)
        import_count_match = re.search(r"importCount=\[(.*?)\]", block)
        reference_match = re.search(r"reference='(.*?)'", block)
        conflicts_match = re.search(r"ImportConflict\{(.*?)\}", block, re.DOTALL)

        summary = ImportSummary(
            status=status_match.group(1) if status_match else None,
            description=description_match.group(1) if description_match else None,
            import_count=import_count_match.group(1) if import_count_match else None,
            reference=reference_match.group(1) if reference_match else None,
            conflicts=(conflicts_match.group(1).strip() if conflicts_match else None),
        )

        summaries.append(summary)

    return summaries


def parse_with_brackets(keyword: str, text: str) -> Iterator[str]:
    """
    Parses text for occurrences of a "keyword{...}", supports balanced braces.

    For example, it can parse ImportSummary blocks like:

        ImportSummary{some error} -> "some error"
        ImportConflict{{error 1}, {error2}} -> "{error 1}, {error2}"
    """
    keyword2 = keyword + "{"
    i = 0

    while i < len(text):
        start = text.find(keyword2, i)
        if start == -1:
            break

        brace_level = 1
        j = start + len(keyword2)
        while j < len(text) and brace_level > 0:
            if text[j] == "{":
                brace_level += 1
            elif text[j] == "}":
                brace_level -= 1
            j += 1

        if brace_level == 0:
            content = text[start + len(keyword2) : j - 1]
            yield content
            i = j
        else:
            # Unbalanced braces; abort
            break
