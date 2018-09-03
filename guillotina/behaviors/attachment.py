from guillotina import configure
from guillotina.fields import CloudFileField
from zope.interface import Interface


class IAttachmentMarker(Interface):
    """Marker interface for content with attachments."""


@configure.behavior(
    title="Attachment behavior",
    marker=IAttachmentMarker,
    for_="guillotina.interfaces.IResource",
    alias="attachment")
class IAttachment(Interface):
    file = CloudFileField()
