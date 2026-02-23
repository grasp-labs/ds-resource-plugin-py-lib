# Dataset Contract

This document defines the abstract methods available on every dataset
resource, their intent, and the rules that all provider implementations
must follow. These rules are universal -- no exceptions.

---

## Principles

1. **One method, one intent.** Each method does exactly one thing.
   It does not change behaviour based on settings or input state.

2. **Atomic.** Every write method executes as a single atomic
   transaction against the backend. All rows in `self.input` either
   succeed together or fail together. There is no partial success.
   Batching is the caller's responsibility -- the provider never
   splits work internally.

3. **Idempotent where possible.** A method that can be safely retried
   without side effects must be implemented that way. Methods that
   are not naturally idempotent must document this.

4. **Settings configure, they do not change intent.** Settings control
   provider-specific details (connection parameters, formatting,
   performance tuning). They never alter what a method does -- only
   how it does it.

5. **Fail loudly.** If a method cannot fulfil its intent, it raises
   an appropriate error. It never returns partial results or silently
   skips work.

6. **Connection is not yours.** The dataset never calls
   `self.linked_service.connect()`. It only accesses the already-
   established connection via `self.linked_service.connection`. The
   caller is responsible for connecting before using the dataset and
   closing when done (see `LINKED_SERVICE_CONTRACT.md`).

---

## Input Handling

Methods that use `self.input` (`create`, `update`, `upsert`, `delete`)
must follow these rules:

### Empty input

If `self.input` is `None` or an empty DataFrame, the method must
**return immediately without error**. An empty input means "there is
nothing to do" -- this is not an error condition. The caller (e.g. the
batch writer) may legitimately call a method with no rows.

### Backend capacity limits

Some backends limit how many rows can be processed in a single atomic
transaction (e.g. Azure Table allows max 100 entities per batch, some
APIs accept only 1 entity per request). The provider must **not** work
around this by splitting the operation internally -- that breaks the
atomic guarantee.

Instead, the provider must declare its capacity limit so the caller
can batch accordingly:

| Capacity | Provider behaviour                                    |
| -------- | ----------------------------------------------------- |
| No limit | Accept any size `self.input`.                         |
| Limited  | Accept up to N rows. Raise if `self.input` exceeds N. |

The caller is responsible for chunking `self.input` to fit within
the provider's capacity. The provider must document its limit (or
expose it via a property/setting) so the caller can respect it.

> **Example:** Azure Table supports max 100 entities per batch
> transaction. The provider accepts up to 100 rows in `self.input`
> and raises if more are provided. The caller sets `batch_size: 100`
> to stay within the limit.

### Input must not be mutated

Methods must never modify `self.input`. The caller may reuse the
same DataFrame across multiple operations or for logging. If the
provider needs to transform the data (e.g. rename columns, cast
types), it must work on a copy.

---

## Return Values & Output

Each method has a defined return type. Success is also indicated by the
absence of an exception.

### Return types

All methods return `None`. Data is always in `self.output`.
Operation details (success, timing, row counts, schema, errors) are in `self.operation`.

| Method     | Returns | Description                                  |
| ---------- | ------- | -------------------------------------------- |
| `read()`   | `None`  | Data goes to `self.output`.                  |
| `create()` | `None`  | Data goes to `self.output`.                  |
| `update()` | `None`  | Data goes to `self.output`.                  |
| `upsert()` | `None`  | Data goes to `self.output`.                  |
| `delete()` | `None`  | Data goes to `self.output`.                  |
| `purge()`  | `None`  | Success means the target is empty.           |
| `list()`   | `None`  | Data goes to `self.output`.                  |
| `rename()` | `None`  | Success means the resource was renamed.      |
| `close()`  | `None`  | Success means the connection is closed.      |

### `self.output` after each method

Every method that produces data must populate `self.output`:

- **Write methods** (`create`, `update`, `upsert`, `delete`): if the
  backend returns row-level data (e.g. PostgreSQL `RETURNING *`, API
  response bodies), use the backend response. If it does not (e.g. S3,
  SFTP), set `self.output = self.input.copy()`.
- **`read()`**: the result set from the source (full or incremental,
  depending on `self.checkpoint`).
- **`list()`**: a DataFrame of discovered resources with available
  metadata (name, size, modified date, type, etc.).

This guarantees that `self.output` is always populated after a
successful data operation, regardless of provider. The caller can
rely on it for logging, auditing, or downstream processing.

