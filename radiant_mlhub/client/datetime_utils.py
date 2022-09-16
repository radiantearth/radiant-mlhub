from datetime import datetime
from typing import Tuple


def one_to_one_check(d1: datetime, d2: datetime) -> bool:
    """
    Compare two dates for equality.
    """
    return d1 == d2


def one_to_range_check(d1: datetime, d2: Tuple[datetime, datetime]) -> bool:
    """
    Check for overlap: single datetime with date range.
    """
    (d2_start, d2_end) = d2
    return d1 >= d2_start and d1 <= d2_end


def range_to_range_check(d1: Tuple[datetime, datetime], d2: Tuple[datetime, datetime]) -> bool:
    """
    Check for overlap: two date ranges.
    """
    (d1_start, d1_end) = d1
    (d2_start, d2_end) = d2
    if d1_start >= d2_start and d1_start <= d2_end:
        return True
    if d1_end >= d2_start and d1_start <= d2_end:
        return True
    return False
