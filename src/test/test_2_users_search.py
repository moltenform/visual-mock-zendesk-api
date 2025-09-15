from test_helpers import *


def go2UsersSearch():
    ############## No results ###################
    result = sendGet('/api/v2/users/search', 'query=email:utest444@a.com')
    assertEq(0, result['count'])
    assertEq(0, len(result['users']))

    ############## One result ###################
    result = sendGet('/api/v2/users/search', 'query=email:utest3@a.com')
    assertEq(1, result['count'])
    assertEq(1, len(result['users']))
    assertTrue(int(result['users'][0]['id']) > 0)
    assertEq('utest3', result['users'][0]['name'])
    assertEq('utest3@a.com', result['users'][0]['email'])
