"""
**File:** ``builtin.py``
**Region:** ``ds_resource_plugin_py_lib/common/serde/serialize``

Description
-----------
Built-in serializer registration metadata shipped with this library.
"""

from .base import SerializerInfo

BUILTIN_SERIALIZER_VERSION = "1.0.0"

PANDAS_DATAFRAME_SERIALIZER_INFO = SerializerInfo(
    type="DS.RESOURCE.SERIALIZER.DATAFRAME.PANDAS",
    name="DATAFRAME_PANDAS",
    class_name="ds_resource_plugin_py_lib.common.serde.serialize.pandas.PandasSerializer",
    version=BUILTIN_SERIALIZER_VERSION,
    description="Built-in pandas DataFrame serializer.",
)

AWSWRANGLER_DATAFRAME_SERIALIZER_INFO = SerializerInfo(
    type="DS.RESOURCE.SERIALIZER.DATAFRAME.AWSWRANGLER",
    name="DATAFRAME_AWSWRANGLER",
    class_name="ds_resource_plugin_py_lib.common.serde.serialize.awswrangler.AwsWranglerSerializer",
    version=BUILTIN_SERIALIZER_VERSION,
    description="Built-in awswrangler DataFrame serializer.",
)

BUILTIN_SERIALIZER_INFOS = (
    PANDAS_DATAFRAME_SERIALIZER_INFO,
    AWSWRANGLER_DATAFRAME_SERIALIZER_INFO,
)