from datetime import datetime
from guillotina import schema
from guillotina.schema.interfaces import IObject
from typing import AsyncIterator, List, Optional, Tuple
from zope.interface import Interface, Attribute


class IUploadDataManager(Interface):
    """
    Interface to manage upload data
    """

    async def load():  # type: ignore
        """
        Load the current upload status
        """

    async def update(**kwargs):
        """
        update file upload data
        """

    async def finish():  # type: ignore
        """
        finish upload
        """

    async def save():  # type: ignore
        """
        save any current operations to db
        """

    async def get(name):
        """
        get attribute
        """

    async def get_offset():  # type: ignore
        """
        get current upload offset
        """


class IFileStorageManager(Interface):
    """
    Manage storing file data
    """

    async def start(dm: IUploadDataManager):
        """
        start upload
        """

    async def iter_data() -> AsyncIterator[bytes]:
        """
        iterate through data in file
        """

    async def range_supported() -> bool:
        """
        If range is supported with manager
        """

    async def read_range(start: int, end: int) -> AsyncIterator[bytes]:
        """
        Iterate through ranges of data
        """

    async def append(data):
        """
        append data to the file
        """

    async def finish():  # type: ignore
        """
        finish upload
        """

    async def copy(dm, other_storage_manager: IUploadDataManager, other_dm: IUploadDataManager):
        """
        copy file to another file
        """


class IExternalFileStorageManager(IFileStorageManager):
    """
    File manager that uses database to store upload state
    """


class IFileManager(Interface):
    """Interface to create uploaders and downloaders."""

    async def upload():  # type: ignore
        """
        Upload complete file in one shot
        """

    async def download():  # type: ignore
        """
        Download file
        """

    async def tus_post():  # type: ignore
        """
        Start tus upload process
        """

    async def tus_patch():  # type: ignore
        """
        Upload part of file
        """

    async def tus_options():  # type: ignore
        """
        Get tus supported version
        """

    async def tus_head():  # type: ignore
        """
        Get current tus status
        """

    async def iter_data():  # type: ignore
        """
        Return an async iterator of the file
        """

    async def save_file(generator):
        """
        Save data to a file from an async generator
        """

    async def copy(other_manager):
        """
        Copy current file to new one
        """

    async def delete():
        """
        Delete the file
        """


class IBlobMetadata(Interface):

    name: str = Attribute("""The key used to access the file""")
    createdTime: datetime = Attribute("""The date the file was created""")
    size: int = Attribute("""The size of the file in bytes""")
    bucket: str = Attribute("""The bucket the file is located in""")


class IBlobVacuum(Interface):
    async def get_blobs(
        page_token: Optional[str] = None, prefix=None, max_keys=1000
    ) -> Tuple[List[IBlobMetadata], str]:
        """
        Get a page of files from the bucket
        """

    async def delete_blobs(keys: List[str], bucket_name: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """
        Deletes a batch of files.  Returns successful and failed keys.
        """

    async def delete_bucket(bucket_name: Optional[str] = None):
        """
        Delete the given bucket
        """


class IFileCleanup(Interface):
    def __init__(context):
        """
        adapter of ob file is on
        """

    def should_clean(**kwargs):
        """
        whether or not old file should be cleaned
        """


class IFileNameGenerator(Interface):
    """
    Name generator for a file
    """


class IFile(Interface):

    content_type = schema.TextLine(
        title="Content Type",
        description="The content type identifies the type of data.",
        default="",
        required=False,
    )

    filename = schema.TextLine(title="Filename", required=False, default=None)

    extension = schema.TextLine(title="Extension of the file", default="", required=False)

    md5 = schema.TextLine(title="MD5", default="", required=False)

    size = schema.Int(title="Size", default=0)


# File Field


class IFileField(IObject):
    """Field for storing IFile objects."""


class ICloudFileField(IObject):
    """Field for storing generic cloud File objects."""


class IDBFileField(ICloudFileField):
    """
    Store files in database blob storage
    """


class IDBFile(IFile):
    """Marker for a DBFile"""
