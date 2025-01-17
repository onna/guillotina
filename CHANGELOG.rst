CHANGELOG
=========
5.5.5 (2025-01-10)
-------------------
- More delete file handling improvements

5.5.4 (2025-01-09)
-------------------
- Add delete file endpoint

5.5.3 (2024-10-09)
-------------------
- More PG handling improvements

5.5.2 (2024-10-08)
-------------------
- Fix IPatchField field_converter

5.5.1 (2024-09-10)
-------------------
- Python 3.10

5.5.0 (2024-05-10)
-------------------

- Adding interfaces to use for standardizing cloud vacuum support

5.4.20 (2024-02-14)
-------------------

- Minor fixture teardown handling

5.4.19 (2023-12-19)
-------------------

- Fix transaction context manager doesn't abort the txn when a exception is raised

5.4.18 (2023-09-12)
-------------------

- More work on fixing annotation bugs.

5.4.17 (2023-09-08)
-------------------

- One more annotation cache fix.

5.4.16 (2023-09-07)
-------------------

- Fix transaction.get_annotation().

5.4.15 (2023-07-28)
-------------------

- More annotation cache updates + test fixes.

5.4.14 (2023-07-26)
-------------------

- More connection re-use.

5.4.13 (2023-07-25)
-------------------

- Use txn conn for getting/setting TID sequence since it's not affected by transaction.

5.4.12 (2023-05-04)
-------------------

- Prevent using cache if the type field is missing.

5.4.11 (2023-04-20)
-------------------

- More updates to prevent in-memory caching of registry objects.

5.4.10 (2023-03-31)
-------------------

- Keep reference to modified object's serial after commit.

5.4.9 (2023-02-25)
------------------

- Add state_reader method to ensure cache includes the correct/populated state value.

5.4.8 (2023-02-24)
------------------

- More cache sync updates.

5.4.7 (2023-02-24)
------------------

- Ensure 'of' is cached for annotation data.

5.4.6 (2023-02-08)
------------------

- Make content serialization and deserialization methods asynchronous to support reading state objects from other object storage.

5.4.5 (2023-01-24)
------------------

- Perform each migration in a separate transaction

5.4.4 (2023-01-12)
-------------------

- Allow annotations and resource types to not be stored in memory
- Fix CI/tests

5.4.3 (2022-11-13)
------------------

- Allow initialize_tid to be called multiple times.


5.4.2 (2022-11-09)
------------------

- Update brotli compression quality to improve performance.


5.4.1 (2022-10-19)
------------------

- Enable brotli (de)compression on pickle dump fields.


5.4.0 (2021-04-20)
------------------

- Remove db transaction strategy support
- Remove CockroachDB support
- Try not to reserve connection when possible
  [vangheem]


5.3.68 (2021-04-16)
-------------------

- No longer have dedicated read connection and do not use any prepared statements
  [vangheem]


5.3.67 (2021-02-03)
-------------------

- Improve memcached metrics probe [lferran]


5.3.66 (2021-01-13)
-------------------

- Fix: prevent caching large objects on fill_cache [lferran]


5.3.65 (2021-01-11)
-------------------

- Fix emcache client settings pass-through [lferran]


5.3.64 (2021-01-11)
-------------------

- Bump emcache version and provide support for new metrics and new intialization parameters
  [pfreixes]


5.3.63 (2020-11-30)
-------------------

- Check deleted list in Transaction.contains
  [qiwn]

- Change commit order (delete before add) in Transaction.tpc_commit
  [qiwn]


5.3.62 (2020-11-25)
-------------------

- Fix recording root hit/miss metrics
  [vangheem]


5.3.61 (2020-11-11)
-------------------

- Do nothing when memcache delete_all opeartion receives an empty list. Observe
  size of the len of keys [pfreixes]


5.3.60 (2020-11-03)
-------------------

- Increase pg operation long tail bucket size
  [vangheem]


5.3.59 (2020-11-03)
-------------------

- Fix db metrics to isolate acquiring connection
  [vangheem]


5.3.58 (2020-10-16)
-------------------

- Safer keys for memcached driver [lferran]


5.3.57 (2020-10-14)
-------------------

- Add metric for object cache records size [lferran]

