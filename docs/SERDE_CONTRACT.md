# Serde Contract

This document defines the contract for serde components in this library:

- **serializers** transform an in-memory object into another representation
- **deserializers** transform a source representation into an in-memory object

In practice, serde is most often used by datasets:

- `serializer` prepares data for writes/exports
- `deserializer` prepares data returned from reads/imports

---

## Principles

1. **Configuration belongs on the serde object.** Static options such as
   `format`, parsing/writer kwargs, field mappings, and provider-specific
   formatting should be expressed through `settings` when the serde object
   is created.
2. **Runtime context belongs in `__call__()`.** The value being
   serialized/deserialized and transient runtime inputs such as
   `boto3_session` must be passed at execution time.
3. **Do not own backend connection lifecycle.** Serde components may use
   runtime clients/sessions passed in by the caller, but they must not
   create or manage long-lived backend connections themselves.
4. **Fail loudly.** Unsupported formats, invalid input, and missing
   required runtime context must raise explicit errors.
5. **Keep intent stable.** Settings control how conversion happens, not
   what operation the caller is asking for.

---

## Base Classes

- Serializers subclass `DataSerializer`
- Deserializers subclass `DataDeserializer`

Both are extensible runtime components intended to be subclassed.

### Serializer shape

- implements `__call__(obj, **kwargs) -> Any`

### Deserializer shape

- implements `__call__(value, **kwargs) -> Any`
- may override `get_next(...) -> bool`
- may override `get_end_cursor(...) -> str | None`

The pagination/checkpoint hooks are optional and default to no-op
behavior in `DataDeserializer`.

---

## Registration and Discovery

### Serializers

Serializers are **registered assets**. Provider or protocol packages may
register them in `resource.yaml` under the top-level `serde` key.

Example:

```yaml
serde:
  - name: EmploymentUpdateSerializer
    type: ds.resource.serde.sdworx.employment-update
    version: 1.0.0
    description: Serializer for SD Worx EmploymentUpdateRequest XML format
    class_name: ds_provider_sdworx_py_lib.serde.employment_update.EmploymentUpdateSerializer
```

`ResourceClient` is responsible for:

- discovering registered serializers
- exposing serializer metadata
- creating serializer instances from config

Serializer lookup uses `(type, version)`.

Built-in serializers shipped by this library use these canonical
registered identifiers:

- `DS.RESOURCE.SERIALIZER.DATAFRAME.PANDAS` / `1.0.0`
- `DS.RESOURCE.SERIALIZER.DATAFRAME.AWSWRANGLER` / `1.0.0`

### Deserializers

Deserializers are part of the serde contract too, but they are **not
currently registered as standalone assets through `ResourceClient`**.

They are runtime components used by datasets and follow the same general
construction/call rules described below.

When a deserializer is nested inside a dataset representation, its
`deserialize(...)` path accepts both:

- the preferred nested `settings` shape
- legacy flat config such as top-level `format` and `kwargs`

If `type` and `version` are present on the nested deserializer object, they
are ignored today unless and until standalone deserializer registration is
introduced.

---

## Construction Contract

Serde classes should accept all static configuration through `settings`.

Typical settings fields include:

- `format`
- `kwargs`
- column mappings
- XML/JSON field configuration
- provider-specific parsing/formatting options

Examples from this library:

- `PandasSerializer(settings={"format": ..., "kwargs": ...})`
- `AwsWranglerSerializer(settings={"format": ..., "kwargs": ...})`
- `PandasDeserializer(settings={"format": ..., "kwargs": ...})`
- `AwsWranglerDeserializer(settings={"format": ..., "kwargs": ...})`

Providers should prefer settings objects that are easy to express in
YAML/JSON configuration. Flat constructor kwargs may be supported
temporarily for backward compatibility.

For deserializers, that backward compatibility applies both to direct class
construction and to nested dataset deserialization.

---

## Dataset Representation JSON Example

Serde is commonly attached directly to a dataset representation as nested
`serializer` and `deserializer` objects.

Example:

```json
{
  "id": "8d5d8f7b-4e79-4c10-9f03-9e72c0f9d3d2",
  "name": "employment-update",
  "version": "1.0.0",
  "settings": {
    "path": "s3://bucket/employment-update.xml"
  },
  "linked_service": {
    "type": "DS.RESOURCE.LINKED_SERVICE.S3",
    "version": "1.0.0",
    "settings": {
      "region_name": "eu-north-1"
    }
  },
  "serializer": {
    "type": "ds.resource.serde.sdworx.employment-update",
    "version": "1.0.0",
    "settings": {
      "request_level_columns": ["CompanyNo", "EmployeeNo"],
      "metadata_columns": ["ValidFrom", "ValidUntil"]
    }
  },
  "deserializer": {
    "settings": {
      "format": "XML",
      "kwargs": {
        "xpath": ".//EmploymentUpdate"
      }
    }
  }
}
```

In this example:

- `serializer` is customized with provider-specific static config
- `deserializer` is customized with parsing config for the dataset's read path
- runtime-only values such as `boto3_session` are still passed to
  `__call__()`, not stored in the dataset JSON

When the serializer is a registered asset, the nested serializer config is
the same shape you would pass to `ResourceClient.serializer(config)`.

For backward compatibility, nested deserializers may also be expressed in a
legacy flat form such as:

```json
{
  "deserializer": {
    "type": "DS.RESOURCE.DESERIALIZER.DATAFRAME.PANDAS",
    "version": "1.0.0",
    "format": "JSON"
  }
}
```

The preferred representation is still to place static config under
`deserializer.settings`.

---

## Call Contract

### Serializer Calls

`__call__(obj, **kwargs)` performs serialization.

- `obj` is the value to serialize
- runtime-only kwargs are allowed
- runtime-only kwargs must not be required at construction time

Examples of runtime-only kwargs:

- `boto3_session`
- request-scoped credentials/tokens
- temporary output handles

### Deserializer Calls

`__call__(value, **kwargs)` performs deserialization.

- `value` is the source representation to parse/load
- runtime-only kwargs are allowed
- runtime-only kwargs must not be required at construction time

Examples of deserializer inputs:

- raw bytes
- JSON/XML/CSV strings
- file-like objects
- remote paths/URIs

---

## Return Value Contract

Return types are serde-specific and provider-specific.

Examples:

- serializer returns `str`, `bytes`, or an SDK write result
- deserializer returns `pandas.DataFrame` or another in-memory object

Providers must document any non-obvious return shape.

---

## ResourceClient Contract for Serializers

`ResourceClient.serializer(config)` creates serializer instances using the
registered class.

Creation rules:

1. Read `type` and `version` from `config`
2. Resolve the registered serializer class
3. Remove `type` and `version` from `config`
4. If `settings` is present, deserialize the serializer from the remaining config
5. Otherwise pass the remaining keys as constructor keyword arguments for
   backward compatibility

This keeps serializer creation in `ResourceClient` while allowing the
preferred nested `settings` pattern.

---

## Error Contract

Serde components must raise an appropriate exception when:

- the input object/value type is unsupported
- required runtime context is missing
- the configured format is unsupported
- conversion cannot be completed correctly

They must not silently produce partial or misleading output.

---

## Provider Implementation Guidance

- subclass the appropriate base class
- keep static `settings` separate from runtime execution inputs
- avoid hidden environment-dependent behavior
- keep output deterministic for the same input/config when practical
- make side effects explicit if conversion writes to a backend
