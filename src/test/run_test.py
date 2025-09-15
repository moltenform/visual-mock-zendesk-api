from test_helpers import *
from test_1_users_create_many import *
from test_2_users_search import *
from test_3_users_show_many import *
from test_4_tickets_create_many import *
from test_5_tickets_show_many import *
from test_6_tickets_show_comments import *
from test_7_tickets_update_many import *
from test_8_search import *


def go():
    setupStateIds()
    go1UsersCreateMany()
    go2UsersSearch()
    go3UsersShowMany()
    go4TicketsCreateMany()
    go5TicketsShowMany()
    go6TicketsShowComments()
    go7TicketsUpdateMany()
    go8Search()
    trace('\n\nall tests complete')


if __name__ == '__main__':
    go()
