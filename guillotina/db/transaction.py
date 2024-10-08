from collections import OrderedDict
from lru import LRU
from guillotina import task_vars
from guillotina._settings import app_settings
from guillotina.component import query_adapter
from guillotina.const import ROOT_ID
from guillotina.content import Container
from guillotina.db.db import Root
from guillotina.db.interfaces import ITransaction
from guillotina.db.interfaces import ITransactionCache
from guillotina.db.interfaces import IWriter
from guillotina.db.orm.interfaces import IBaseObject
from guillotina.exceptions import ConflictError
from guillotina.exceptions import ReadOnlyError
from guillotina.exceptions import RestartCommit
from guillotina.exceptions import TIDConflictError
from guillotina.exceptions import TransactionClosedException
from guillotina.exceptions import TransactionObjectRegistrationMismatchException
from guillotina.profile import profilable
from guillotina.registry import Registry
from guillotina.utils import lazy_apply
from typing import Any
from typing import AsyncIterator
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from typing_extensions import TypedDict
from zope.interface import implementer

import asyncio
import asyncpg
import logging
import sys
import time

_EMPTY = "__<EMPTY VALUE>__"
TID_VERIFY_SKIP = {"Container", "guillotina.db.db.Root", "User"}


class ObjectResultType(TypedDict, total=False):
    state: bytes
    zoid: str
    tid: str
    id: str
    parent_id: Optional[str]


try:
    import prometheus_client

    CACHE_HITS = prometheus_client.Counter(
        "guillotina_cache_ops_total",
        "Total count of ops by type of operation and the error if there was.",
        labelnames=["type", "result"],
    )

    def record_cache_metric(
        name: str, result_type: str, value: Union[ObjectResultType, str], key_args: Dict[str, Any]
    ) -> None:
        if value == _EMPTY:
            result_type += "_empty"
        elif isinstance(value, (dict, asyncpg.Record)) and (
            value["zoid"] == ROOT_ID
            or value.get("parent_id") == ROOT_ID
            or isinstance(key_args.get("container"), (Container, Registry, Root))
        ):
            # since these types of objects will always be in cache, let's tag these differently
            result_type += "_roots"
        CACHE_HITS.labels(type=name, result=result_type).inc()


except ImportError:

    def record_cache_metric(
        name: str, result_type: str, value: Union[ObjectResultType, str], key_args: Dict[str, Any]
    ) -> None:
        ...


logger = logging.getLogger(__name__)


class Status:
    # ACTIVE is the initial state.
    ACTIVE = "Active"
    COMMITTING = "Committing"
    COMMITTED = "Committed"
    ABORTED = "Aborted"
    CONFLICT = "Conflict"


class cache:
    def __init__(
        self,
        key_gen: Callable[..., Dict[str, Any]],
        check_state_size=False,
        additional_keys: Optional[List[Callable[[Dict[str, Any]], Dict[str, Any]]]] = None,
    ):
        self.key_gen = key_gen
        self.check_state_size = check_state_size
        self.additional_keys = additional_keys or []

    def __call__(self, func):
        this = self

        async def _wrapper(self, *args, **kwargs):
            key_args = this.key_gen(*args, **kwargs)
            oid = key_args.get("oid")

            result = await self._cache.get(**key_args)
            if not isinstance(result, dict) and not isinstance(result, asyncpg.Record):
                result = None
            elif oid is None:
                oid = result["zoid"]
            if result and "type" not in result:
                result = None

            # For cacheable requests containing an oid as part of the
            # key parameters, double check that the TID in cache
            # matches the TID in the database.
            if result is not None and oid is not None and result.get("type") not in TID_VERIFY_SKIP:
                expected_tid = None
                try:
                    expected_tid = await self._manager._storage.get_obj_tid(self, oid)
                except KeyError:
                    logger.error(f"Couldn't find TID for object with zoid: {oid}")
                    record_cache_metric(func.__name__, "tid_check_miss", _EMPTY, key_args)
                    result = None

                if expected_tid:
                    tid = result["tid"]
                    if tid != expected_tid:
                        logger.warning(f"Cache TID mismatch: {expected_tid} vs {tid} for {oid}")
                        record_cache_metric(func.__name__, "outdated_tid", result, key_args)
                        result = None

            if result is not None:
                record_cache_metric(func.__name__, "hit", result, key_args)
                return result

            result = await func(self, *args, **kwargs)

            record_cache_metric(func.__name__, "miss", result, key_args)
            if result is not None:
                if result == _EMPTY:
                    await self._cache.set(result, keyset=[key_args])
                else:
                    try:
                        if (
                            not this.check_state_size
                            or len(result["state"]) < self._cache.max_cache_record_size
                        ):
                            await self._cache.set(
                                result,
                                keyset=[key_args] + [key_gen(result) for key_gen in this.additional_keys],
                            )
                    except (TypeError, KeyError):
                        await self._cache.set(result, **key_args)
                return result

        return _wrapper


