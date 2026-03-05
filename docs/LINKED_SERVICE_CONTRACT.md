# Linked Service Contract

This document defines the abstract methods available on every linked
service, their intent, and the rules that all provider implementations
must follow.

A linked service represents a connection to a backend data store
(database, API, file system, cloud service). It owns the
authentication credentials and connection lifecycle. Datasets use a
linked service to reach their backend -- the linked service is the
"how to connect", the dataset is the "what to do".

---

## Principles

1. **One service, one backend.** Each linked service instance connects
  to exactly one backend. Multiple backends require multiple linked
   service instances.
2. **Settings configure, they do not change intent.** Settings control
  provider-specific connection details (host, port, credentials,
   timeouts). They never alter what a method does -- only how it
   connects.
3. **Fail loudly.** If a connection cannot be established or verified,
  the method raises an appropriate error. It never silently returns a
   broken or partial connection.
4. **Context manager support.** Every linked service supports `with`
  statements. `__enter__` returns `self`, `__exit__` calls `close()`.

---

## Schema and Dataclass Alignment

The provider-facing schema used to create a linked service instance
(for example JSON validated before `LinkedService.deserialize(...)`)
must stay in sync with linked service dataclass fields.

### Why this is critical

The schema defines what callers are allowed to send. The dataclass
defines what runtime construction accepts. If these drift, payloads may
either fail during deserialize or pass values that should have remained
internal implementation details.

### Field categories

Every linked service field must be classified as either exposed or
internal.

| Category | Intent | User payload | Dataclass guidance |
| -------- | ------ | ------------ | ------------------ |
| Exposed field | Caller configures this value. | Allowed | Keep as normal dataclass init field and include in schema. |
| Internal field | Runtime detail. | Not allowed | Use `init=False`, `serialize=False`, and a default. |

### Mandatory rules

1. **Schema and exposed dataclass fields must match.**
   - Every exposed field in the dataclass must be represented in schema.
   - Every schema field must map to a dataclass field.
2. **Internal fields must not be schema properties.**
   - Never expose runtime-only fields (`connection`, clients, pools,
     caches, handles, tokens, session objects, etc.).
3. **Internal fields must not be user-initializable.**
   - Set `init=False` so payload cannot pass those keys through
     `deserialize()`.
4. **Internal fields must remain safe at runtime.**
   - Provide `default` or `default_factory` (or set in `__post_init__`)
     so instances are always valid after construction.
5. **Unknown schema keys must be rejected.**
   - Use strict schema validation (`additionalProperties: false`) at
     each object level to fail fast on unsupported keys.
6. **Schema validity must imply constructability.**
   - Any payload that passes the provider schema must construct the
     dataclass successfully via `deserialize()` without runtime
     construction errors.
   - If a payload can pass schema validation but fail dataclass
     construction, the schema and dataclass are out of sync and the
     provider is non-compliant.

### Construction guarantee

Treat this as a hard compatibility guarantee between frontend/user
payload and backend dataclass binding:

- **Guarantee:** schema-valid payload -> successful dataclass
  construction.
- **Corollary:** dataclass changes that affect required/optional fields,
  field types, or field names must be reflected in schema in the same
  change.
- **Verification:** providers should include a contract test that
  validates representative schema-valid payloads and asserts
  `LinkedService.deserialize(payload)` succeeds.

### Provider communication requirement

Provider docs must clearly state which fields are user-facing config and
which are internal implementation details. This must be explicit for the
following field groups:

- Top-level linked service fields (`id`, `name`, `version`,
  `settings`, etc.)
- Nested settings fields
- Inherited compatibility fields required by abstract/base classes that
  are intentionally internal and not user-exposed

---

## Fields

| Field         | Type                        | Description                                |
| ------------- | --------------------------- | ------------------------------------------ |
| `id`          | `uuid.UUID`                 | Unique identifier for this linked service. |
| `name`        | `str`                       | Human-readable name.                       |
| `description` | `str \| None`               | Optional description.                      |
| `version`     | `str`                       | Provider version.                          |
| `settings`    | `LinkedServiceSettingsType` | Connection configuration.                  |

---

## Abstract Properties

### `connection`

Return the backend client or connection object.

**Returns:** `Any` -- the type is provider-specific. It may be a
database connection, an SDK client, an HTTP session, or any handle
the dataset needs to interact with the backend.

**Rules:**

- Must return the connection object established by `connect()`.
- Must raise `ConnectionError` if `connect()` has not been called.
- The property name is standardized; the return type is not. Each
provider defines and documents the concrete type.

