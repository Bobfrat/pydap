try:
    from functools import singledispatch
except ImportError:
    from singledispatch import singledispatch

from collections import Iterable

from pydap.model import *
from pydap.lib import encode, quote
from pydap.responses.lib import BaseResponse
from pydap.responses.dds import typemap


INDENT = ' ' * 4


class DASResponse(BaseResponse):
    def __init__(self, dataset):
        BaseResponse.__init__(self, dataset)
        self.headers.extend([
            ('Content-description', 'dods_das'),
            ('Content-type', 'text/plain; charset=utf-8'),

            # CORS
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Headers',
                'Origin, X-Requested-With, Content-Type'),
        ])

    def __iter__(self):
        for line in das(self.dataset):
            yield line


@singledispatch
def das(var, level=0):
    raise StopIteration


@das.register(DatasetType)
def _(var, level=0):
    yield '{indent}Attributes {{\n'.format(indent=level*INDENT)

    for attr, values in var.attributes.items():
        for line in build_attributes(attr, values, level+1):
            yield line

    for child in var.children():
        for line in das(child, level=level+1):
            yield line
    yield '{indent}}}\n'.format(indent=level*INDENT)


@das.register(StructureType)
def structure(var, level=0):
    yield '{indent}{name} {{\n'.format(indent=level*INDENT, name=var.name)

    for attr, values in var.attributes.items():
        for line in build_attributes(attr, values, level+1):
            yield line

    for child in var.children():
        for line in das(child, level=level+1):
            yield line
    yield '{indent}}}\n'.format(indent=level*INDENT)


@das.register(BaseType)
@das.register(GridType)
def base(var, level=0):
    yield '{indent}{name} {{\n'.format(indent=level*INDENT, name=var.name)

    for attr, values in var.attributes.items():
        for line in build_attributes(attr, values, level+1):
            yield line
    yield '{indent}}}\n'.format(indent=level*INDENT)


def build_attributes(attr, values, level=0):
    """
    Recursive function to build the DAS.

    """
    # check for metadata
    if isinstance(values, dict):
        yield '{indent}{attr} {{\n'.format(indent=(level)*INDENT, attr=attr)
        for k, v in values.items():
            for line in build_attributes(k, v, level+1):
                yield line
        yield '{indent}}}\n'.format(indent=(level)*INDENT)
    else:
        # get type
        type = get_type(values)

        # encode values
        if isinstance(values, basestring) or not isinstance(values, Iterable):
            values = [encode(values)]
        else:
            values = map(encode, values)

        yield '{indent}{type} {attr} {values};\n'.format(
                indent=(level)*INDENT,
                type=type,
                attr=quote(attr),
                values=', '.join(values))


def get_type(values):
    if hasattr(values, 'dtype'):
        return typemap[values.dtype.char]
    elif isinstance(values, basestring) or not isinstance(values, Iterable):
        return type_convert(values)
    else:
        # if there are several values, they may have different types, so we need
        # to convert all of them and use a precedence table
        types = map(type_convert, values)
        precedence = ['String', 'Float64', 'Int32']
        types.sort(key=precedence.index)
        return types[0]


def type_convert(obj):
    """
    Map Python objects to the corresponding Opendap types.

    """
    if isinstance(obj, float):
        return 'Float64'
    elif isinstance(obj, (long, int)):
        return 'Int32'
    else:
        return 'String'
