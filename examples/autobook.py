import datetime

from htg import CondecoBooker


def main():
    booker = CondecoBooker()

    # Let's book the week a fortnight from now
    now = datetime.datetime.now()
    delta_days = 14 - now.weekday()
    monday_fortnight = now + datetime.timedelta(days=delta_days)

    for i in range(5):
        booker.book_desk(monday_fortnight + datetime.timedelta(days=i))


if __name__ == '__main__':
    main()
