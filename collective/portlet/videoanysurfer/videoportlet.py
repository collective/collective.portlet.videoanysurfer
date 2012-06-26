from zope import interface
from zope import schema

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from zope.formlib import form

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collective.videoanysurfer.video import IVideoExtraData
from collective.portlet.videoanysurfer import VideoPortletMessageFactory as _


class IVideoPortlet(IPortletDataProvider, IVideoExtraData):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    video_url = schema.URI(
        title=_(u"Video URL"),
        description=_(u"An URL from youtube"),
        required=True)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    interface.implements(IVideoPortlet)

    header = u""
    video_url = u""
    captions = u""
    transcription = u""
    download_url = u""

    def __init__(self, header=u"", video_url=u"", captions=u"",
                 transcription=u"", download_url=u""):
        self.header = header
        self.video_url = video_url
        self.captions = captions
        self.transcription = transcription
        self.download_url = download_url

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen. Here, we use the title that the user gave.
        """
        return self.header


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('videoportlet.pt')

    def captions_url(self):
        import pdb;pdb.set_trace()

    def transcription_url(self):
        pass


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IVideoPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IVideoPortlet)
