import assert from "assert";
import { generateCommentId, getCurrentTimestamp } from "./helpers.js";
import { validateInternalUser } from "./schema.js";


export function apiGetTicketComments(ticketId) {
    const globalState = getGlobalState()
    const ticket = globalState.persistedState.tickets[ticketId]
    if (!ticket) {
        throw new Error('ticket not found')
    }

    // don't implement pagination yet
    const results = []
    for (let commentId of ticket.comment_ids) {
        const comment = globalState.persistedState.comments[commentId]
        results.push(comment)
    }
    return { comments:results, otherPagesRemain:false, next_page:undefined}
}

export function createComment(globalState, createdAt, author_id, body, is_public) {
    const result = {
        id: generateCommentId(globalState.persistedState),
        created_at: createdAt || getCurrentTimestamp(),
        body: body,
        html_body: body,
        plain_body: body,
        public: is_public,
        author_id: author_id,
        attachment_ids: [] // would be possible to add, but haven't added it yet.
    }

    assert(globalState.persistedState.users[author_id], 'author id not found:' + author_id)
    result.modified_at = result.created_at
    return result
}

export function addCommentOnTicket(globalState, ticket, obj) {
    obj = validateInternalComment(obj)
    globalState.persistedState.comments[obj.id] = obj
    ticket.comment_ids.push(obj.id)
}
