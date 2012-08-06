#python
from captionstransformer import youtube
from captionstransformer.registry import REGISTRY as CAPTION_REGISTRY

#zope
from zope import component
from zope import interface
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.formlib import form
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

#plone
from plone.portlet.static import PloneMessageFactory as _p
from plone.portlets.interfaces import IPortletDataProvider, IPortletRetriever
from plone.app.portlets.portlets import base

from collective.videoanysurfer.video import IVideoExtraData
from collective.portlet.videoanysurfer import VideoPortletMessageFactory as _
from collective.videoanysurfer.browser.link_view import VideoCaptions

PORTLET_PATH = "%(context_path)s/++%(category)sportlets++%(manager)s/%(id)s"


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

    update_youtube = schema.Bool(title=_(u"Update captions from youtube"),
                description=_(u"This will download the caption from youtube"),
                default=True)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    interface.implements(IVideoPortlet)

    header = u""
    video_url = u""
    captions = u""
    captions_format = u"TTML"
    transcription = u""
    download_url = u""
    omit_border = False
    update_youtube = True

    def __init__(self, header=u"", video_url=u"", captions=u"",
                 captions_format=u"",
                 transcription=u"", download_url=u"",
                 update_youtube=False):
        self.header = header
        self.video_url = video_url
        self.captions = captions
        self.captions_format = captions_format
        self.transcription = transcription
        self.download_url = download_url
        self.update_youtube = update_youtube
#        self.omit_border = omit_border

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

    _render = ViewPageTemplateFile('videoportlet.pt')
    def __init__(self, context, request, view, manager, data):
        super(Renderer, self).__init__(context, request, view, manager, data)
        self.portlet_url = None
        self.portal_state = None
        self.portal_url = None
        self.portal_path = None

    def render(self):
        self.update()
        return self._render()

    def update(self):
        if not self.portal_state:
            self.portal_state = component.getMultiAdapter((self.context,
                                                           self.request),
                                           name="plone_portal_state")
        if not self.portal_url:
            self.portal_url = self.portal_state.portal_url()

        if self.portal_path is None:
            portal = self.portal_state.portal()
            self.portal_path = '/'.join(portal.getPhysicalPath())

        if self.portlet_url is None:
            #http://stackoverflow.com/questions/11211134/how-do-i-get-the-kind-of-portlet-group-context-type-from-its-renderer-in-pl/11211893#11211893
            retriever = component.getMultiAdapter((self.context, self.manager),
                                                  IPortletRetriever)
            category = None
            for info in retriever.getPortlets():
                if info['assignment'] is self.data.aq_base:
                    category = info['category']
                    key = info['key']
                    break
            if category is not None:
                path = key[len(self.portal_path)+1:]
                info = {'category': category,
                        'id': '%s' % self.data.id,
                        'manager': self.manager.__name__,
                        'context_path': path}
                self.portlet_url = '%s/%s' % (self.portal_url, 
                                              PORTLET_PATH % info)

    def captions_url(self):
        if not self.data.captions:
            return
        return '%s/@@video_captions' % self.portlet_url

    def transcription_url(self):
        if not self.data.transcription:
            return
        return '%s/@@video_transcription' % self.portlet_url


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IVideoPortlet)

    def create(self, data):

        if data.get('update_youtube'):
            # download captions:
            language = self.get_language()
            reader = youtube.get_reader(data.get('video_url'), language)
            if reader:
                reader.read()
                data['captions'] = reader.rawcontent
                data['captions_format'] = 'transcript'

        return Assignment(**data)

    def get_language(self):
        return 'fr'


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IVideoPortlet)
#        form = self.request.form
#        if not form['captions']:
#            form['captions'] = download_youtube_captions(form['video_url'])
#            form['captions_format'] = 'transcript'
#
#        return super(EditForm, self).__call__()


def modify_portlet_handler(ob, event):
    if ob.update_youtube:
        language = 'en'
        reader = youtube.get_reader(ob.video_url, language)
        if reader:
            reader.read()
            ob.captions = reader.rawcontent
            ob.captions_format = 'transcript'


class CaptionsView(VideoCaptions):
    """View to get captions for the portlet"""


class PortletVideoExtraData(object):
    """Implement IVideoExtraData for portlet Assignement"""
    interface.implements(IVideoExtraData)

    def __init__(self, context):
        self.context = context

    def update(self):
        pass

    @property
    def captions(self):
        return self.context.captions

    @property
    def transcription(self):
        return self.context.transcription

    @property
    def download_url(self):
        return self.context.download_url

    @property
    def captions_format(self):
        captions_format = self.context.captions_format
        if captions_format:
            return CAPTION_REGISTRY[captions_format]


class TranscriptionView(BrowserView):
    """View to display transcription"""

    index = ViewPageTemplateFile('transcription.pt')

    def __call__(self):
        self.request['ajax_load'] = True
        return self.index()

    def transcription(self):
        return self.context.transcription