- Fix metrics context manager when prometheus not installed [lferran]

5.3.56 (2020-10-14)
-------------------

- Fix BasicCache.fill_cache: do not exclude parent_id key for root
  object [lferran]


5.3.55 (2020-10-01)
-------------------

- Add memcached support as cache driver [lferran]

5.3.54 (2020-09-30)
-------------------

- increase precision of lock metrics reporting
  [vangheem]


5.3.53 (2020-09-30)
-------------------

- Add metrics for in-memory cache
  [vangheem]


5.3.52 (2020-09-30)
-------------------

- Move to github actions
  [lferran]
- Add id checker for move
  [qiwn]

5.3.51 (2020-09-24)
-------------------

- Record metrics on cache hit/misses
  [vangheem]

- Record metrics on time waiting for pg locks
  [vangheem]


5.3.50 (2020-09-23)
-------------------

- Record redis cache misses
  [vangheem]


5.3.49 (2020-09-22)
-------------------

- Add metrics to pg and redis operations
  [vangheem]


5.3.48 (2020-09-09)
-------------------

- Add IFileNameGenerator adapter
  [qiwn]


5.3.47 (2020-06-25)
-------------------

- Include bugfix version for aiohttp in setup.py [lferran]


5.3.46 (2020-06-17)
-------------------

- Fix registry update, when type provided mismatch with the one specified
  by the schema return an error HTTP status code instead of throwing an
  exception.
  [pfreixes]


5.3.45 (2020-06-11)
-------------------

- Fix: Be able to define optional requestBody [lferran]


5.3.44 (2020-06-11)
-------------------

- Be able to define optional requestBody [lferran]


5.3.43 (2020-06-07)
-------------------

- Optimize json schema ref resolution to not make so copies of all json schema definition
  for every validator instance
  [vangheem]

- Fix json schema ref resolution for nested objects
  [vangheem]


5.3.42 (2020-05-26)
-------------------

- Allow arbitrary path parameter within the path parameters
  [dmanchon]


5.3.41 (2020-05-19)
-------------------

- Fix import
  [vangheem]


5.3.40 (2020-05-19)
-------------------

- swagger tags fixes [ableeb]

- Register aiohttp server object with app that it is serving(`._server`)
  [vangheem]

5.3.39 (2020-05-11)
-------------------

- Handle ConnectionResetError when downloading files
  [vangheem]


5.3.38 (2020-05-04)
-------------------

- Bug fix: handle raw strings in json payload [lferran]


5.3.37 (2020-04-24)
-------------------

- swagger tags fixes


5.3.36 (2020-04-24)
-------------------

- Provide patch operations for json field
  [vangheem]

- Optimize extend operation for bucket list field
  [vangheem]

- `.` and `..` should be blocked as valid ids. The browser will auto translate them
  to what current dir and parent dir respectively which gives unexpected results.
  [vangheem]


5.3.35 (2020-04-21)
-------------------

- Change log level for conflict errors to warning and fix locating tid of conflict error
  [vangheem]


5.3.34 (2020-04-14)
-------------------

- Use bigint for statement replacement values
  [vangheem]


5.3.33 (2020-03-24)
-------------------

- Error handling: ValueDeserializationError editing registry value
  [vangheem]

- Handle db transaction closed while acquiring transaction lock
  [vangheem]

- Handle db transaction closed while acquiring lock
  [vangheem]

- Handle connection errors on file head requests
  [vangheem]


5.3.32 (2020-03-06)
-------------------

- Fix integer query param validation [lferran]


5.3.31 (2020-02-28)
-------------------

- Be able to have async schema invariants
  [vangheem]


5.3.30 (2020-02-24)
-------------------

- Provide better validation for json schema field
  [vangheem]


5.3.29 (2020-02-21)
-------------------

- Handle error when "None" value provided for behavior data
  [vangheem]


5.3.28 (2020-02-20)
-------------------

- Handle connection reset errors when downloading files
  [vangheem]


5.3.27 (2020-02-13)
-------------------

- Add `max_ops` property to `PatchField`, `BucketListField` and `BucketDictField`
  [vangheem]

- Add clear action to list, dict and annotation patch fields
  [vangheem]


