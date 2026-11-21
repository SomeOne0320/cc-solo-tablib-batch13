""" Tablib - *SV Support.
"""

__lazy_modules__ = {"csv", "io", "tablib.exceptions", "tablib.utils"}

import csv
from io import StringIO

from ..exceptions import InvalidDimensions
from ..utils import normalize_input, pop_batch_size, validate_batch_size


class CSVFormat:
    title = 'csv'
    extensions = ('csv',)

    DEFAULT_DELIMITER = ','

    @classmethod
    def export_stream_set(cls, dataset, **kwargs):
        """Returns CSV representation of Dataset as file-like."""
        stream = StringIO()

        kwargs.setdefault('delimiter', cls.DEFAULT_DELIMITER)

        _csv = csv.writer(stream, **kwargs)

        for row in dataset._package(dicts=False):
            _csv.writerow(row)

        stream.seek(0)
        return stream

    @classmethod
    def export_set(cls, dataset, **kwargs):
        """Returns CSV representation of Dataset."""
        stream = cls.export_stream_set(dataset, **kwargs)
        return stream.getvalue()

    @classmethod
    def import_set(cls, dset, in_stream, headers=True, skip_lines=0, batch_size=None, **kwargs):
        """Returns dataset from CSV stream.

        If a batch size is passed (either as *batch_size* or through one of the
        aliases accepted by :func:`tablib.utils.pop_batch_size`), an iterator
        over :class:`tablib.Dataset` instances is returned and *dset* is left
        untouched.  Otherwise *dset* is populated as before.
        """
        batch_size = pop_batch_size(kwargs, default=batch_size)
        if batch_size is not None:
            return cls.import_batches(
                in_stream,
                headers=headers,
                skip_lines=skip_lines,
                batch_size=batch_size,
                **kwargs,
            )

        dset.wipe()

        kwargs.setdefault('delimiter', cls.DEFAULT_DELIMITER)

        rows = csv.reader(in_stream, **kwargs)
        for i, row in enumerate(rows):
            if i < skip_lines:
                continue
            if i == skip_lines and headers:
                dset.headers = row
            elif row:
                if i > 0 and len(row) < dset.width:
                    row += [''] * (dset.width - len(row))
                dset.append(row)

    @classmethod
    def import_batches(cls, in_stream, headers=True, skip_lines=0, batch_size=None, **kwargs):
        """Return an iterator yielding successive batches read from *in_stream*.

        Every batch is a :class:`tablib.Dataset` containing at most
        *batch_size* rows; the last one may contain fewer. No empty batch is
        ever yielded. Reading is lazy, so producing the first batch only
        consumes the rows it contains (plus the header, if any) and never
        reads the rest of the stream.

        ``skip_lines`` is honoured exactly once, before the header (if any) is
        read.  The header is read once as well, and every batch receives its
        own copy, so modifying one batch's headers leaves the next batches
        untouched.

        The stream is never closed here: a stream opened by the caller stays
        the caller's responsibility.
        """
        batch_size = pop_batch_size(kwargs, default=batch_size)
        batch_size = validate_batch_size(batch_size)
        kwargs.setdefault('delimiter', cls.DEFAULT_DELIMITER)

        # Accept a plain string as well, like the other import entries.
        in_stream = normalize_input(in_stream)
        # Creating a reader does not consume anything from the stream.
        reader = csv.reader(in_stream, **kwargs)
        return cls._iter_batches(reader, headers, skip_lines, batch_size)

    @classmethod
    def _iter_batches(cls, reader, headers, skip_lines, batch_size):
        """Lazily consume *reader* and yield batches of rows.

        ``headers`` and ``skip_lines`` are handled here, once, when iteration
        starts.
        """
        from ..core import Dataset  # Avoid a circular import at module load time.

        # Explanation lines are skipped exactly once, before the header row.
        for _ in range(skip_lines):
            try:
                next(reader)
            except StopIteration:
                return

        header = None
        width = None
        if headers:
            # Column names are read exactly once, from the row following the
            # skipped lines, mirroring the non-batched importer.  A blank
            # header row yields a dataset without headers.
            try:
                row = next(reader)
            except StopIteration:
                return
            if row:
                header = row
                width = len(header)

        batch = []

        def make_batch():
            # Dataset copies the header list, so batches never share headers.
            dset = Dataset(headers=header)
            dset.extend(batch)
            return dset

        for row in reader:
            if not row:
                # Blank lines are not records and never form a batch.
                continue
            if width is None:
                # Without headers, the first record determines the row width,
                # just like the non-batched importer.
                width = len(row)
            elif len(row) < width:
                row = row + [''] * (width - len(row))
            elif len(row) > width:
                # Report over-wide records the same way Dataset.append() does
                # for the non-batched importer, even when they would open a
                # new batch.
                raise InvalidDimensions
            batch.append(row)
            if len(batch) == batch_size:
                yield make_batch()
                batch = []

        if batch:
            yield make_batch()

    @classmethod
    def detect(cls, stream, delimiter=None):
        """Returns True if given stream is valid CSV."""
        try:
            csv.Sniffer().sniff(stream.read(2048), delimiters=delimiter or cls.DEFAULT_DELIMITER)
            return True
        except Exception:
            return False
