from guillotina.db.orm.interfaces import IBaseObject

import gzip
import pickle
import typing


def reader(result: dict) -> IBaseObject:
    state = result["state"]
    if result["state"][0:2] == b"\x1f\x8b":
        state = pickle.loads(gzip.decompress(state))
    else:
        state = pickle.loads(state)
    obj = typing.cast(IBaseObject, state)
    obj.__uuid__ = result["zoid"]
    obj.__serial__ = result["tid"]
    obj.__name__ = result["id"]
    return obj
