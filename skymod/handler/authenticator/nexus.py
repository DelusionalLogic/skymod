from ..sessionfactory import SessionFactory
from ..errors import AuthorizationError

import skymod.query as query


class Nexus(SessionFactory):
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
                "Nexus username wasn't set."
                "Please set nexus.username and optionally nexus.password"
            )
        username = config.username
        password = config.password
        if password == "":
            password = query.password("Nexus password: ")

        session = super().getSession()

        r = session.post(
            "http://www.nexusmods.com/skyrim/sessions/?Login",
            params={"username": username, "password": password},
            headers=headers
        )
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")

        r = session.get(
            "http://www.nexusmods.com/skyrim/Core/Libs/Flamework/Entities/User",  # noqa
            params={"GetCredentials": ""},
            allow_redirects=True,
            headers=headers
        )
        if r.status_code != 200:
            raise AuthorizationError(
                "Failed getting credentials (How did that happen?)"
            )
