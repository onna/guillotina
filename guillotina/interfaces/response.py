from zope.interface import Attribute
from zope.interface import Interface


class IResponse(Interface):
    status_code = Attribute("status code")
    content = Attribute("content")
    headers = Attribute("headers")

    def __init__(*, content: dict = {}, headers: dict = {}, status: int = None):  # type: ignore
        """
        """


class IAioHTTPResponse(Interface):
    """
    Mark aiohttp responses with interface
    """
