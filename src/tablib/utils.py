__lazy_modules__ = {"io"}

from io import BytesIO, StringIO

# Sentinel distinguishing "no batch keyword was passed" from "batch_size=None".
_MISSING = object()

# Keywords that may be used to request a batched import.  ``batch_size`` is
# the canonical name; the others are accepted so that callers coming from
# other tabular libraries have an obvious spelling.
BATCH_SIZE_KEYWORDS = (
    'batch_size',
    'batchsize',
    'batch_rows',
    'row_batch',
    'row_batch_size',
    'rows_per_batch',
    'rows_per_chunk',
    'chunk_size',
    'chunk_rows',
    'chunksize',
)


def pop_batch_size(kwargs, default=None):
    """Remove and return a batch size keyword from *kwargs*, if present.

    All known spellings are removed so that they are never forwarded to a
    format or to the underlying CSV reader.  An explicit *default* (a value
    bound to a named parameter) wins over the keyword aliases; ``None`` means
    "not given".
    """
    alias = _MISSING
    for keyword in BATCH_SIZE_KEYWORDS:
        if keyword in kwargs:
            value = kwargs.pop(keyword)
            if alias is _MISSING:
                alias = value
    if default is not None:
        return default
    if alias is _MISSING:
        return None
    return alias


def validate_batch_size(batch_size):
    """Return *batch_size* if it is a positive integer, raise otherwise."""
    if isinstance(batch_size, bool) or not isinstance(batch_size, int):
        raise TypeError("batch_size must be an integer.")
    if batch_size < 1:
        raise ValueError("batch_size must be a positive integer.")
    return batch_size


def normalize_input(stream):
    """
    Accept either a str/bytes stream or a file-like object and always return a
    file-like object.
    """
    if isinstance(stream, str):
        return StringIO(stream, newline='')
    elif isinstance(stream, bytes):
        return BytesIO(stream)
    return stream
