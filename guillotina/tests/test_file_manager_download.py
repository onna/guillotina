from guillotina.files.manager import FileManager
from guillotina.response import HTTPClientClosedRequest
from unittest import mock

import logging
import pytest


def _file_manager(range_header, transport):
    manager = FileManager.__new__(FileManager)
    manager.context = mock.MagicMock()
    manager.field = mock.MagicMock()
    manager.field.get.return_value = mock.MagicMock(size=1024 * 1024)
    manager.request = mock.MagicMock(
        headers={"Range": range_header} if range_header else {}, transport=transport
    )

    async def data(*args, **kwargs):
        yield b"0" * 1024

    manager.file_storage_manager = mock.MagicMock(
        iter_data=data, read_range=data, range_supported=mock.AsyncMock(return_value=True)
    )

    download_resp = mock.MagicMock()
    download_resp.write = mock.AsyncMock(side_effect=ConnectionError("Connection lost"))
    download_resp.drain = mock.AsyncMock()
    download_resp.write_eof = mock.AsyncMock()
    manager.prepare_download = mock.AsyncMock(return_value=download_resp)
    return manager


@pytest.mark.parametrize("range_header", [None, "bytes=0-"])
async def test_download_client_gone_is_a_cancel(range_header, caplog):
    caplog.set_level(logging.INFO)
    manager = _file_manager(range_header, transport=None)

    with pytest.raises(HTTPClientClosedRequest):
        await manager.download()

    assert any("cancelled" in record.getMessage() for record in caplog.records)
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.parametrize("range_header", [None, "bytes=0-"])
async def test_download_write_error_with_client_connected_closes_connection(range_header):
    transport = mock.MagicMock()
    manager = _file_manager(range_header, transport=transport)

    with pytest.raises(ConnectionError):
        await manager.download()

    transport.close.assert_called_once()
