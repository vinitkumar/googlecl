import os
import httplib2
import threading
from gdata.photos.service import *
import gdata.media
from datetime import timedelta, datetime
import gdata.geo
from oauth2client import client


class Authenticate(object):
    def __init__(self):
        self.config_filename = '.googlecl.conf'

    def oauthLogin(self):
        from oauth2client.file import Storage
        filename = os.path.join(os.path.expanduser('~'), self.config_filename)
        storage = Storage(filename)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json',
                                                  scope='https://picasaweb.google.com/data/',
                                                  redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            auth_uri = flow.step1_get_authorize_url()
            print 'Authorization_URL: %s' % auth_uri
            auth_code = raw_input('Enter the auth code: ')
            credentials = flow.step2_exchange(auth_code)
            storage.put(credentials)
        return self.refreshCreds(credentials, 0)

    def refreshCreds(self, credentials, sleep):
        global gd_client    
        time.sleep(sleep)
        credentials.refresh(httplib2.Http())    

        now = datetime.utcnow() 
        expires = credentials.token_expiry
        expires_seconds = (expires-now).seconds     
        # print ("Expires %s from %s = %s" % (expires,now,expires_seconds) )

        gd_client = gdata.photos.service.PhotosService(email='default', additional_headers={'Authorization': 'Bearer %s' % credentials.access_token})

        d = threading.Thread(name='refreshCreds', target=self.refreshCreds, args=(credentials,expires_seconds - 10) )
        d.setDaemon(True)
        d.start()
        return gd_client


def main():
    auth = Authenticate()
    gd_client = auth.oauthLogin()
    webAlbums = gd_client.GetUserFeed(user='vinitcool76')
    for webalbum in webAlbums.entry:
        print webalbum.title.text


if __name__ == '__main__':
    main()