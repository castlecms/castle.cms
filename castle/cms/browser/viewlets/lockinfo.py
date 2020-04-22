from plone.locking.browser.info import LockInfoViewlet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class CastleCMSLockInfo(LockInfoViewlet):
    
    template = ViewPageTemplateFile("../templates/info.pt")
