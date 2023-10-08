import pdb
from guillotina.db.interfaces import IPostgresStorage
from zope.interface import implementer
from string import Template
from guillotina._settings import app_settings


import asyncpg

from guillotina.exceptions import ConflictIdOnContainer

SQL_TABLES = """
CREATE SCHEMA IF NOT EXISTS $schema;

CREATE SEQUENCE IF NOT EXISTS $schema.tid_sequence;

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$$$
BEGIN
    NEW.timestamp = now() at time zone 'utc';
    IF NEW.of is not NULL THEN
        -- annotation, update parent timestamp
        -- there is a slight performance penalty here.
        EXECUTE 'UPDATE ' || quote_ident(TG_TABLE_SCHEMA)
                    || '.' || quote_ident(TG_TABLE_NAME)
                    || ' SET timestamp = now() at time zone ''utc'' '
                    || ' WHERE zoid = ''' || quote_ident(NEW.of) || ''''
        USING NEW;
    END IF;
    RETURN NEW;
END;
$$$$ language 'plpgsql';
    CREATE OR REPLACE FUNCTION dataapi_concat(ts timestamp, zoid text)
  RETURNS text
AS
$$BODY$$
    select concat_ws('//', ts, zoid);
$$BODY$$
LANGUAGE sql
IMMUTABLE;

CREATE TABLE IF NOT EXISTS $schema.objects
(
    zoid character varying(64) COLLATE pg_catalog."default" NOT NULL,
    tid bigint NOT NULL,
    state_size bigint NOT NULL,
    part bigint NOT NULL,
    resource boolean NOT NULL,
    of character varying(64) COLLATE pg_catalog."default",
    otid bigint,
    parent_id character varying(64) COLLATE pg_catalog."default",
    id text COLLATE pg_catalog."default",
    type text COLLATE pg_catalog."default" NOT NULL,
    json jsonb,
    state bytea,
    "timestamp" timestamp without time zone,
    CONSTRAINT objects_pkey PRIMARY KEY (zoid),
    CONSTRAINT objects_of_fkey FOREIGN KEY (of)
        REFERENCES $schema.objects (zoid) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT objects_parent_id_fkey FOREIGN KEY (parent_id)
        REFERENCES $schema.objects (zoid) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT object_parent_id_zoid_check CHECK (parent_id::text <> zoid::text) NOT VALID
)
WITH (
    OIDS = FALSE
);
"""

SQL_INDICES = """
CREATE INDEX IF NOT EXISTS idx_objects_access_roles
    ON $schema.objects USING gin
    ((json -> 'access_roles'::text))
    TABLESPACE pg_default    WHERE of IS NULL AND (type <> ANY ('{Resource,SourceAccount,RealIdentity}'::text[]));

CREATE INDEX IF NOT EXISTS idx_objects_access_users
    ON $schema.objects USING gin
    ((json -> 'access_users'::text))
    TABLESPACE pg_default    WHERE of IS NULL AND (type <> ANY ('{Resource,SourceAccount,RealIdentity}'::text[]));

CREATE INDEX IF NOT EXISTS object_id
    ON $schema.objects USING btree
    (id COLLATE pg_catalog."default")
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS object_main_types
    ON $schema.objects USING btree
    (type COLLATE pg_catalog."default")
    TABLESPACE pg_default    WHERE of IS NULL AND type <> 'Resource'::text
;

CREATE INDEX IF NOT EXISTS object_of
    ON $schema.objects USING btree
    (of COLLATE pg_catalog."default")
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS object_parent
    ON $schema.objects USING btree
    (parent_id COLLATE pg_catalog."default")
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS object_tid
    ON $schema.objects USING btree
    (tid)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS object_type
    ON $schema.objects USING btree
    (type COLLATE pg_catalog."default")
    TABLESPACE pg_default;

CREATE UNIQUE INDEX IF NOT EXISTS objects_annotations_unique
    ON $schema.objects USING btree
    (of COLLATE pg_catalog."default", id COLLATE pg_catalog."default")
    TABLESPACE pg_default;

CREATE UNIQUE INDEX IF NOT EXISTS objects_parent_id_id_key
    ON $schema.objects USING btree
    (parent_id COLLATE pg_catalog."default", id COLLATE pg_catalog."default")
    TABLESPACE pg_default    WHERE parent_id::text <> 'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD'::text;
"""