5.3.26 (2020-02-12)
-------------------

- Improve performance of bucket dict field
  [vangheem]


5.3.25 (2020-02-11)
-------------------

- Fix storages integration with some asyncpg pool settings
  [vangheem]


5.3.24 (2020-02-06)
-------------------

- Fix release
  [vangheem]


5.3.23 (2020-02-06)
-------------------

- Be able to configure `max_inactive_connection_lifetime` and `max_queries`
  of pg pool.
  [vangheem]

- Do not have timeout when closing pg connection.
  [vangheem]


5.3.22 (2020-02-05)
-------------------

- Fix asyncpg integration with connection leaks on timeout
  [vangheem]


5.3.21 (2020-02-04)
-------------------

- Validate POST @sharing payload too [lferran]


5.3.20 (2020-02-01)
-------------------

- Be able to customize pg db in test fixtures
  [vangheem]

5.3.19 (2020-02-01)
-------------------

- fix release
  [vangheem]


5.3.18 (2020-01-31)
-------------------

- add IAnnotations.async_del type annotation
  [vangheem]


5.3.17 (2020-01-31)
-------------------

- Add pg db constraint for annotation data
  [vangheem]


5.3.16 (2020-01-30)
-------------------

- more IRequest type hints
  [vangheem]

5.3.15 (2020-01-30)
-------------------

- Add json to IRequest for mypy
  [vangheem]


5.3.14 (2020-01-28)
-------------------

- Fix DummyCache type signature to be the same as base class
  [vangheem]


5.3.13 (2020-01-22)
-------------------

- Correctly bubble http errors for file downloads
  [vangheem]


5.3.12 (2020-01-21)
-------------------

- Add title/description to json schema field serialization
  [vangheem]


5.3.11 (2020-01-16)
-------------------

- Better error handling on redis connection issues
  [vangheem]


5.3.10 (2020-01-16)
-------------------

- JSON Schema and open api serialization fixes
  [vangheem]


5.3.9 (2020-01-15)
------------------

- Fix validating array params in query parameters [lferran]

- Add open api tests and fix ones that do not pass tests
  [vangheem]


5.3.8 (2020-01-15)
------------------

- Fix automatic type conversion on nested fields
  [vangheem]


5.3.7 (2020-01-13)
------------------

- Fix automatic type conversion on nested fields. Fixes #832
  [vangheem]


5.3.6 (2020-01-09)
------------------

- Be able to start database transaction before transaction has started it
  without causing errors
  [vangheem]


5.3.5 (2020-01-09)
------------------

- Fix optimized lookup to work with fields that do not have `_type`
  [vangheem]


5.3.4 (2020-01-07)
------------------

- Fix query param validation
  [vangheem]


5.3.3 (2020-01-07)
------------------

- Optimize json deserialization
  [vangheem]

- Update Dockerfile
  [svx]


5.3.2 (2020-01-03)
------------------

- Be able to disable supporting range headers in `IFileManager.download`
  [vangheem]

- Make `Field.required` an optional property. To change default required behavior,
  you can monkey patch `IField['required'].default = False`
  [vangheem]


5.3.1 (2020-01-02)
------------------

- Save old file attrs before content is cleaned
  [vangheem]


5.3.0 (2020-01-02)
------------------

- Add `Range` header support
  [vangheem]

5.2.2 (2019-12-27)
------------------

- Fix validating None values in required fields
  [vangheem]


5.2.1 (2019-12-21)
------------------

- Fix error with requeued async queue tasks
  [vangheem]


5.2.0 (2019-12-20)
------------------

- Added `IIDChecker` adapter
  [vangheem]

- Added `valid_id_characters` app setting
  [vangheem]


5.1.26 (2019-12-20)
-------------------

- Bubble cancelled errors in resolver
  [vangheem]

- Fix duplicate behaviors interfaces in get_all_behavior_interfaces()
  [qiwn]


5.1.25 (2019-12-18)
-------------------

- Better CancelledError handling in resolving a request
  [vangheem]

- Fix adding duplicate behaviors
  [qiwn]

- PatchField: added operation "multi"
  [masipcat]


5.1.24 (2019-12-16)
-------------------

