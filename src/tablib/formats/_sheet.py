""" Tablib - Shared worksheet import handling.
"""


def import_sheet_rows(dset, rows, read_row, headers=True, skip_lines=0,
                      skip_empty_rows=False):
    """Populate ``dset`` from an iterable of worksheet rows.

    ``rows`` yields the format's raw rows and ``read_row`` converts one raw row
    into a list of cell values. Formats keep ownership of reading cells and
    sheet names; this function only applies the row rules shared by
    spreadsheet formats: skipping leading lines, using the first remaining row
    as headers, and padding short rows to the dataset width.

    Rows before ``skip_lines`` are never passed to ``read_row``.
    ``skip_empty_rows`` preserves the ODS behaviour of dropping rows without
    usable cells instead of importing them as blank rows.
    """
    for i, row in enumerate(rows):
        if i < skip_lines:
            continue
        row_vals = read_row(row)
        if skip_empty_rows and not row_vals:
            continue
        if i == skip_lines and headers:
            dset.headers = row_vals
        else:
            if i > skip_lines and len(row_vals) < dset.width:
                row_vals += [''] * (dset.width - len(row_vals))
            dset.append(row_vals)
