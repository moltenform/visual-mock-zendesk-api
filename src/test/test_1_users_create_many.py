from test_helpers import *


def go1UsersCreateMany():
    if not getInputBool('OK to run this test, which will reset all tickets+users?'):
        assertTrue(False, 'cancelling test')

    ############## Reset state ###################
    sendPost('/api/delete_all', {})

    ############## Invalid input ###################
    # cannot set id
    s = r'''{"users": [
{
   "id": 567,
   "email": "utest1@a.com",
   "name": "utest1"
}]}'''
    assertException(lambda: sendPost('/api/v2/users/create_many', s), Exception)

    # email is required
    s = r'''{"users": [
{
   "name": "utest1"
}]}'''
    assertException(lambda: sendPost('/api/v2/users/create_many', s), Exception)

    ############## Successes ###################
    template = r'''{"users": [
{
   "email": "utest1@a.com",
   "name": "utest1"
},
{
   "email": "utest2@a.com",
   "name": "utest2"
}]}
    '''
    result = sendPostAndGetJob('/api/v2/users/create_many', jsonData=template)
    assertEq(2, len(result['results']))

    testBatchResults(result, hasSuccess=True, action='create', status='Created')
    stateIds['user1'] = int(result['results'][0]['id'])
    stateIds['user2'] = int(result['results'][1]['id'])

    ############## Successes and already exists ###################
    template = r'''{"users": [
{
   "email": "utest1@a.com",
   "name": "utest1"
},
{
   "email": "utest3@a.com",
   "name": "utest3"
}]}
    '''
    result = sendPostAndGetJob('/api/v2/users/create_many', template)
    assertEq(2, len(result['results']))
    expectedAction = lambda i: 'update' if i == 0 else 'create'
    expectedStatus = lambda i: 'Updated' if i == 0 else 'Created'
    testBatchResults(result, hasSuccess=True, action=expectedAction, status=expectedStatus)
    stateIds['user3'] = int(result['results'][1]['id'])
