
I've written some known minor behavior differences. Someday maybe these can all be fixed such that visual-mock-zendesk-api acts the same as actual-zendesk. I've also included complexities in the api.


* General
    * in visual-mock-zendesk-api, the ending .json is optional for all endpoints, e.g. `/api/v2/search` and `/api/v2/search.json` are equivalent, this might not be the case in actual-zendesk.
    * errors will likely return different responses / different status codes as compared with actual-zendesk. visual-mock-zendesk-api has generally only currently implemented the cases that are not error cases.
    * pagination is not yet implemented, either cursor or page-level
    * rate-limit response-codes and headers are not yet implemented
    * several properties are not implemented. see schema.js
    * in general, if extra properties or unsupported properties are included on a ticket or comment, they are silently ignored (in actual-zendesk a warning header is sent back)
    * in both visual-mock-zendesk and actual-zendesk string ids are supported, sending in `id: "123"` will work, although it is technically more correct to use integer ids.
    * in visual-mock-zendesk, dates must be specified in ISO 8601 format
    * in visual-mock-zendesk, we are sometimes loose around creating a user again. if you ask visual-mock-zendesk to create a user that already exists we might silently return the existing user, actual-zendesk might error.
    * in visual-mock-zendesk, we don't look at any headers for any credentials or to know who the current admin is. there is one hard-coded admin user who is always assumed to be the current admin. 
* Ticket show
    * In both visual-mock-zendesk and actual-zendesk, `show?ids=1,2,3` might return results in a different order than the order you had in your query, like 3,2,1. 
    * in visual-mock-zendesk retrieving a ticket, the ticket has a comment_ids property, this doesn't exist in actual-zendesk.
* Ticket update
    * fail-if-last-updated-sooner-than (safe_update) is a good tool for protecting against race conditions, but it isn't implemented yet.
    * we don't support the `update_many.json?id=1` syntax.
    * In visual-mock-zendesk, if posting a new comment and the author_id is missing, we fall back to the requester, which is likely the behavior of actual-zendesk. Unclear what happens if the requester_id is being updated at the same time. I encourage you to simply send `author_id` for each comment which works in all cases.
* Ticket import
    * In both visual-mock-zendesk and actual-zendesk, there is slight distinction between tickets/imports/create_many and tickets/create_many,
        * imports can set a created_at on the comments
        * triggers are not run during imports
    * in visual-mock-zendesk ticket ids are randomly chosen, in actual-zendesk, they are always increasing.
    * Short syntax for comments when importing tickets,
        * visual-mock-zendesk allows some shorter syntax `comment: 'x'` that sometimes isn't supported by actual-zendesk 
        * I encourage you to simply send the full structure (`comments: [ {body: 'x', author_id:1} ]`) which works in all cases
    * Complexity of missing author_id or missing requester_id when importing tickets,
        * if the author_id is missing for a comment, what should the author be set to?
        * visual-mock-zendesk does implement what appears to be actual-zendesk's non-trivial behavior for these edge cases
        * I encourage you to simply send `author_id` for each comment and `requester_id` for each ticket though which works in all cases
    * Comment-ordering
        * I recommend setting a created_at in comments when importing a ticket with >1 comment, otherwise actual-zendesk might place the comments in the wrong order.
    * Inline user creation
        * In both visual-mock-zendesk and actual-zendesk,
        * Some ticket apis, especially the batch ones,
        * let you create a new user inline, for example instead of providing
        * requester_id: 234, providing requester: { name: 'name', email: 'example@example.com'}
        * this function implements this feature. Not really documented.
    * Default values
        * in visual-mock-zendesk, if certain fields like subject and description are missing there will be fallback value like '(no subject)'. in actual-zendesk there isn't a default value like this.
    * Description
        * in visual-mock-zendesk, setting the description property acts like a typical property, like subject. In actual-zendesk, setting the description property has odd behavior, like creating a comment on the ticket. I recommend not setting description, it's not needed. 