- @duplicate: added option to reset acl [inakip]

5.1.23 (2019-12-11)
-------------------

- Make pytest.mark.app_settings work in older pytest versions too [lferran]

- @move: destination id conflict should return 409 error, not 412
  [inaki]


5.1.22 (2019-12-02)
-------------------

- Fix security bug in @move and @duplicate [lferran]

5.1.21 (2019-11-29)
-------------------

- Allow to iterate keys, values and items of a BucketDictValue
  [lferran]

5.1.20 (2019-11-27)
-------------------

- Fix security bug: anonymous users were being granted
  guillotina.Authenticated [lferran]


5.1.19 (2019-11-19)
-------------------

- Update default zope.interface to 4.7.1
  [bloodbare]

- Be able to provide `DEBUG_SUBSCRIBERS` env variable to get details about
  event timings being run.
  [vangheem]


5.1.18 (2019-11-25)
-------------------

- Make sure to reset registry task var when setting up new container
  [vangheem]


5.1.17 (2019-11-22)
-------------------

- Fix potential deadlock issues when storage read conn handling
  [vangheem]


5.1.16 (2019-11-21)
-------------------

- Allow uid as destination in `@duplicate` and `@move`
  [qiwn]


5.1.15 (2019-11-20)
-------------------

- Fix correctly saving patch field
  [vangheem]


5.1.14 (2019-11-20)
-------------------

- Fix patch field validation
  [vangheem]


5.1.13 (2019-11-13)
-------------------

- Prevent JSONField name clash with field `validator` decorator
  [vangheem]


5.1.12 (2019-11-12)
-------------------

- Remove task call back to run execute_futures automatically. aiohttp reuses task object for
  keepalive implementation and the `_callbacks` were never run
  [vangheem]


5.1.11 (2019-11-12)
-------------------

- Lazy create thread pool executor so we can properly use thread pool setting
  [vangheem]


5.1.10 (2019-11-12)
-------------------

- Be able to customize number of thread pool workers
  [vangheem]


5.1.9 (2019-11-12)
------------------

- Add custom settings into test server
  [qiwn]


5.1.8 (2019-11-11)
------------------

- bump


5.1.7 (2019-11-11)
------------------

- Make sure to use `txn.lock` when using pg connection
  [vangheem]


5.1.6 (2019-11-08)
------------------

- reduce the load dbvacuum can cause
  [vangheem]


5.1.6 (unreleased)
------------------

- Fix `required` param not specified in service `parameters` configuration
  [vangheem]


5.1.5 (2019-11-06)
------------------

- Fix test util: add db in task vars too [lferran]
  [lferran]

- Added "pickle_protocol" to app_settings
  [masipcat]


5.1.4 (2019-11-06)
------------------

- Add `extra_headers` parameter into `FileManager.prepare_download()`
  [qiwn]


5.1.3 (2019-11-04)
------------------

New:

- More mypy support and better type checking
  [vangheem]

- Added deserializer for IUnionField
  [masipcat]

- Provide new `@field.validator` to validate field values against bound fields
  [vangheem]

Fixes:

- Fix @invariant validation. Any usage of it previously would cause exceptions.
  [vangheem]


5.1.2 (2019-10-30)
------------------

- Handle empty `G_` environment variable values
  [vangheem]


5.1.1 (2019-10-29)
------------------

- more mypy definitions on ITransactionManager


5.1.0 (2019-10-25)
------------------

- Move guillotina_dbusers to guillotina.contrib.dbusers
  [jordic, lferran]

- Missed debug information.
  [bloodbare]


5.0.28 (2019-10-23)
-------------------

- Cache debug information should be debug level
  [bloodbare]


5.0.27 (2019-10-23)
-------------------

- Do not fallback to `setattr` with unhandled errors on fields
  [vangheem]


5.0.26 (2019-10-21)
-------------------

- Documentation and training fixes
  [vangheem]


5.0.25 (2019-10-21)
-------------------

- Documentation and training fixes
  [vangheem]

- Fix compatiblity issues with Python 3.8
  [masipcat]


5.0.24 (2019-10-17)
-------------------

- Add `BucketDictValue.clear()`
  [qiwn]

