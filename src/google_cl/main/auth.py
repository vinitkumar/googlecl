from __future__ import annotations


import logging
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session

from pathlib import Path
from urllib3.util.retry import Retry

from typing import Optional

from json import load, dump, JSONDecodeError


log = logging.getLogger(__name__)

# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_uri = "https://www.googleapis.com/oauth2/v4/token"


class Authorize:
    def __init__(
            self,
            scope: list[str],
            token_file: Path,
            secrets_file: Path,
            max_retries: int = 5,
    ):
        self.max_retries = max_retries
        self.scope: list[str] = scope
        self.token_file: Path = token_file
        self.session = None
        self.token = None

        try:
            with secrets_file.open("r") as stream:
                all_json = load(stream)
            secrets = all_json["installed"]
            self.client_id = secrets["client_id"]
            self.client_secret = secrets["client_secret"]
            self.redirect_uri = secrets["redirect_uri"][0]
            self.token_uri = secrets["token_uri"]
            self.extra = {
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        except (JSONDecodeError, IOError):
            print(f"Missing or bad secrets file: {secrets_file}")


    def load_token(self) -> Optional[str]:
        try:
            with self.token_file.open("r") as stream:
                token = load(stream)

        except (JSONDecodeError, IOError):
            return None
        return token

    def save_token(self, token: str):
        with self.token_file.open("w") as stream:
            dump(token, stream)
        self.token_file.chmod(0o600)


    def authorize(self):
        token = self.load_token()
        if token:
            self.session = OAuth2Session(
                self.client_id,
                token=token,
                auto_refresh_url=self.token_uri,
                auto_refreh_kwargs=self.extra,
                token_update=self.save_token,
            )
        else:
            self.session = OAuth2Session(
                self.client_id,
                scope=self.scope,
                redirect_uri=self.redirect_uri,
                auto_refresh_url=self.token_uri,
                auto_refreh_kwargs=self.extra,
                token_update=self.save_token,
            ) 
            authorization_url, _ = self.session.authorization_url(
                authorization_base_url,
                access_type="offline",
                prompt="select_account",
            )
            print(f"Please go here and authorize, {authorization_url}\n", )

            # Get the authorization verifier code from the callback url
            response_code = input("Paste the response token here:\n")

            # Fetch the access token
            self.token = self.session.fetch_token(
                self.token_uri, client_secret=self.client_secret, code=response_code
            )
            self.save_token(self.token)

        # set up the retry bevaiour for the authorized session
        retries = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        # apply the retry behaviour to our session by repalcing the default HTTPAdapter
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

