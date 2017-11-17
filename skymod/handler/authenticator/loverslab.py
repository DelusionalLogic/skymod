# Copyright 2017 Jesper Jensen (delusionallogic)
#
# This file is part of skymod.
#
# skymod is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# skymod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with skymod.  If not, see <http://www.gnu.org/licenses/>.
from ..sessionfactory import SessionFactory
from ..errors import AuthorizationError

import skymod.query as query
from bs4 import BeautifulSoup as soup


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

        # Get CSRF token
        r = session.get("https://www.loverslab.com/")
        s = soup(r.content, "lxml")

        formTag = s.find("div", attrs={"data-role": "loginForm"})
        csrfTag = formTag.find("input", attrs={"name": "csrfKey"})
        csrfToken = csrfTag["value"]

        data = {
            "login__standard_submitted": 1,
            "auth": username,
            "password": password,
            "remember_me": 0,
            "remember_me_checkbox": 0,
            "signin_anonumouns": 1,
            "csrfKey": csrfToken,
        }
        r = session.post(
            "https://www.loverslab.com/login/",
            data=data,
            headers=headers
        )
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")
