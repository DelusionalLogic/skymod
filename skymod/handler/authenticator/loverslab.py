from ..sessionfactory import SessionFactory
from ..errors import AuthorizationError

import skymod.query as query


class LoversLab(SessionFactory):
    def __init__(self):
        self.isLogged = False
        super().__init__()

    def needs_login(self):
        return not self.isLogged

    def perform_login(self, config, headers):
        if self.isLogged:
            return
        self.isLogged = True

        if config.username == "":
            raise Exception(
                "Loverlab username wasn't set."
                "Please set ll.username and optionally ll.password"
            )
        username = config.username
        password = config.password
        if password == "":
            password = query.password("LoversLab password: ")

        session = super().getSession()

        data = {
            "ips_username": username,
            "ips_password": password,
            "rememberMe": 0,
            "auth_key": "880ea6a14ea49e853634fbdc5015a024"
        }
        r = session.post(
            "https://www.loverslab.com/index.php?app=core&module=global&section=login&do=process",  # noqa
            data=data,
            headers=headers
        )
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")