* Custom Fields and Tags
    * Custom fields and tags functionality is fairly complete.
    * Only text custom fields are supported. Note that other types are often tied to a text field, for example a dropdown custom field is backed by another text field, making them less useful because they clutter up the space.
    * The tags/set_tags property when updating tickets is not ideal because of the potential race conditions if another process is setting tags at the same time. this race conditition can be avoided with either safe_update, or the add_tags / remove_tags property. (These are only available on the batch apis, but it might be worth using the batch apis for features like this even though they involve more calls). The documentation says that add_tags / remove_tags only work for the `update_many.json?id=1` syntax (not very useful because it applies the same change to all the ids). In practice add_tags / remove_tags does work for the better `update_many.json` syntax where ticket ids are specified in a tickets array, so visual-mock-zendesk follows this.
    * in visual-mock-zendesk, if you omit setting a custom field value, it isn't there on the ticket. In actual-zendesk, if you omit setting a custom field value, it will be put there on the ticket with value null. Should fix but isn't the most urgent since null and undefined are usually treated the same way.
    * we don't support someone trying to do more than one of tags, add_tags, and remove_tags on the same ticket at the same time, which doesn't make sense.
    * In both visual-mock-zendesk and actual-zendesk, updates to custom fields merge. So if current is {fld1:a} and you set customfields to {fld2:b}, the result is {fld1:a, fld2:b}
* Comments
    * in visual-mock-zendesk, body, plain_body, and html_body are all the same. in actual-zendesk they can be different.
    * One pitfall of actual-zendesk: in some configurations like a small nonprod zendesk instance, retrieving a ticket retrieves its comment contents. In larger instances though, the comments aren't there and you have to explicitly call `/comments` to get them. visual-mock-zendesk-api follows this second behavior for safer behavior.
    * Attachments are not yet supported. It would be straightforward to add a button in the ui that added a hard-coded attachment to a comment.
    * Comments have an updated_at, which isn't there in actual-zendesk
* Users
    * In visual-mock-zendesk, user objects are essentially just an email address and a name. In actual-zendesk, there are many other features, and even features like user-custom-fields
    * In users create_many, visual-mock-zendesk returns success:true and action:updated if a user already exists with a given email. Would be good to check the behavior of actual-zendesk to ensure it matches. 
* Statuses for batch calls
    * in visual-mock-zendesk status ids are numeric, in actual-zendesk, they might contain alphanumeric chars.
    * in visual-mock-zendesk, jobs complete instantly. in actual-zendesk, there is a status=pending period.
    * in visual-mock-zendesk, job statuses expire on app restart (note that saving any js file in the source code can trigger a restart). in actual-zendesk, they expire after a defined amount of time.
    * Remember to refer to the index property when looking at the results because in actual-zendesk the order will be different. 
    * When getting job results, the different batch endpoints all have slightly different-looking output. in visual-mock-zendesk we sometimes return a superset of what happens in actual-zendesk, like getting an extra 'success: true', but the important ones like index and id are correct.
    * in actual-zendesk the ticket import job returns something called the account id (undocumented), this is ommitted in visual-mock-zendesk-api
* Search
    * Remember to correctly url-encode what you send
    * The way Zendesk's search api works is this:
    * if you specify "tags:a tags:b" this means to search for
    * tags:a OR tags:b
    * (tickets with a, tickets with b, and tickets with both are included)
    * 
    * and you can say "-tags:a" to exclude tickets with the a tag.
    * 
    * We don't currently support something like tags:a -tags:b
    * We don't currently support saying tags:"a b" to require both a AND b
    * And we don't currently support the interesting clause custom_field:a which looks for a in all custom fields
    * We only support searching by `tags`, `status`, and `custom_field_x` where x is a custom fld id
    * We do support specifying sort_by and sort_order
    * We don't limit/paginate the output. The search api limit of # of returned results is actually an issue sometimes, if you are writing an app that uses search recommend to order by created_at desc so that recent ones can be looked at first.
    * Lots of interesting features, see this, https://support.zendesk.com/hc/en-us/articles/4408886879258 and https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/
* Triggers
    * Only two triggers are supported.
    * To simulate a trigger like "Conditions: All of the following: When 'Comment' is 'Public' | Action: Remove tag"
        * in configs.json, define {"action": "removeTagWhenPublicCommentPosted", "value":"(tag)"}
    * To simulate a trigger like "Conditions: All of the following: When 'Comment' is 'Public', When 'Text' Contains String 'x' | Action: Set Ticket Status = Open"
        * in configs.json, define {"action": "openPostWhenPublicCommentContainingTextPosted", "value": "x"}
    * These will fire when tickets are updated (they'd run on ticket creation too but  the only ticket creation we support is batch import which does not run triggers).
* Zendesk custom apps
    * In visual-mock-zendesk, we don't support Zendesk custom apps