| Method     | `self.output` after success                           |
| ---------- | ----------------------------------------------------- |
| `read()`   | Result set from the source (full or incremental).     |
| `create()` | The inserted rows (backend response or input copy).   |
| `update()` | The updated rows (backend response or input copy).    |
| `upsert()` | The upserted rows (backend response or input copy).   |
| `delete()` | The deleted rows (backend response or input copy).    |
| `purge()`  | Not populated. No row-level data to return.           |
| `list()`   | DataFrame of resources with metadata.                 |
| `rename()` | Not populated.                                        |
| `close()`  | Not populated.                                        |

### `self.checkpoint`

An opaque `dict[str, Any]` for incremental/delta load support. The
pipeline orchestrator manages persistence; the provider manages content.

- **Empty dict** (`{}`) signals a full load.
- **Populated dict** signals an incremental load -- the provider reads
  only data that is new or changed since the checkpoint.
- The provider updates `self.checkpoint` after a successful operation
  so the next run can continue from where it left off.
- The base class does not read, write, or persist the checkpoint.
  It only defines the field.

| Responsibility      | Actor                          |
| ------------------- | ------------------------------ |
| Define the field    | Base class (this package)      |
| Populate and read   | Provider                       |
| Persist and restore | Pipeline orchestrator (caller) |

**Capability declaration:**

Providers that support checkpointing must override the
`supports_checkpoint` property to return `True`:

```python
@property
def supports_checkpoint(self) -> bool:
    return True
```

The base class returns `False` by default. The orchestrator should
check `ds.supports_checkpoint` before relying on checkpoint state.
If `supports_checkpoint` is `False` and the caller sets
`self.checkpoint`, the provider ignores it and performs a full load.

**Checkpoint vs settings:**

`self.settings` and `self.checkpoint` are not interchangeable.
Settings define the static scope of the operation -- they are
configured once and do not change between runs. Checkpoint tracks
the moving position within that scope -- it advances after each
successful operation.

| Concern          | Field             | Mutates at runtime |
| ---------------- | ----------------- | ------------------ |
| What to read     | `self.settings`   | No                 |
| Where to resume  | `self.checkpoint` | Yes                |

When both apply to the same dimension (e.g. a `last_modified`
filter in settings and a `last_modified` cursor in checkpoint),
they compose: settings define the lower bound, checkpoint narrows
further within it. The provider is responsible for combining them
correctly.

**Example lifecycle:**

```python
if ds.supports_checkpoint:
    ds.checkpoint = state_store.load(ds.id)

ds.read()

if ds.supports_checkpoint:
    state_store.save(ds.id, ds.checkpoint)
```

The checkpoint content is provider-specific and opaque to the caller.

### `self.operation` after each method

Every tracked method call populates `self.operation` with an
`OperationInfo` report. All methods listed in `DatasetMethod` are
tracked automatically (`create`, `read`, `update`, `upsert`, `delete`,
`purge`, `list`, `rename`). `close()` is **not** tracked because it is
a lifecycle method with no meaningful operational output.

Outcome, timing, and error details are always captured automatically.
Row counts and schema are auto-derived from `self.output` when the
provider does not set them explicitly.

| Field         | Type                     | Auto-populated          | Description                                              |
| ------------- | ------------------------ | ----------------------- | -------------------------------------------------------- |
| `method`      | `DatasetMethod \| None`  | Always                  | The operation that was called.                           |
| `success`     | `bool`                   | Always                  | `True` when the method returns without raising.          |
| `error`       | `OperationError \| None` | On failure              | Structured error captured from the raised exception.     |
| `row_count`   | `int`                    | From `len(self.output)` | Number of rows read, written, or discovered.             |
| `started_at`  | `datetime`               | Always                  | UTC timestamp when the method started.                   |
| `ended_at`    | `datetime`               | Always                  | UTC timestamp when the method finished.                  |
| `duration_ms` | `float`                  | Always                  | Wall-clock duration in milliseconds.                     |
| `schema`      | `dict[str, Any] \| None` | From `self.output`      | Column names and PyArrow-inferred types.                 |
| `metadata`    | `dict[str, Any]`         | Never                   | Provider-specific info (request IDs, ETags, etc.).       |

**Auto-derivation rules:**

- `success` is set to `True` when the method returns without raising.
  On exception, it is set to `False`.
- `error` is populated from the raised exception's attributes
  (`message`, `code`, `status_code`, `details`). Not populated on
  success.
- `row_count` is derived from `len(self.output)` if the provider
  leaves it at the default (`0`). Providers may override by setting
  `self.operation.row_count` inside their method.
- `schema` is derived using
  `self.output.convert_dtypes(dtype_backend="pyarrow")` for any
  method where `self.output` exposes `convert_dtypes` (i.e. a
  DataFrame). Providers may override by setting
  `self.operation.schema` inside their method.