- Fix error closing cache with some objects
  [vangheem]


5.0.23 (2019-10-17)
-------------------

- Cache improvements:
    - Store changes in cache immediately after transaction has finished instead of in task
    - Clear txn cache fill data after using it
    - Properly cache annotation lookup misses


5.0.22 (2019-10-16)
-------------------

- Fix push invalidation data type
  [vangheem]


5.0.21 (2019-10-16)
-------------------

- `add_behavior` should only write to database if behavior is new for object
  [vangheem]

- Improve cache hit performance by setting cache keys on objects loaded
  directly by uid and by looking up children object
  [vangheem]

5.0.20 (2019-10-15)
-------------------

- Add event when database tables created for postgres
  [vangheem]


5.0.19 (2019-10-14)
-------------------

- Bucket dict field does not always split index properly
  [vangheem]


5.0.18 (2019-10-13)
-------------------

- Fix connection leaks in edge-cases
  [masipcat]

- Pinned asyncpg to 0.19.0
  [masipcat]


5.0.17 (2019-10-11)
-------------------

- Transaction manager type hints
  [vangheem]


5.0.16 (2019-10-11)
-------------------

- Handle deserialization errors on bucket fields. Otherwise, dict values were getting incorrectly saved
  [vangheem]


5.0.15 (2019-10-02)
-------------------

- Provide workaround for asyncio contextvars ipython bug in shell
  [vangheem]


5.0.14 (2019-10-02)
-------------------

- Throw an `TransactionObjectRegistrationMismatchException` exception if you attempt to
  register an object with a transaction that is a different than existing registration
  for that object.
  [vangheem]


5.0.13 (2019-09-27)
-------------------

- Case insensitive environ `G_` variable lookup
  [svx]

- Improve reST syntax of README
  [svx]

- Fix typo in CHANGELOG
  [svx]

5.0.12 (2019-09-24)
-------------------

- Fix shut down for redis pubsub driver
  [vangheem]

- Swagger url support for X-Forwarded-Proto and X-Forwarded-Schema
  [bloodbare]


5.0.11 (2019-09-18)
-------------------

- Fix patch field delete to handle when value is None
  [vangheem]

- Adjust Sphinx to build in parallel
  [svx]


5.0.10 (2019-09-06)
-------------------

- Be able to use guillotina's types in 3rd party apps
  [vangheem]


5.0.9 (2019-09-05)
------------------

- Handle errors vacuuming
  [vangheem]


5.0.8 (2019-09-05)
------------------

- pypi package desc fix


5.0.7 (2019-09-05)
------------------

- Explicitly reset task vars on every request
  [vangheem]

- Fix futures execute error when no futures are defined for type
  [vangheem]


5.0.6 (2019-09-04)
------------------

- Fix `execute.clear_futures()`
  [vangheem]

- Adding Helm Charts
  [karannaoh]

5.0.4 (2019-09-04)
------------------

- Upgrade mypy
  [vangheem]

- Fix not setting cache values for updated object when push is not enabled
  [vangheem]

- Fix conflict error handling with registry objects
  [vangheem]

- Sorted imports in all files and added `isort` in .travis to keep the format
  [masipcat]


5.0.3 (2019-09-02)
------------------

- `BaseObject.__txn__` now weakref to prevent reference cycles
  [vangheem]

- Change default service registration to work without inline defined klass methods
  [vangheem]

- Fix doc builds for new open api 3
  [vangheem]

- Fix getting cache value from redis
  [vangheem]

- Fix calculating in-memory cache size
  [vangheem]

- Update Makefile [svx]
- Remove buildout bits [svx]

5.0.2 (2019-08-30)
------------------

- Fix json schema validation
  [vangheem]

- Fix memory cache to be able to calc size properly
  [vangheem]

- Better redis pubsub error handling
  [vangheem]


5.0.1 (2019-08-30)
------------------

- Be not log verbose when pubsub utility task is cancelled
  [vangheem]


5.0.0 (2019-08-30)
------------------

- Be able to configure cache to not push pickles with invalidation data
  [vangheem]

- Fix transaction handling to always get current active transaction, throw exception
  when transaction is closed and be able to refresh objects.
  [vangheem]

