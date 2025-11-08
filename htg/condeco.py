import json
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from htg.settings import Settings


class CondecoBooker:
    """ """

    TIMEOUT = (5, 9)  # (connect timeout, read timeout)

    def __init__(self, logger: logging.Logger | None = None):
        # Load in our settings from .env or .env.prod
        self.settings = Settings()  # type: ignore
        self.host = self.settings.HOST

        # Create out logger
        self.logger = logging.getLogger(__name__) if logger is None else logger

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
        self.logger.info(f'ATTEMPTING LOGIN TO {host} as {username}')

        # -- Login request for ASP.session
        r = self.session.get(f'https://{host}/login/login.aspx')

        soup = BeautifulSoup(r.text, 'html.parser')

        try:
            # ignore typing as we are handling error at runtime
            view_state = soup.find('input', {'name': '__VIEWSTATE'})['value']  # pyright: ignore[reportOptionalSubscript]
            view_stategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']  # pyright: ignore[reportOptionalSubscript]
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']  # pyright: ignore[reportOptionalSubscript]

        except TypeError:
            self.logger.exception('Failed to login')
            return

        self.logger.info(f'Parsed __VIEWSTATE: {view_state}')
        self.logger.info(f'Parsed __VIEWSTATESTATEGENERATOR: {view_stategen}')
        self.logger.info(f'Parsed __EVENTVALIDATION: {event_validation}')

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

        # Fetch our user id, user full name and user id long
        try:
            # ignore typing as we are handling error at runtime
            self.user_id = response.text.split('var int_userID = ')[-1].split(';')[0]  # pyright: ignore[reportOptionalSubscript]
            self.user_full_name = response.text.split('var userFullName = ')[-1].split(';')[0]  # pyright: ignore[reportOptionalSubscript]
            self.user_id_long = self.session.cookies.get('CONDECO').split('=')[-1]  # pyright: ignore[reportOptionalMemberAccess, reportOptionalSubscript]

        except TypeError:
            self.logger.exception('Failted to fetch user data')
            return

        self.logger.info(f'FETCHED user id: {self.user_id}')
        self.logger.info(f'FETCHED user full name: {self.user_full_name}')
        self.logger.info(f'FETCHED user id long: {self.user_id_long}')

        # -- Enterprise Lite Login
        self.logger.info('ATTEMPTING FETCH EnterpriseLite token...')

        response = self.session.get(url=f'https://{host}/EnterpriseLiteLogin.aspx')
        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            token = soup.find('input', {'name': 'token'})['value']  # pyright: ignore[reportOptionalSubscript]

        except TypeError:
            self.logger.exception('Failed to fetch EnterpriseLite token')
            return

        self.logger.info('Fetched EnterpriseLite token')

        # Auth page next
        self.logger.info('ATTEMPTING to fetch EliteSession token...')
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

        # Get the EliteSession cookie from the session
        elite_session_cookie = self.session.cookies.get('EliteSession')

        if not elite_session_cookie:
            self.logger.error('Login Failed: Unable to retrieve EliteSession cookie')
            return

        self.session.headers['Authorization'] = f'Bearer {elite_session_cookie}'
        self.logger.info('FOUND EliteSession token')

    def get_bookings(self, date: datetime) -> dict:
        payload = {
            'CountryId': '3',
            'LocationId': '12',
            'GroupId': '61',
            'FloorId': '12',
            'WStypeId': '2',
            'UserLongId': self.user_id_long,
            'UserId': self.user_id,
            'ViewType': '2',
            'LanguageId': '1',
            'ResourceType': '128',
            'StartDate': f'{date.strftime("%Y-%M-%d")}T00:00:00',
        }

        self.logger.info('Fetching bookings')
        response = self.session.post(
            url=f'https://{self.host}/webapi/BookingGrid/GetFilteredBookings',
            data=payload,
            timeout=CondecoBooker.TIMEOUT,
        )

        bookings = json.loads(response.text)

        return bookings

    def get_user_bookings(self, date: datetime) -> list[dict]:
        user_bookings = []
        bookings = self.get_bookings(date)
        for booking in bookings['Meetings']:
            if booking['AdditionalInfo']['FullName'] == self.user_full_name:
                user_bookings.append(booking)
        return user_bookings

    def book_desk(self, date: datetime, resourceitem_id: str = '2383'):  # desk 69...
        date_string = date.strftime('%d/%m/%Y')
        payload = {
            'UserID': self.user_id,
            'countryID': '3',
            'locationID': '12',
            'groupID': '61',
            'datesRequested': f'{date_string}_0;{date_string}_1;',
            'generalForm': 'fkUserID~¬firstName~¬lastName~¬company~¬emailAddress~¬telephone~¬isExternal~0¬notifyByPhone~0¬notifyByEmail~0¬notifyBySMS~',
            'bookingID': '0',
            'resourceItemID': resourceitem_id,
            'UserLongID': self.user_id_long,
            'CultureCode': 'en-GB',
            'LanguageID': '1',
            'BookingSource': '1',
            'ValidateBooking': 'True',
            'IsSwap': 0,
        }

        self.logger.info(f'Attempting to book desk {resourceitem_id}')

        # Send the desk booking request.
        response = self.session.post(
            url=f'https://{self.host}/webapi/BookingService/SaveDeskBooking',
            data=payload,
            timeout=CondecoBooker.TIMEOUT,
        )

        # TODO: Check our booking was actually successful

        return response