@implementer(IPostgresStorage)
class PostgresqlStorage:
    def __init__(
        self,
        dsn: str,
        read_only=False,
        schema="public",
        **kw,
    ):
        self.schema = schema
        self.dsn = dsn
        self._read_only = read_only
        self.pool = None

    # create the tables and indices
    async def initialize(self, loop=None, **kw):
        self.pool = await asyncpg.create_pool(dsn=self.dsn, loop=loop)

        async with self.pool.acquire() as con:
            t = Template(SQL_TABLES)
            query = t.substitute(schema=self.schema)
            await con.execute(query)

            t = Template(SQL_INDICES)
            query = t.substitute(schema=self.schema)
            await con.execute(query)

    # finish any pending task
    async def finalize(self):
        raise NotImplemented()  # pragma: no cover

    # get a connection from the pool
    async def open(self):
        con = await self.pool.acquire()
        return con

    # release the connection back to the pool
    async def close(self, con):
        await self.pool.release(con)

    # deserialize an object from the database
    # use the oid to get the object then deserialize it
    # using the configured state reader.
    async def load(self, txn, oid):
        query = f"SELECT * FROM {self.schema}.objects WHERE zoid = $1"
        async with self.pool.acquire() as con:
            row = await con.fetchrow(query, oid)
            if row is None:
                raise KeyError(oid)
        row = dict(row)
        row["state"] = await app_settings["state_reader"](row)
        return row

    # this is confusing: get the TID from an object
    async def get_obj_tid(self, txn, oid):
        query = f"SELECT tid FROM {self.schema}.objects WHERE zoid = $1"
        async with self.pool.acquire() as con:
            row = await con.fetchrow(query, oid)
            if row is None:
                raise KeyError(oid)
        return row["tid"]

    # this is the main method for storing an object
    # either insert or update the object in the database
    # keep a serialized object also stored in a cache.
    async def store(self, oid, old_serial, writer, serialized, obj, txn):
        assert oid is not None
        is_update = old_serial is not None and old_serial > 0

        # note: interesting metric, ration between updates and inserts
        # its interesting to understand our workload.
        if is_update:
            return await self._update(oid, old_serial, writer, serialized, obj, txn)
        else:
            try:
                return await self._insert(oid, old_serial, writer, serialized, obj, txn)
            except asyncpg.exceptions.UniqueViolationError as ex:
                # Try to post an already existing object
                if "Key (parent_id, id)" in ex.detail or "Key (of, id)" in ex.detail:
                    raise ConflictIdOnContainer(ex)

    async def _update(self, oid, old_serial, writer, serialized, obj, txn):
        pickled, cache_value = serialized
        part = writer.part
        if part is None:
            part = 0

        query = f"""
        WITH ROWS AS(
            UPDATE {self.schema}.objects
            SET
                tid = $1,
                state_size = $2,
                part = $3,
                resource = $4,
                of = $5,
                otid = $6,
                parent_id = $7,
                id = $8,
                type = $9,
                json = $10,
                state = $11
            WHERE zoid = $12 AND tid = $13
            RETURNING 1
        ) SELECT count(*) FROM ROWS;
        """

        async with self.pool.acquire() as con:
            res = await con.fetchval(
                query,
                txn._tid,
                len(pickled),
                part,
                writer.resource,
                writer.of,
                old_serial,
                writer.parent_id,
                writer.id,
                writer.type,
                None,
                pickled,
                oid,
                old_serial,
            )
            breakpoint()
            assert res == 1

    async def _insert(self, oid, old_serial, writer, serialized, obj, txn):
        pickled, cache_value = serialized
        part = writer.part
        if part is None:
            part = 0

        query = f"""
        INSERT INTO {self.schema}.objects (
            tid,
            state_size,
            part,
            resource,
            of,
            otid,
            parent_id,
            id,
            type,
            json,
            state,
            zoid
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) 
        RETURNING zoid;
        """

        async with self.pool.acquire() as con:
            res = await con.fetchval(
                query,
                txn._tid,
                len(pickled),
                part,
                writer.resource,
                writer.of,
                old_serial,
                writer.parent_id,
                writer.id,
                writer.type,
                None,
                pickled,
                oid,
            )
            assert res == oid

    # delete an object from the database
    async def delete(self, txn, oid):
        raise NotImplemented()  # pragma: no cover

    # get the next transaction id using 'nextval'
    # i wonder if we can just ignore the tid and rely
    # on pg to transparently handle it for us.
    async def get_next_tid(self, txn):
        async with self.pool.acquire() as con:
            tid = await con.fetchval(f"SELECT nextval('{self.schema}.tid_sequence')")
            return tid

    # same... can we ignore tid?
    async def get_current_tid(self, txn):
        async with self.pool.acquire() as con:
            tid = await con.fetchval(f"SELECT last_value FROM {self.schema}.tid_sequence")
            return tid

    # helper method to execute a query and get just one row
    async def get_one_row(self, smt, *args):
        raise NotImplemented()  # pragma: no cover

    # First get get a connection
    # then we start the transaction
    # there are many logic to handle the errors while
    # starting the transaction
    async def start_transaction(self, txn, retries=0):
        async with self.pool.acquire() as con:
            await con.execute("BEGIN;")

    # this is a bit insane, instead on relying on postgres
    # manually throw a query 'txn_conflicts' to get the conflicts
    # why? i dont really have a clue.
    async def get_conflicts(self, txn):
        return []

    # commit. why do we need to have a layer on top on this
    # already well defined pg client api?
    # commit, get_transaction, get_one_row, abort,... it is
    # not necessary nor useful.
    async def commit(self, transaction):
        async with self.pool.acquire() as con:
            await con.execute("COMMIT;")

    # same.
    async def abort(self, transaction):
        async with self.pool.acquire() as con:
            await con.execute("ROLLBACK;")

    # giving a parent get children by looking at the parent_id index
    async def get_page_of_keys(self, txn, oid, page=1, page_size=1000):
        breakpoint()
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                f"SELECT id FROM {self.schema}.objects WHERE parent_id = $1 LIMIT $2 OFFSET $3",
                oid,
                page_size,
                page_size * (page - 1),
            )
            return [r["id"] for r in rows]

    # same but without pagination.
    async def keys(self, txn, oid):
        breakpoint()
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                f"SELECT * FROM {self.schema}.objects WHERE parent_id = $1",
                oid,
            )
            return rows

    # get a child by id and parent oid
    async def get_child(self, txn, parent_oid, id):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                f"SELECT * FROM {self.schema}.objects WHERE parent_id = $1 AND id = $2",
                parent_oid,
                id,
            )
            return row
    
    async def get_children(self, txn, parent_oid, ids):
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                f"SELECT * FROM {self.schema}.objects WHERE parent_id = $1 AND id = ANY($2)",
                parent_oid,
                ids,
            )
            return rows

    # does the child exists?
    async def has_key(self, txn, parent_oid, id):
        breakpoint()
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                f"SELECT 1 FROM {self.schema}.objects WHERE parent_id = $1 AND id = $2",
                parent_oid,
                id,
            )
            return row is not None

    # get the number of children
    async def len(self, txn, oid):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                f"SELECT count(*) FROM {self.schema}.objects WHERE parent_id = $1",
                oid,
            )
            return row["count"]

    # another way to get the children? this time
    # as an async generator.
    async def items(self, txn, oid):
        raise NotImplemented()  # pragma: no cover

    # get the annotation of an object
    # what is the id?
    async def get_annotation(self, txn, oid, id):
        async with self.pool.acquire() as con:
            row = await con.fetchrow(
                f"SELECT * FROM {self.schema}.objects WHERE of = $1 AND id = $2",
                oid,
                id,
            )
            return row

    # Get all the resource annotated rows
    async def get_annotations(self, txn, oid, ids):
        async with self.pool.acquire() as con:
            rows = await con.fetch(
                f"SELECT * FROM {self.schema}.objects WHERE of = $1 AND id = ANY($2)",
                oid,
                ids,
            )
            return rows

    # how this is different from the prior?
    async def get_annotation_keys(self, txn, oid):
        raise NotImplemented()  # pragma: no cover

    # why not just write the blob when creating the
    # resource?
    async def write_blob_chunk(self, txn, bid, oid, chunk_index, data):
        raise NotImplemented()  # pragma: no cover

    # read the binary
    async def read_blob_chunk(self, txn, bid, chunk=0):
        raise NotImplemented()  # pragma: no cover

    # cursor query to get all the chunks
    async def read_blob_chunks(self, txn, bid):
        raise NotImplemented()  # pragma: no cover

    # why do we have all this mutable methods?
    # a resource can be inmutable by nature, should be
    # a better idea to create a new resource and mark
    # the old one as deleted?
    async def del_blob(self, txn, bid):
        raise NotImplemented()  # pragma: no cover

    # all this count type queries
    async def get_total_number_of_objects(self, txn):
        raise NotImplemented()  # pragma: no cover

    async def get_total_number_of_resources(self, txn):
        raise NotImplemented()  # pragma: no cover

    async def get_total_resources_of_type(self, txn, type_):
        raise NotImplemented()  # pragma: no cover

    async def _get_page_resources_of_type(self, txn, type_, page, page_size):
        raise NotImplemented()  # pragma: no cover

    async def vacuum(self):
        raise NotImplemented()  # pragma: no cover

    # compat
    @property
    def objects_table_name(self):
        return "objects"
   
    @property
    def supports_unique_constraints(self):
        return True