**Example usage by a dataset:**

```python
response = self.linked_service.connection.get("/api/data")
cursor = self.linked_service.connection.cursor()
```

---

## Abstract Methods

### `connect()`

Establish a connection to the backend data store. The result is stored
internally and accessible via the `connection` property.

| Attribute       | Description                                      |
| --------------- | ------------------------------------------------ |
| `self.settings` | Connection parameters (host, port, credentials). |

**Returns:** `None`.

**Rules:**

- Must establish a connection and store it so that the `connection`
property returns it.
- Must authenticate using credentials from `self.settings`.
- Must raise `ConnectionError` if the connection cannot be established.
- Must raise `AuthenticationError` if credentials are invalid.
- May re-establish the connection if called again on an already-connected
service.

**Idempotent:** Yes. Calling `connect()` on an already-connected
service should re-use or re-establish the connection.

---

### `test_connection()`

Verify that the connection to the backend is healthy.

| Attribute       | Description                         |
| --------------- | ----------------------------------- |
| `self.settings` | Connection parameters used to test. |

**Returns:** `tuple[bool, str]` -- a boolean indicating success and
a message. On success: `(True, "")`. On failure: `(False, "reason")`.

**Rules:**

- Must perform a lightweight check against the backend (e.g. a ping,
a simple query, an API health endpoint).
- Must **not** raise on connection failure -- instead return
`(False, "error message")`. Exceptions are reserved for unexpected
internal errors, not for a failed health check.
- Must not modify any data.
- Should complete quickly -- this is a health check, not a load test.

**Idempotent:** Yes.

---

### `close()`

Release connections, sessions, or handles held by the linked service.

**Returns:** `None`.

**Rules:**

- Must release any open connections, sessions, or handles.
- Must not raise if the connection is already closed.
- Must be safe to call multiple times.
- Called automatically by `__exit__` when using a context manager.

**Idempotent:** Yes. Closing an already-closed service is a no-op.

---

## Error Contract

Providers must use the shared exception hierarchy from
`ds_resource_plugin_py_lib.common.resource`. Linked service errors
inherit from `LinkedServiceException` > `ResourceException`.

| Error class           | When to raise                               |
| --------------------- | ------------------------------------------- |
| `ConnectionError`     | Connection failed or not yet established.   |
| `AuthenticationError` | Credentials are invalid or expired.         |
| `AuthorizationError`  | Authenticated but insufficient permissions. |
| `NotSupportedError`   | Provider does not support a method.         |

### Rules

1. **Wrap backend exceptions.** Raw backend errors must never leak to
  the caller. Catch them and re-raise as the appropriate
   `LinkedServiceException` subclass, chaining the original:
2. **Use `details` for context.** Include information that helps
  debugging: host, port, database name, service endpoint, etc.
3. **Custom errors must inherit.** Providers may define their own
  error classes, but they must inherit from `LinkedServiceException`
   (or a subclass of it).

---

## Provider Discovery (Reference)

Linked service providers must be discoverable through a package-level
`resource.yaml` file and Python entry points.

Required `resource.yaml` fields for linked service entries:

- `name`
- `type` (for example: `ds.resource.linked_service.{name}`)
- `version`
- `description`
- `class_name`

The provider package must also define:

```toml
[project.entry-points."ds.providers"]
{name} = "ds_provider_{name}_py_lib"

[tool.setuptools.package-data]
ds_provider_{name}_py_lib = ["resource.yaml", "py.typed"]
```

Enum rule: enum member values used for identifiers must
be lowercase strings.

---

## Summary

| Member              | Intent                | Returns       | Idempotent |
| ------------------- | --------------------- | ------------- | ---------- |
| `connection`        | Access backend client | `Any`         | N/A        |
| `connect()`         | Establish connection  | `None`        | Yes        |
| `test_connection()` | Verify health         | `(bool, str)` | Yes        |
| `close()`           | Release resources     | `None`        | Yes        |

- All methods are inherently optional -- a provider may raise
`NotSupportedError` for any method it cannot fulfil.
- `**connection`** is a property that returns the backend client.
It raises `ConnectionError` if `connect()` has not been called.
The concrete return type is provider-defined.
- `**connect()**` is typically called once. The connection is stored
internally and accessed via the `connection` property.
- `**test_connection()**` does **not** raise on failure -- it returns
`(False, "reason")`. This allows callers to check connectivity
without exception handling.
- `**close()`** is called automatically when exiting a `with` block.
