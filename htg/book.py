from datetime import datetime, timedelta, timezone
from tarfile import data_filter
from unittest.mock import Base

import requests
import urllib3.util
from bs4 import BeautifulSoup

from htg.settings import Settings


class CondecoBooker:
    """ """

    TIMEOUT = (5, 9)

    ENV_USER = 'ENGAGE_USER'
    ENV_PASSWORD = 'ENGAGE_PASSWORD'

    def __init__(self):
        # Load in our settings from .env or .env.prod
        self.settings = Settings()  # type: ignore
        self.host = self.settings.HOST

        # These will get populated at login time
        self.user_id: str | None = None
        self.user_full_name: str | None = None
        self.user_id_long: str | None = None

        # Create a new web session
        self.session = requests.Session()
        self.session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0'}
        )

        self.login(self.host, self.settings.USER_EMAIL, self.settings.USER_PWD)

    def login(self, host: str, username: str, password: str):
        # -- Login request for ASP.session
        r = self.session.get(f'https://{host}/login/login.aspx')

        soup = BeautifulSoup(r.text, 'html.parser')

        view_state = soup.find('input', {'name': '__VIEWSTATE'})['value']
        view_stategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
        event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

        payload = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': view_state,
            '__VIEWSTATEGENERATOR': view_stategen,
            '__EVENTVALIDATION': event_validation,
            'txtUserName': username,
            'txtPassword': password,
            'btnLogin': 'Sign-in',
        }
        response = self.session.post(
            url=f'https://{host}/login/login.aspx',
            data=payload,
        )
        print('Login response:', response.status_code)
        print(response.cookies.get_dict())
        print(self.session.cookies.get_dict())

        # Fetch our user id, user full name and user id long
        self.user_id = response.text.split('var int_userID = ')[-1].split(';')[0]
        self.user_full_name = response.text.split('var userFullName = ')[-1].split(';')[0]
        self.user_id_long = self.session.cookies.get('CONDECO').split('=')[-1]
        print(f'Fetched user id of: {self.user_id}')
        print(f'Fetched user full name of: {self.user_full_name}')
        print(f'Fetched user id long: {self.user_id_long}')

        # -- Enterprise Lite Login
        response = self.session.get(url=f'https://{host}/EnterpriseLiteLogin.aspx')
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find('input', {'name': 'token'})['value']
        print(f'Found token: {token}')
        print('EnterpriseLiteLogin', response.status_code)
        print(response.cookies.get_dict())

        # Auth page next

        now = datetime.now(timezone.utc)
        request_datetime = now.isoformat(timespec='milliseconds')
        data = {
            'token': token,  # or extract JWT if in page/response
            'requestDateTime': request_datetime.split('+')[0] + 'Z',
            'requestTimeZoneOffset': '-600',
        }

        response = self.session.post(
            url=f'https://{host}/enterpriselite/auth',
            data=data,
            allow_redirects=True,
        )
        print(response.status_code)
        print(self.session.cookies.get_dict())

        # Get the EliteSession cookie from the session
        elite_session_cookie = self.session.cookies.get('EliteSession')

        if not elite_session_cookie:
            raise RuntimeError('EliteSession cookie was not retrieved.')
        self.session.headers['Authorization'] = f'Bearer {elite_session_cookie}'

    def book_desk(self, dates: list[str]):
        payload = {
            'UserID': self.user_id,
            'countryID': '3',
            'locationID': '12',
            'groupID': '61',
            'datesRequested': [f'{date}_0;{date}_1;' for date in dates],
            'generalForm': 'fkUserID~¬firstName~¬lastName~¬company~¬emailAddress~¬telephone~¬isExternal~0¬notifyByPhone~0¬notifyByEmail~0¬notifyBySMS~',
            'bookingID': '0',
            'resourceItemID': '2383',  # desk 69
            'UserLongID': self.user_id_long,
            'CultureCode': 'en-GB',
            'LanguageID': '1',
            'BookingSource': '1',
            'ValidateBooking': 'True',
            'IsSwap': 0,
        }

        # Send the desk booking request.
        response = self.session.post(
            url=f'https://{self.host}/webapi/BookingService/SaveDeskBooking',
            data=payload,
            timeout=CondecoBooker.TIMEOUT,
        )

        # Return the response.
        print(response.status_code)
        print(response.headers)
        # print(response.headers)
        return response