- More normalization of execute module with task_vars/request objects
  [vangheem]

- Allow committing objects that were created with different transaction
  [vangheem]

- Fix async utils to work correctly with transactions and context vars
  [vangheem]

- Be able to have `None` default field values
  [vangheem]


5.0.0a16 (2019-08-26)
---------------------

- Throw exception when saving object to closed transaction
  [vangheem]

- Fix cache key for SQLStatements cache. This was causing vacuuming on multi-db environments
  to not work since the vacuuming object was shared between dbs on guillotina_dynamictablestorage.
  [vangheem]

- Refractor and bug fix in validation of parameter

- Implement more optimized way to vacuum objects which dramatically improves handling
  of deleting very large object trees
  [vangheem]

- Fix `LightweightConnection` pg class to close active cursors when connection done
  [vangheem]

- Swagger doc for search endpoint
  [karannaoh]

- Fix `modification_date` not indexed when an object is patched
  [masipcat]

- Move to black code formatter
  [vangheem]

- Fix field.validate() crashes when providing invalid schema (for field of type Object)
  [masipcat]

- Upgrade to Swagger 3/Open API 3
  [karannaoh]

- Implement json schema validation
  [karannaoh]


5.0.0a15 (2019-08-02)
---------------------

- Dict schema serialization needs properties to be valid JSON Schema
  [bloodbare]

- Fix potential bug when working with multiple databases/transaction managers
  [vangheem]

- New `guillotina.fields.BucketDictField`
  [vangheem]

- New `@fieldvalue/{field name or dotted behavior + field name}` endpoint
  [vangheem]


5.0.0a14 (2019-07-30)
---------------------

- Leaking txn on reindex on pg
  [bloodbare]


5.0.0a13 (2019-07-29)
---------------------

- Run default factory on attributes on behaviors
  [bloodbare]

- Allow to get full object serialization on GET operation
  [bloodbare]

- Only register object for writing if base object changed. Otherwise, changes to behavior data
  was also causing writes to the object it was associated with
  [vangheem]

- Add `x-virtualhost-path` header support for url generation
  [vangheem]


5.0.0a12 (2019-07-26)
---------------------

- Make Tuple type work with patch field
  [vangheem]

- Make IDublinCore.tags a patch field
  [vangheem]

- Add `appendunique` and `extendunique` to patch field operations
  [vangheem]

- Fix exhausted retries conflict error response
  [vangheem]

- Make sure field name of patch field is set before using
  [vangheem]

- Improve request memory usage
  [vangheem]

- Fix: just skip indexing attributes from schemas that object does not
  adapt to [lferran]


5.0.0a11 (2019-07-22)
---------------------

- Allow to receive a fullobject serialization on search
  [bloodbare]

- Allow to reindex on PG catalog implementation
  [bloodbare]

- Read only txn can be reused without changing read only param
  [bloodbare]

- Merge CORS headers
  [qiwn]

- Fix redis pubsub potential cpu bound deadlock
  [vangheem]

- Make sure that channel is configured on cache pubsub
  [bloodbare]

- Handle cancelled error on cleanup
  [vangheem]

- Define TTL on cache set
  [bloodbare]

- Logging async util exception
  [bloodbare]

- Documentation improvements
  [vangheem]

- Cache JSONField schema validator object
  [vangheem]

- JSONField works with dict instead of requiring str(which is then converted to dict anyways)
  [vangheem]


5.0.0a10 (2019-06-27)
---------------------

- Adding store_json property on db configuration so we can disable json storage for each db.
  [bloodbare]


5.0.0a9 (2019-06-27)
--------------------

- Move guillotina_mailer to guillotina.contrib.mailer
  [bloodbare]

- Be able to customize the object reader function with the `object_reader` setting
  [vangheem]

- Fix indexing data potentially missing updated content when `fields` for accessor
  is not specified
  [vangheem]

- Executioner:
    - providing pagination support in navigation (1.2.0)
    - supporting token authentication from login form (1.3.0)
    - using @search endpoint to navigate in container items

- A few more python antipattern fixes [lferran]

5.0.0a8 (2019-06-23)
--------------------

- Aggregations in PG JSONb
  [bloodbare]