- `metadata` is never auto-populated. Providers set it for
  backend-specific information.

**Timing is guaranteed:** `started_at`, `ended_at`, and `duration_ms`
are populated even if the method raises an exception.

---

## Error Contract

Providers must use the shared exception hierarchy from
`ds_resource_plugin_py_lib.common.resource`. Every method has a
corresponding error class:

| Method     | Exception                          |
| ---------- | ---------------------------------- |
| `read()`   | `ReadError`                        |
| `create()` | `CreateError`                      |
| `update()` | `UpdateError`                      |
| `delete()` | `DeleteError`                      |
| `rename()` | `RenameError`                      |
| `purge()`  | `PurgeError`                       |
| `upsert()` | `UpsertError`                      |
| `list()`   | `ListError`                        |

All exceptions inherit from `DatasetException` > `ResourceException`.

### Rules

1. **Raise the matching error.** `create()` raises `CreateError`,
   `delete()` raises `DeleteError`, etc. Never raise a generic
   `Exception` or an unrelated error type.

2. **Wrap backend exceptions.** Raw backend errors (`psycopg2.Error`,
   `botocore.ClientError`, `HttpResponseError`, etc.) must never
   leak to the caller. Catch them and re-raise as the appropriate
   `DatasetException` subclass, chaining the original:

   ```python
   except pg.Error as e:
       raise CreateError(
           message=f"Failed to insert into {table}: {e}",
           details={"table": table, "rows": len(self.input)},
       ) from e
   ```

3. **Use `details` for context.** Include information that helps
   debugging: table name, row count, backend error code, identity
   columns used, etc.

4. **Custom errors must inherit.** Providers may define their own
   error classes, but they must inherit from `ResourceException`
   (or a subclass of it) so the caller can catch all provider
   errors with a single handler.

---

## Identity Columns

Methods that match rows against the target (`update`, `upsert`,
`delete`) need to know which columns uniquely identify a row.

### This is provider-specific

How identity columns are defined is a `self.settings` concern -- each
provider chooses the appropriate settings key for its backend:

| Provider        | Typical identity configuration                  |
| --------------- | ----------------------------------------------- |
| PostgreSQL      | `self.settings.update.identity_columns: [...]`  |
| Azure Table     | `PartitionKey` + `RowKey` (implicit)            |
| API / REST      | Endpoint path contains the entity ID            |
| File / SFTP     | File name or path (implicit)                    |

### Universal rules

- If identity columns are required and **not configured**, the method
  must raise -- never guess or default to "all columns."
- Identity columns must uniquely identify each row. If `self.input`
  contains duplicate identity values, the method must raise.
- The identity column configuration is a setting. It does not change
  the method's intent -- only how the provider locates the target rows.

---

## Abstract Methods

### `read()`

Read data from the source and assign it to `self.output`.

| Attribute         | Description                                       |
| ----------------- | ------------------------------------------------- |
| `self.output`     | The provider assigns the result here (DataFrame). |
| `self.settings`   | Controls what and how to read.                    |
| `self.checkpoint` | Incremental state (see below).                    |

**Rules:**

- Must populate `self.output` with the result set.
- If the source contains multiple pages, files, or partitions, the
  provider must collect all of them internally and assign a single
  concatenated result to `self.output`.
- On failure, the provider must raise. `self.output` may contain
  partial data collected before the error occurred -- the caller is
  responsible for deciding whether to use or discard it.
- Must not modify the source.

**Scope is determined by `self.settings`:**

What to read -- single resource or collection -- is a setting, not a
different method. The provider reads whatever the settings describe
and exhausts it completely:

| Setting pattern                           | Provider behaviour              |
| ----------------------------------------- | ------------------------------- |
| Single resource (file path, entity ID)    | Read one resource               |
| Collection (directory, prefix, endpoint)  | Read all, concatenate into one  |
| Paginated endpoint                        | Follow all pages to exhaustion  |
| Filtered (WHERE clause, query params)     | Read matching subset completely |

**Pagination within a single call is internal:**

If the backend requires multiple requests (paginated API, chunked
query, file listing), the provider handles iteration internally.
Page tokens and offsets used to exhaust a single read must not leak
into the abstract interface. The caller sees one `read()` call and
one complete DataFrame in `self.output`.

**Incremental / delta loads via `self.checkpoint`:**

When `self.checkpoint` is empty (`{}`), the provider performs a full
load. When it contains state from a previous run, the provider reads
only data that is new or changed since that checkpoint. After a
successful read, the provider updates `self.checkpoint` with the new
position so the caller can persist it for the next run.