@implementer(ITransaction)
class Transaction:
    _status = "empty"
    _skip_commit = False
    user = None

    def __init__(self, manager, loop=None, read_only: bool = False, cache=None, strategy=None):

        # Transaction Manager
        self._manager = manager

        self.initialize(read_only, cache, strategy)

        logger.debug("new transaction")

        # Connection to DB
        self._db_conn = None
        # Transaction on DB
        self._db_txn = None
        # Lock on the transaction
        # some databases need to lock during queries
        # this provides a lock for each transaction
        # which would correspond with one connection
        self._lock = asyncio.Lock()

    def initialize(self, read_only, cache=None, strategy=None):
        self._read_only = read_only
        self._txn_time = None
        self._tid = None
        self.status = Status.ACTIVE
        self.user = None

        # List of objects added
        # needs to be ordered because content inserted after other might
        # reference each other
        self.added = OrderedDict()
        self.modified = {}
        self.version_history = {}
        self.deleted = {}

        # List of (hook, args, kws) tuples added by addBeforeCommitHook().
        self._before_commit = []

        # List of (hook, args, kws) tuples added by addAfterCommitHook().
        self._after_commit = []
        self._after_commit_failure = []

        self._cache = cache or query_adapter(self, ITransactionCache, name=app_settings["cache"]["strategy"])
        self._query_count_start = self._query_count_end = 0

        self._annotation_cache = LRU(100)

    def get_query_count(self):
        """
        diff versions of asyncpg
        """
        if self._db_conn is None:
            return 0
        try:
            return self._db_conn._protocol.queries_count
        except Exception:
            try:
                return self._db_conn._con._protocol.queries_count
            except Exception:
                pass
        return 0

    async def get_connection(self):
        if self._db_conn is None:
            self._db_conn = await self._manager._storage.open()
            self._query_count_start = self.get_query_count()
        return self._db_conn

    @property
    def connection_reserved(self):
        return self._db_conn is not None

    @property
    def lock(self):
        return self._lock

    @property
    def manager(self):
        return self._manager

    @property
    def storage(self):
        return self._manager._storage

    def get_before_commit_hooks(self):
        """See ITransaction."""
        return iter(self._before_commit)

    def add_before_commit_hook(self, hook, *real_args, args=None, kws=None, **kwargs):
        """See ITransaction."""
        args = args or []
        kws = kws or {}
        kwargs.update(kws)
        self._before_commit.append((hook, real_args + tuple(args), kwargs))

    def get_after_commit_hooks(self):
        """See ITransaction."""
        return iter(self._after_commit)

    def get_after_commit_failure_hooks(self):
        """See ITransaction."""
        return iter(self._after_commit_failure)

    def add_after_commit_hook(self, hook, *real_args, args=None, kws=None, **kwargs):
        """See ITransaction."""
        args = args or []
        kws = kws or {}
        kwargs.update(kws)
        self._after_commit.append((hook, real_args + tuple(args), kwargs))

    def add_after_commit_failure_hook(self, hook, *real_args, args=None, kws=None, **kwargs):
        """See ITransaction."""
        args = args or []
        kws = kws or {}
        kwargs.update(kws)
        self._after_commit_failure.append((hook, real_args + tuple(args), kwargs))

    @profilable
    async def _call_after_commit_hooks(self, hooks, status=True):
        # Avoid to abort anything at the end if no hooks are registred.
        if not hooks:
            return
        # Call all hooks registered, allowing further registrations
        # during processing.  Note that calls to addAterCommitHook() may
        # add additional hooks while hooks are running, and iterating over a
        # growing list is well-defined in Python.
        for hook, args, kws in hooks:
            # The first argument passed to the hook is a Boolean value,
            # true if the commit succeeded, or false if the commit aborted.
            try:
                result = lazy_apply(hook, status, *args, **kws)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                # We need to catch the exceptions if we want all hooks
                # to be called
                logger.error("Error in after commit hook exec in %s ", hook, exc_info=sys.exc_info())

    async def _call_after_commit_success_hooks(self, status=True):
        result = await self._call_after_commit_hooks(self._after_commit, status=status)
        self._after_commit = []
        return result

    async def _call_after_commit_failure_hooks(self, status=True):
        result = await self._call_after_commit_hooks(self._after_commit_failure, status=status)
        self._after_commit_failure = []
        return result

    # BEGIN TXN
    async def tpc_begin(self):
        """Begin commit of a transaction

        conn is a real db that will be got by db.open()
        """
        self._txn_time = time.time()
        # make sure this is reset on retries
        self._after_commit = []
        self._after_commit_failure = []
        self._before_commit = []

    @property
    def read_only(self) -> bool:
        if self._read_only:
            return True
        if self._manager._storage._read_only:
            return True
        return False

    @profilable
    def register(self, obj: IBaseObject, new_oid: Optional[str] = None):
        """We are adding a new object on the DB"""
        if self.read_only:
            raise ReadOnlyError()

        if self.status in (Status.ABORTED, Status.COMMITTED, Status.CONFLICT):
            raise TransactionClosedException(f"Could not save {obj} to closed transaction", self, obj)

        if obj.__txn__ is None:
            obj.__txn__ = self

        oid = obj.__uuid__
        new = False
        if oid is None:
            if new_oid is not None:
                new = True
            else:
                new_oid = app_settings["uid_generator"](obj)
            oid = new_oid

        obj.__uuid__ = oid
        if new or obj.__new_marker__:
            self.added[oid] = obj
        elif oid in self.modified:
            if id(obj) != id(self.modified[oid]):
                raise TransactionObjectRegistrationMismatchException(self.modified[oid], obj)
        elif oid not in self.added:
            self.modified[oid] = obj

    def delete(self, obj: IBaseObject):
        if self.read_only:
            raise ReadOnlyError()
        oid = obj.__uuid__
        if oid is not None:
            if oid in self.modified:
                del self.modified[oid]
            elif oid in self.added:
                del self.added[oid]
            self.deleted[oid] = obj

    async def clean_cache(self):
        self._manager._hard_cache.clear()
        await self._cache.clear()

    async def refresh(self, ob):
        """
        refresh an object with the value from the database
        """
        new = await self.get(ob.__uuid__, ignore_registered=True)
        for key, value in new.__dict__.items():
            if key.startswith("__"):
                continue
            ob.__dict__[key] = value
        ob.__serial__ = new.__serial__
        ob.__txn__ = self

    @cache(
        lambda oid: {"oid": oid},
        True,
        additional_keys=[lambda item: {"container": item["parent_id"], "id": item["id"]}],
    )
    async def _get(self, oid):
        return await self._manager._storage.load(self, oid)

    @profilable
    async def get(self, oid: str, ignore_registered: bool = False) -> IBaseObject:
        """Getting a oid from the db"""
        if not ignore_registered:
            obj = self.modified.get(oid, None)
            if obj is not None:
                return obj

        result = self._manager._hard_cache.get(oid, None)
        if result is None:
            result = await self._get(oid)

        obj = await app_settings["object_reader"](result)
        obj.__txn__ = self
        if obj.__immutable_cache__:
            # ttl of zero means we want to provide a hard cache here
            self._manager._hard_cache[oid] = result
        return obj

    async def commit(self) -> None:
        restarts = 0
        while True:
            # for now, the max commit restarts we'll manage...
            try:
                return await self._commit()
            except RestartCommit:
                restarts += 1
                if restarts >= 3:
                    raise
                else:
                    logger.warn(f"Restarting commit for tid: {self._tid}")
                    await self._db_txn.restart()  # type: ignore

    @profilable
    async def _commit(self):
        await self._call_before_commit_hooks()
        self.status = Status.COMMITTING
        try:
            if len(self.modified) > 0 or len(self.deleted) > 0 or len(self.added) > 0:
                # only do the commit steps if we have objects to commit
                await self.tpc_commit()
                # vote will do conflict resolution if there are conflicting writes
                await self.tpc_vote()
            else:
                # signal to not worry about not making a transaction here..
                self._skip_commit = True
            await self.tpc_finish()
        except (ConflictError, TIDConflictError) as ex:
            # this exception should bubble up
            # in the case of TIDConflictError, we should make sure to try
            # and invalidate again to make sure we aren't caching the ob
            self.status = Status.CONFLICT
            await self._manager._storage.abort(self)
            await self._cache.close(invalidate=isinstance(ex, TIDConflictError), publish=False)
            self.tpc_cleanup()
            self.version_history = {}
            await self._call_after_commit_failure_hooks()
            raise
        self.status = Status.COMMITTED
        await self._call_after_commit_success_hooks()

    @profilable
    async def abort(self):
        self.status = Status.ABORTED
        await self._manager._storage.abort(self)
        await self._cache.close(invalidate=False)
        self.tpc_cleanup()

    async def _call_before_commit_hooks(self):
        for hook, args, kws in self._before_commit:
            result = lazy_apply(hook, *args, **kws)
            if asyncio.iscoroutine(result):
                await result
        self._before_commit = []

    @profilable
    async def _store_object(self, obj, uid, writer, serialized, added=False, update_not_new=False):
        # There is no serial
        if added:
            serial = None
        else:
            serial = getattr(obj, "__serial__", None) or 0
        await self._manager._storage.store(uid, serial, writer, serialized, obj, self)
        obj.__serial__ = self._tid
        obj.__uuid__ = uid
        if obj.__txn__ is None:
            obj.__txn__ = self
        if update_not_new:
            obj.__new_marker__ = False

    async def initialize_tid(self) -> None:
        if self._tid is not None:
            return self._tid
        if not self.read_only:
            tid = await self.storage.get_next_tid(self)
            if tid is not None:
                self._tid = tid

    @profilable
    async def tpc_commit(self):
        """Commit changes to an object"""

        await self.initialize_tid()

        if self._db_txn is None:
            await self.storage.start_transaction(self)

        for oid, obj in self.deleted.items():
            await self._manager._storage.delete(self, oid)

        # Get the writer objects for each object, then call the serialize()
        added_oids = list(self.added)
        modified_oids = list(self.modified)
        added_writers = [IWriter(self.added[oid]) for oid in added_oids]
        modified_writers = [IWriter(self.modified[oid]) for oid in modified_oids]
        serialized = []
        if added_writers or modified_writers:
            futures = [writer.serialize() for writer in added_writers + modified_writers]
            serialized = await asyncio.gather(*futures)
        for idx in range(len(added_oids)):
            await self._store_object(
                self.added[added_oids[idx]],
                added_oids[idx],
                added_writers[idx],
                serialized[idx],
                True,
                update_not_new=True,
            )
        for idx in range(len(modified_oids)):
            await self._store_object(
                self.modified[modified_oids[idx]],
                modified_oids[idx],
                modified_writers[idx],
                serialized[idx + len(added_oids)],
            )

    @profilable
    async def tpc_vote(self):
        """Verify that a data manager can commit the transaction."""
        # potential conflict error, get changes
        # Check if there is any commit bigger than the one we already have
        conflicts = await self.storage.get_conflicts(self)
        for conflict in conflicts:
            # both writing to same object...
            if conflict["zoid"] in self.modified and conflict["zoid"] not in (ROOT_ID,):
                modified_keys = [k for k in self.modified.keys()]
                logger.warning(
                    f"Could not resolve conflicts in TID: {self._tid}\n"
                    f'Conflicted TID: {conflict["tid"]}\n'
                    f"IDs: {modified_keys}"
                )
                raise ConflictError(self)

    @profilable
    async def tpc_finish(self):
        """Indicate confirmation that the transaction is done."""
        if not self.read_only:
            await self.storage.commit(self)
        await self._cache.close()
        self.tpc_cleanup()

    def tpc_cleanup(self):
        self.added = {}
        self.version_history = {zoid: obj.__serial__ for zoid, obj in self.modified.items()}
        self.modified = {}
        self.deleted = {}
        self._db_txn = None
        self._annotation_cache = LRU(100)

    # Inspection

    @profilable
    @cache(lambda oid: {"oid": oid, "variant": "keys"})
    async def keys(self, oid: str) -> List[str]:
        keys = []
        for record in await self._manager._storage.keys(self, oid):
            keys.append(record["id"])
        return keys

    @cache(
        lambda container, key: {"container": container, "id": key},
        True,
        additional_keys=[lambda item: {"oid": item["zoid"]}],
    )
    async def _get_child(self, container, key):
        return await self._manager._storage.get_child(self, container.__uuid__, key)

    @profilable
    async def get_child(self, parent, key):
        result = await self._get_child(parent, key)
        if result is None:
            return None

        return await self._fill_object(result, parent)

    async def _fill_object(self, item: dict, parent: IBaseObject) -> IBaseObject:
        obj = await app_settings["object_reader"](item)
        obj.__parent__ = parent
        obj.__txn__ = self
        return obj

    async def _get_batch_children(self, parent: IBaseObject, keys: List[str]) -> AsyncIterator[IBaseObject]:
        for litem in await self._manager._storage.get_children(self, parent.__uuid__, keys):
            if len(litem["state"]) < self._cache.max_cache_record_size:
                await self._cache.set(litem, container=parent, id=litem["id"])
            yield await self._fill_object(litem, parent)

    async def get_children(self, parent, keys):
        """
        More performant way to get groups of items.
        - look at cache
        - batch get from storage
        - async for iterate items
        - store retrieved values in storage
        """
        lookup_group = []  # backlog of object that need to be looked up
        for key in keys:
            item = await self._cache.get(container=parent, id=key)
            if item is None:
                lookup_group.append(key)
                if len(lookup_group) > 15:  # limit batch size
                    async for litem in self._get_batch_children(parent, lookup_group):
                        yield litem
                    lookup_group = []
                continue

            if len(lookup_group) > 0:
                # we need to clear this buffer first before we can yield this item
                async for litem in self._get_batch_children(parent, lookup_group):
                    yield litem
                lookup_group = []

            yield await self._fill_object(item, parent)

        # flush the rest
        if len(lookup_group) > 0:
            async for item in self._get_batch_children(parent, lookup_group):
                yield item

    @profilable
    async def contains(self, oid: str, key: str) -> bool:
        for obj in self.deleted.values():
            if obj.id == key and obj.__parent__.__uuid__ == oid:
                return False

        return await self._manager._storage.has_key(self, oid, key)  # noqa

    @profilable
    @cache(lambda oid: {"oid": oid, "variant": "len"})
    async def len(self, oid: str) -> bool:
        return await self._manager._storage.len(self, oid)

    @profilable
    async def items(self, container):
        # XXX not using cursor because we can't cache with cursor results...
        keys = await self.keys(container.__uuid__)
        async for item in self.get_children(container, keys):
            yield item.__name__, item

    @profilable
    @cache(
        lambda base_obj, id: {"container": base_obj, "id": id, "variant": "annotation"},
        True,
        additional_keys=[lambda item: {"oid": item["zoid"]}],
    )
    async def _get_annotation(self, base_obj, id):
        try:
            result = await self._manager._storage.get_annotation(self, base_obj.__uuid__, id)
        except KeyError:
            return _EMPTY
        if result is None:
            return _EMPTY
        return result

    @profilable
    async def get_annotation(self, base_obj, id, reader=None):
        cache_key = f"{base_obj.__uuid__}::{id}"
        result = None
        if cache_key in self._annotation_cache:
            result = self._annotation_cache[cache_key]
            self._cache._hits += 1

        if result and result != _EMPTY:
            return result
        if not result:
            result = await self._get_annotation(base_obj, id)
        if result == _EMPTY:
            self._annotation_cache[cache_key] = _EMPTY
            raise KeyError(id)
        if reader is None:
            obj = await app_settings["object_reader"](result)
        else:
            obj = await reader(result)
        obj.__of__ = base_obj.__uuid__
        obj.__txn__ = self
        self._annotation_cache[cache_key] = obj
        return obj

    @profilable
    async def get_annotations(self, base_obj, ids, reader=None):
        cached = {}
        to_fetch = []
        for _id in ids:
            cache_key = f"{base_obj.__uuid__}::{_id}"
            if cache_key in self._annotation_cache and self._annotation_cache[cache_key] != _EMPTY:
                cached[_id] = self._annotation_cache[cache_key]
            else:
                to_fetch.append(_id)
        if not to_fetch:
            return cached

        # One query fetch all remaining annotations.
        raw_data = await self._manager._storage.get_annotations(self, base_obj.__uuid__, to_fetch)
        if not raw_data:
            return cached

        # Read the state data.
        if not reader:
            reader = app_settings["object_reader"]
        keys = list(raw_data)
        futures = [reader(raw_data[key]) for key in keys]
        state_data = await asyncio.gather(*futures)
        for data in state_data:
            data.__of__ = base_obj.__uuid__
            data.__txn__ = self
        return {**cached, **{keys[idx]: state_data[idx] for idx in range(len(keys))}}

    def clear_annotation_cache(self, base_obj, _id):
        try:
            del self._annotation_cache[f"{base_obj.__uuid__}::{_id}"]
        except KeyError:
            ...

    @profilable
    @cache(lambda oid: {"oid": oid, "variant": "annotation-keys"})
    async def get_annotation_keys(self, oid):
        return [r["id"] for r in await self._manager._storage.get_annotation_keys(self, oid)]

    async def del_blob(self, bid):
        return await self._manager._storage.del_blob(self, bid)

    async def write_blob_chunk(self, bid, oid, chunk_index, data):
        return await self._manager._storage.write_blob_chunk(self, bid, oid, chunk_index, data)

    async def read_blob_chunk(self, bid, chunk=0):
        return await self._manager._storage.read_blob_chunk(self, bid, chunk)

    async def read_blob_chunks(self, bid):
        return await self._manager._storage.read_blob_chunks(self, bid)

    async def get_total_number_of_objects(self):
        return await self._manager._storage.get_total_number_of_objects(self)

    async def get_total_number_of_resources(self):
        return await self._manager._storage.get_total_number_of_resources(self)

    async def get_total_resources_of_type(self, type_):
        return await self._manager._storage.get_total_resources_of_type(self, type_)

    async def _get_resources_of_type(self, type_, page_size=1000):
        page = 1
        keys = await self._manager._storage._get_page_resources_of_type(
            self, type_, page=page, page_size=page_size
        )
        while len(keys) > 0:
            for key in keys:
                yield key
            page += 1
            keys = await self._manager._storage._get_page_resources_of_type(
                self, type_, page=page, page_size=page_size
            )

    async def get_page_of_keys(self, parent_oid, page=1, page_size=1000):
        return await self._manager._storage.get_page_of_keys(self, parent_oid, page=page, page_size=page_size)

    @profilable
    async def iterate_keys(self, oid, page_size=1000):
        page = 1
        keys = await self._manager._storage.get_page_of_keys(self, oid, page=page, page_size=page_size)
        while len(keys) > 0:
            for key in keys:
                yield key
            page += 1
            keys = await self._manager._storage.get_page_of_keys(self, oid, page=page, page_size=page_size)

    def __enter__(self):
        task_vars.tm.set(self.manager)
        task_vars.txn.set(self)
        return self

    def __exit__(self, *args):
        """
        contextvars already tears down to previous value, do not set to None here!
        """

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *args):
        return self.__exit__()