5.0.0a7 (2019-06-22)
--------------------

- Change `guillotina.files.utils.generate_key` to not accept a `request` parameter. It was
  used to get the container id which is now a context var.
  [vangheem]

- Add `IExternalFileStorageManager` interface to be able to designate a file storage that
  store a file into an external database. This enables you to automatically leverage the
  `redis` data manager.

- Add `cloud_datamanager` setting. Allows you to select between `db`(default) and
  `redis`(if `guillotina.contrib.redis` is used) to not write to db to maintain state.
  The `redis` option is only usable for gcloud and s3 adapters.

5.0.0a6 (2019-06-22)
--------------------

- Cache password checked decisions to fix basic auth support
  [vangheem]

- Make sure you can import contrib packages without automatically activating them
  [vangheem]

5.0.0a5 (2019-06-22)
--------------------
- Adding rediscache and pubsub logic. Now you can have memory cache, network cache with invalidation
  and pubsub service. `guillotina_rediscache` is not necessary any more.
  [bloodbare]


- deprecate `__local__properties__`. `ContextProperty` works on it's own now
  [vangheem]

- Add argon2 pw hashing
  [vangheem]

- Completely remove support for `utilities` configuration. Use `load_utilities`.
  [vangheem]

5.0.0a4 (2019-06-21)
--------------------

- Fix path__startswith query
  [vangheem]


5.0.0a3 (2019-06-21)
--------------------

- Add `guillotina.contrib.swagger`


5.0.0a2 (2019-06-19)
--------------------

- Missing mypy requirement
- Fix catalog interface
- Fix catalog not working with db schemas
- Update intro docs


5.0.0a1 (2019-06-19)
--------------------

- Fix events antipattern [lferran]

- Rename `utils.get_object_by_oid` to `utils.get_object_by_uid`

- Emit events for registry configuration changes

- Default catalog interface removes the following methods: `get_by_uuid`, `get_by_type`, `get_by_path`,
  `get_folder_contents`. Keep interfaces simple, use search/query.

- Allow modifying app settings from pytest marks [lferran]

- No longer setup fake request with login for base command

- Moved `ISecurityPolicy.cached_principals` to module level function `guillotina.security.policy.cached_principals`

- Moved `ISecurityPolicy.cached_roles` to module level function `guillotina.security.policy.cached_roles`

- `utils.get_authenticated_user_id` no longer accepts `request` param

- `utils.get_authenticated_user` no longer accepts `request` param

- Removed `guillotina.exceptions.NoInteraction`

- Removed `guillotina.interfaces.IInteraction`

- `auth_user_identifiers` no longer accept `IRequest` in the constructor. Use `utils.get_current_request`

- `auth_user_identifiers` no longer accept `IRequest` in constructor. Use `utils.get_current_request`

- Remove `IInteraction`. Use `guillotina.utils.get_security_policy()`

- Remove `Request._db_write_enabled`, `Transaction` now has `read_only` property

- Remove `Request._db_id`, Use `guillotina.task_vars.db.get().id`

- Remove `Request.container_settings`, Use `guillotina.utils.get_registry`

- Remove `Request._container_id`, use `guillotina.task_vars.container.get().id`

- Remove `Request.container`, Use `guillotina.task_vars.container.get()`

- Remove `Request.add_future`. Use `guillotina.utils.execute.add_future`

- Add `guillotina.utils.get_current_container`

- Rename `request_indexer` setting to `indexer`

- Rename `guillotina.catalog.index.RequestIndexer` to `guillotina.catalog.index.Indexer`

- Rename `IWriter.parent_id` to `IWriter.parent_uid`

- Rename `guillotina.db.oid` to `guillotina.db.uid`

- Rename `oid_generate` setting to `uid_generator`

- Rename `BaseObject._p_register` -> `BaseObject.register`

- Rename `BaseObject._p_serial` -> `BaseObject.__serial__`

- Rename `BaseObject._p_oid` -> `BaseObject.__uuid__`

- Rename `BaseObject._p_jar` -> `BaseObject.__txn__`

- separate transaction from request object

- rename `guillotina.transactions.managed_transaction` to `guillotina.transactions.transaction`