| `self.checkpoint`    | Provider behaviour                           |
| -------------------- | -------------------------------------------- |
| `{}`                 | Full load -- read everything.                |
| `{"cursor": "abc"}`  | Incremental -- read from cursor onward.      |

Support for incremental loads is optional. Providers that do not
support it simply ignore `self.checkpoint`.

**Idempotent:** Yes for full loads. Incremental reads depend on
external state (`self.checkpoint`) and the source, so consecutive
calls may return different results.

---

### `create()`

Insert rows into the target.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.input`   | The rows to insert (DataFrame), set by the caller. |
| `self.settings`| Controls how to write (table, path, format, etc).  |

**Rules:**

- Must write all rows in `self.input` to the target as a single
  atomic transaction.
- Must create the target structure (table, file, container) if it
  does not exist, unless settings explicitly disable this.
- Must not delete, update, or overwrite existing data. `create()`
  is additive only.
- Must not modify `self.input`.

**Idempotent:** No. Calling `create()` twice with the same input may
produce duplicates. Use `upsert()` when retry safety is required.

---

### `update()`

Update existing rows in the target.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.input`   | The rows to update (DataFrame), set by the caller. |
| `self.settings`| Identity columns, target table, etc.               |

**Rules:**

- Must update only the rows in `self.input`, matched by identity
  columns defined in `self.settings`.
- Must execute as a single atomic transaction.
- Must not insert new rows. If a row in `self.input` does not exist
  in the target, it must be ignored or raise -- never inserted.
- Must not modify `self.input`.

**Idempotent:** Yes. Updating a row to the same values has no effect.

---

### `upsert()`

Insert rows that do not exist, update rows that do.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.input`   | The rows to upsert (DataFrame), set by the caller. |
| `self.settings`| Identity columns, target table, etc.               |

**Rules:**

- Must insert or update all rows in `self.input` as a single
  atomic transaction, matched by identity columns.
- Must not delete rows.
- Must not modify `self.input`.
- Providers that do not support atomic upsert must raise
  `NotSupportedError`.

**Idempotent:** Yes. This is the preferred write method for retry-safe
operations.

---

### `delete()`

Remove specific rows from the target.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.input`   | The rows to delete (DataFrame), set by the caller. |
| `self.settings`| Identity columns for matching.                     |

**Rules:**

- Must remove only the rows in `self.input`, matched by identity
  columns defined in `self.settings`.
- Must execute as a single atomic transaction.
- Must not remove rows that are not in `self.input`.
- Must not modify `self.input`.
- Deleting a row that does not exist is not an error.

**Idempotent:** Yes. Deleting an already-deleted row is a no-op.

---

### `purge()`

Remove all content from the target.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.settings`| Target table, path, container, etc.                |

**Rules:**

- Must remove all content from the target. `self.input` is not used.
- The target structure (table, container, directory) may or may not
  be removed depending on the backend. The only requirement is that
  the target is empty after `purge()` returns.
- The provider may iterate internally (e.g. loop over files, batch
  delete calls). Atomicity is not required -- idempotency makes it
  safe to retry on partial failure.
- Must not fail if the target is already empty.

**Idempotent:** Yes. Purging an empty target is a no-op.

---

### `list()`

Discover available resources.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.output`  | DataFrame of discovered resources with metadata.   |
| `self.settings`| Scope of discovery (schema, directory, prefix).    |

**Rules:**

- Must populate `self.output` with a DataFrame of available resources
  (tables, files, endpoints) and their metadata (e.g. name, size,
  modified date, type, schema).
- Which metadata columns are available depends on the backend.
- Must not modify any data.
- Providers that do not support discovery must raise
  `NotSupportedError`.

**Idempotent:** Yes.

---

### `rename()`

Rename a resource.

| Attribute      | Description                                        |
| -------------- | -------------------------------------------------- |
| `self.settings`| Current name and new name.                         |

**Rules:**

- Renames the resource (table, file, blob) in the backend.
- Must execute as a single atomic transaction.
- Providers that do not support renaming must raise
  `NotSupportedError`.

**Idempotent:** No. Renaming a resource that was already renamed will
fail.

---

### `close()`

Clean up the connection to the backend.

**Rules:**

- Must release any connections, sessions, or handles held by the
  linked service.
- Must not raise if the connection is already closed.
- Must be safe to call multiple times.

**Idempotent:** Yes.

---

## Summary

