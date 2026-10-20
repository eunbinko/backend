from math import ceil


def calculate_report_price(page_count: int | None) -> int | None:
    if page_count is None or page_count <= 0:
        return None
    return ceil(page_count / 100) * 1000
