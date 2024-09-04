from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.units import cm


class CustomDocTemplate(BaseDocTemplate):

    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        template = PageTemplate('normal', [Frame(.5*cm, 1.5*cm, 20*cm, 27.5*cm, id='F1')])
        self.addPageTemplates(template)

    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if flowable.__class__.__name__ == 'Paragraph':
            style = flowable.style.name
            if style == 'h1':
                text = flowable.getPlainText()
                key = 'h1-%s' % self.seq.nextf('h1')
                self.canv.bookmarkPage(key)
                self.notify('TOCEntry', (0, text, self.page, key))






