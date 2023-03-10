import assert from "assert";
import { getGlobalState } from "../persist.js";
import { generateCommentId, getCurrentTimestamp, normalizeId } from "./helpers.js";

/**
 * Endpoint to get comment content for a ticket
 */
export function apiGetTicketComments(ticketId) {
    const globalState = getGlobalState()
    const ticket = globalState.persistedState.tickets[ticketId]
    if (!ticket) {
        throw new Error('ticket not found')
    }

    const results = []
    for (let commentId of ticket.comment_ids) {
        commentId = normalizeId(commentId)
        const comment = globalState.persistedState.comments[commentId]
        results.push(comment)
    }

    return { comments: results, otherPagesRemain: false, next_page: undefined, count: results.length }
}

/**
 * Allow shorter syntax, { comment: 'abc' } as a shortcut for { comment: {body: 'abc' } }
 */
export function allowShortcutStringComment(obj) {
    if (typeof obj === 'string') {
        return {
            body: obj,
        }
    } else {
        return obj
    }
}

/**
 * From incoming data
 */
export function transformIncomingCommentIntoInternal(globalState, obj, fallbackAuthorId) {
    assert(!obj.id, `new comment - cannot specify id`)
    if (obj.uploads || obj.attachments) {
        throw new Error('we do not yet support attachments')
    }

    return {
        id: generateCommentId(globalState.persistedState),
        created_at: obj.created_at || getCurrentTimestamp(),
        updated_at: (obj.updated_at || obj.created_at) || getCurrentTimestamp(),
        type: "Comment",
        body: obj.body || obj.html_body,
        html_body: obj.body || obj.html_body,
        plain_body: obj.body || obj.html_body, // just for simplicity
        public: obj.public === undefined ? true : obj.public,
        author_id: normalizeId(obj.author_id || fallbackAuthorId),
        attachments: [] // not yet implemented
    }
}
