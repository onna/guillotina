from guillotina.db.orm.interfaces import IBaseObject

import brotli
import pickle
import struct
import typing

PICKLE_PREFIXES = [
    pickle.PROTO + struct.pack("<B", pickle.HIGHEST_PROTOCOL),
    pickle.PROTO + struct.pack("<B", pickle.DEFAULT_PROTOCOL),
]


async def reader(result: dict) -> IBaseObject:
    state = result["state"]

    # Detect if this is a compressed or plain pickle.
    if state[-1:] == pickle.STOP and state[0:2] in PICKLE_PREFIXES:
        try:
            state = pickle.loads(state)
        except pickle.UnpicklingError:
            state = pickle.loads(brotli.decompress(state))
    else:
        state = pickle.loads(brotli.decompress(state))

    obj = typing.cast(IBaseObject, state)
    obj.__uuid__ = result["zoid"]
    obj.__serial__ = result["tid"]
    obj.__name__ = result["id"]
    return obj
