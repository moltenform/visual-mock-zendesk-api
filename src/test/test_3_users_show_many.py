from test_helpers import *


def go3UsersShowMany():
    ############## No results ###################
    result = sendGet('/api/v2/users/show_many', f'ids=999')
    sortResultsByOurNumber(result, stateIds, 'users')
    assertEq(0, len(result['users']))

    ############## One result ###################
    result = sendGet('/api/v2/users/show_many', f'ids={stateIds["user1"]}')
    sortResultsByOurNumber(result, stateIds, 'users')
    assertEq(1, len(result['users']))
    assertEq(stateIds["user1"], result['users'][0]['id'])
    assertEq('utest1', result['users'][0]['name'])
    assertEq('utest1@a.com', result['users'][0]['email'])

    ############## Many results, skip missing ###################
    result = sendGet('/api/v2/users/show_many', f'ids={stateIds["user2"]},999,{stateIds["user3"]}')
    sortResultsByOurNumber(result, stateIds, 'users')
    assertEq(2, len(result['users']))
    assertEq(stateIds["user2"], result['users'][0]['id'])
    assertEq('utest2', result['users'][0]['name'])
    assertEq('utest2@a.com', result['users'][0]['email'])
    assertEq(stateIds["user3"], result['users'][1]['id'])
    assertEq('utest3', result['users'][1]['name'])
    assertEq('utest3@a.com', result['users'][1]['email'])
