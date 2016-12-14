import os
import httplib2
import threading
import time
from gdata.photos.service import PhotosService
from gdata.docs.service import DocsService
from gdata.blogger.service import BloggerService
from gdata.contacts.service import  ContactsService
from gdata.calendar.service import CalendarService
from gdata.finance.service import FinanceService
from gdata.youtube.service import YouTubeService
from datetime import timedelta, datetime
from oauth2client import client


class Authenticate(object):
    def __init__(self, service):
        self.config_filename = '.googlecl.conf'
        self.service = service

    def oauth_login(self):
        from oauth2client.file import Storage
        filename = os.path.join(os.path.expanduser('~'), self.config_filename)
        storage = Storage(filename)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json',
                                                  scope='https://picasaweb.google.com/data/ https://www.googleapis.com/auth/drive https://docs.google.com/feeds/' ,
                                                  redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            auth_uri = flow.step1_get_authorize_url()
            print 'Authorization_URL: %s' % auth_uri
            auth_code = raw_input('Enter the auth code: ')
            credentials = flow.step2_exchange(auth_code)
            storage.put(credentials)
        return self.refresh_creds(credentials, 0)

    def refresh_creds(self, credentials, sleep):
        global gd_client
        time.sleep(sleep)
        credentials.refresh(httplib2.Http())

        now = datetime.utcnow()
        expires = credentials.token_expiry
        expires_seconds = (expires-now).seconds
        # print ("Expires %s from %s = %s" % (expires,now,expires_seconds) )
        if self.service == 'docs':
            gd_client = DocsService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'picasa':
            gd_client = PhotosService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'finance':
            gd_client = FinanceService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'calendar':
            gd_client = CalendarService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'contacts':
            gd_client = ContactsService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'youtube':
            gd_client = YouTubeService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })
        elif self.service == 'blogger':
            gd_client = BloggerService(email='default', additional_headers={
                'Authorization': 'Bearer %s' % credentials.access_token
            })

        d = threading.Thread(name='refresh_creds', target=self.refresh_creds, args=(credentials,expires_seconds - 10) )
        d.setDaemon(True)
        d.start()
        return gd_client
