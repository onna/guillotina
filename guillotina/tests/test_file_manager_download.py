from guillotina.files.manager import FileManager
from guillotina.response import HTTPClientClosedRequest
from unittest import mock

import aiohttp
import logging
import pytest


def _file_manager(range_header, transport, read_error=None, write_error=None):
    manager = FileManager.__new__(FileManager)
    manager.context = mock.MagicMock()
    manager.field = mock.MagicMock()
    manager.field.get.return_value = mock.MagicMock(size=1024 * 1024)
    manager.request = mock.MagicMock(
        headers={"Range": range_header} if range_header else {}, transport=transport
    )

    async def data(*args, **kwargs):
        yield b"0" * 1024
        if read_error is not None:
            raise read_error
        yield b"0" * 1024

    manager.file_storage_manager = mock.MagicMock(
        iter_data=data, read_range=data, range_supported=mock.AsyncMock(return_value=True)
    )

    download_resp = mock.MagicMock()
    download_resp.write = mock.AsyncMock(side_effect=write_error)
    download_resp.drain = mock.AsyncMock()
    download_resp.write_eof = mock.AsyncMock()
    manager.prepare_download = mock.AsyncMock(return_value=download_resp)
    return manager


@pytest.mark.parametrize("range_header", [None, "bytes=0-"])
@pytest.mark.parametrize(
    "write_error",
    [ConnectionError("Connection lost"), ConnectionResetError("Cannot write to closing transport")],
)
async def test_download_client_disconnect_is_a_cancel(range_header, write_error, caplog):
    caplog.set_level(logging.INFO)
    manager = _file_manager(range_header, transport=None, write_error=write_error)

    with pytest.raises(HTTPClientClosedRequest):
        await manager.download()

    assert any("cancelled" in record.getMessage() for record in caplog.records)
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.parametrize("range_header", [None, "bytes=0-"])
async def test_download_storage_error_closes_connection(range_header):
    transport = mock.MagicMock()
    error = aiohttp.ClientPayloadError("storage read failed")
    manager = _file_manager(range_header, transport=transport, read_error=error)

    with pytest.raises(aiohttp.ClientPayloadError):
        await manager.download()

    transport.close.assert_called_once()


@pytest.mark.parametrize("range_header", [None, "bytes=0-"])
async def test_download_storage_error_after_client_left_is_not_a_cancel(range_header, caplog):
    caplog.set_level(logging.INFO)
    error = aiohttp.ClientPayloadError("storage read failed")
    manager = _file_manager(range_header, transport=None, read_error=error)

    with pytest.raises(aiohttp.ClientPayloadError):
        await manager.download()

    assert not any("cancelled" in record.getMessage() for record in caplog.records)