| Method     | Intent                | Returns | Atomic | Idempotent | `self.input` | `self.output`    | Empty input |
| ---------- | --------------------- | ------- | ------ | ---------- | ------------ | ---------------- | ----------- |
| `read()`   | Read data             | `None`  | N/A    | Yes*       | Not used     | Result set       | N/A         |
| `create()` | Insert rows           | `None`  | Yes    | No         | Required     | Affected rows    | No-op       |
| `update()` | Update rows           | `None`  | Yes    | Yes        | Required     | Affected rows    | No-op       |
| `upsert()` | Insert or update rows | `None`  | Yes    | Yes        | Required     | Affected rows    | No-op       |
| `delete()` | Remove specific rows  | `None`  | Yes    | Yes        | Required     | Affected rows    | No-op       |
| `purge()`  | Remove all content    | `None`  | N/A    | Yes        | Not used     | Not populated    | N/A         |
| `list()`   | Discover resources    | `None`  | N/A    | Yes        | Not used     | Resource metadata| N/A         |
| `rename()` | Rename a resource     | `None`  | Yes    | No         | Not used     | Not populated    | N/A         |
| `close()`  | Clean up connection   | `None`  | Yes    | Yes        | Not used     | Not populated    | N/A         |

- **Atomic** means the method must execute as a single transaction
  against the backend -- all rows succeed together or fail together.
  Read-only methods (`read`, `list`) are marked N/A because they have
  no side effects and may internally paginate or iterate without risk.
  `purge()` is N/A because its idempotency makes atomicity irrelevant
  -- a partial purge is safely retried.

- **`self.operation`** is an `OperationInfo` populated automatically
  on every tracked method call (all methods except `close()`). Row
  counts are available via `self.operation.row_count`.

- **`self.checkpoint`** is a `dict[str, Any]` for incremental/delta
  load state. The caller persists it between runs; the provider reads
  and updates it. An empty dict means full load. Providers declare
  support via the `supports_checkpoint` property.

- **Yes\*** (idempotent) for `read()` means idempotent for full loads.
  Incremental reads depend on `self.checkpoint` and the source, so
  consecutive calls may return different results.

- **Affected rows** means `self.output` is populated with the backend
  response if available, otherwise a copy of `self.input`.

- **No-op on empty input** means the method returns immediately without
  contacting the backend. This is not an error.

- **Capacity limits** are provider-specific. Providers must document
  their maximum `self.input` size and raise if exceeded. The caller
  is responsible for batching.

- **Connection ownership** belongs to the caller. The dataset must
  never call `self.linked_service.connect()` -- it only uses
  `self.linked_service.connection`. See `LINKED_SERVICE_CONTRACT.md`.

---

## Compliance Testing

The contract is enforced through a shared compliance test suite
shipped in `ds_resource_plugin_py_lib`. Every provider must run
these tests to verify it follows the rules defined in this document.

### How it works

The shared library provides an abstract test class
(`DatasetComplianceSuite`) that validates all contract rules using
**unit tests with mocked backends** -- no live connections required.

The suite verifies:

- `self.output` is populated after every data method.
- All methods return `None`.
- `self.input` is not mutated.
- Empty input results in a no-op (no backend call).
- `self.operation` is populated with timing, success, and row count.
- Errors are wrapped in the correct `DatasetException` subclass.
- Backend exceptions do not leak.

### Provider integration

Each provider implements two hooks and inherits the full suite:

```python
from unittest.mock import patch, MagicMock
from ds_resource_plugin_py_lib.testing import DatasetComplianceSuite

class TestMyProviderCompliance(DatasetComplianceSuite):

    def make_dataset(self):
        """Return a dataset instance with a mocked backend."""
        ds = MyDataset(settings=..., linked_service=MagicMock())
        return ds

    def sample_rows(self):
        """Return a DataFrame of valid rows for this provider."""
        return pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
```

The provider supplies:

- `make_dataset()` -- a dataset instance wired to a mocked linked
  service. No real backend connection.
- `sample_rows()` -- a DataFrame that represents valid data for the
  provider's schema.

The suite controls the test lifecycle. It sets `self.input`, calls
the methods, and asserts contract compliance. Backend calls are
mocked -- the suite validates the provider's behaviour (output
population, return types, error wrapping, input immutability), not
the backend itself.

When a new rule is added to the contract, a corresponding test is
added to the compliance suite. Every provider picks it up on their
next dependency update -- no manual test authoring required.

### Unsupported methods

All methods are inherently optional -- a provider may not be able to
fulfil any given method depending on the backend or protocol (e.g. a
read-only API cannot `create()`, an append-only log cannot `update()`).

Providers must raise `NotSupportedError` for any method they do not
support. The compliance suite detects this and skips further
validation for those methods.
