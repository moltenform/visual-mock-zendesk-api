from test_helpers import *


def go6TicketsShowComments():
    ############## No results ###################
    assertException(lambda: sendGet(f'/api/v2/tickets/999/comments'), Exception)

    ############## Result w 1 comment ###################
    result2 = sendGet(f'/api/v2/tickets/{stateIds["ticket2"]}/comments')
    assertEq(1, result2['count'])
    assertEq(1, len(result2['comments']))

    ############## Other result w 1 comment ###################
    result3 = sendGet(f'/api/v2/tickets/{stateIds["ticket3"]}/comments')
    assertEq(1, result3['count'])
    assertEq(1, len(result3['comments']))

    ############## Result w 2 comments ###################
    result1 = sendGet(f'/api/v2/tickets/{stateIds["ticket1"]}/comments')
    assertEq(2, result1['count'])
    assertEq(2, len(result1['comments']))

    ############## Test ticket contents ###################
    testComment(result2['comments'][0], authorId=stateIds['user4inline'], text='plainStringComment1')
    testComment(result3['comments'][0], authorId=stateIds['admin'], text='plainStringComment2')
    testComment(result1['comments'][0], authorId=stateIds['user2'], text='comment1', public=False)
    testComment(result1['comments'][1], authorId=stateIds['admin'], text='comment2')

    ############## Test default authors ###################
    result1 = sendGet(f'/api/v2/tickets/{stateIds["ticket1"]}/comments')
    result3 = sendGet(f'/api/v2/tickets/{stateIds["ticket3"]}/comments')
    result4 = sendGet(f'/api/v2/tickets/{stateIds["ticket4"]}/comments')
    result5 = sendGet(f'/api/v2/tickets/{stateIds["ticket5"]}/comments')
    #           requester set, author set (comment1)
    assertEq('comment1', result1['comments'][0]['plain_body'])
    assertEq(stateIds['user2'], result1['comments'][0]['author_id'])
    #           requester set, author not set but prev is (comment2)
    assertEq('comment2', result1['comments'][1]['plain_body'])
    assertEq(stateIds['admin'], result1['comments'][1]['author_id'])
    #           requester set, author not set (testAuthorId1)
    assertEq('testAuthorId1', result4['comments'][0]['plain_body'])
    assertEq(stateIds['user2'], result4['comments'][0]['author_id'])
    #           requester not set, author set  (testAuthorId2)
    assertEq('testAuthorId2', result5['comments'][0]['plain_body'])
    assertEq(stateIds['user1'], result5['comments'][0]['author_id'])
    #           requester not set, author not set but prev is (testAuthorId3)
    assertEq('testAuthorId3', result5['comments'][1]['plain_body'])
    assertEq(stateIds['admin'], result5['comments'][1]['author_id'])
    #           requester not set, author not set (plainStringComment2)
    assertEq('plainStringComment2', result3['comments'][0]['plain_body'])
    assertEq(stateIds['admin'], result3['comments'][0]['author_id'])
    # look at tickets
    result = sendGet(
        '/api/v2/tickets/show_many', f'ids={stateIds["ticket3"]},{stateIds["ticket4"]},{stateIds["ticket5"]}'
    )
    sortResultsByOurNumber(result, stateIds, 'tickets')
    assertEq(stateIds['admin'], result['tickets'][0]['requester_id'])
    assertEq(stateIds['admin'], result['tickets'][0]['submitter_id'])
    assertEq(stateIds['user2'], result['tickets'][1]['requester_id'])
    assertEq(stateIds['user3'], result['tickets'][1]['submitter_id'])
    assertEq(stateIds['admin'], result['tickets'][2]['requester_id'])
    assertEq(stateIds['admin'], result['tickets'][2]['submitter_id'])
