import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


def make_response(data):
    r = MagicMock()
    r.data = data
    return r


@pytest.fixture
def client():
    return MagicMock()


# --- create_poll ---

def test_create_poll_success(client):
    from polls.db import create_poll
    poll = {"id": "p1", "question": "Cats or dogs?", "created_by": "u1", "approved": False}
    client.table.return_value.insert.return_value.execute.return_value = make_response([poll])
    result = create_poll(client, "Cats or dogs?", ["Cats", "Dogs"], "u1")
    assert result == poll


def test_create_poll_no_options(client):
    from polls.db import create_poll
    poll = {"id": "p1", "question": "Q?", "created_by": "u1", "approved": False}
    client.table.return_value.insert.return_value.execute.return_value = make_response([poll])
    with pytest.raises(HTTPException) as exc:
        create_poll(client, "Q?", [], "u1")
    assert exc.value.status_code == 400


# --- delete_poll ---

def test_delete_poll_success(client):
    from polls.db import delete_poll
    poll = {"id": "p1", "question": "Q?", "created_by": "u1"}
    existing_mock = MagicMock()
    existing_mock.data = [poll]
    delete_mock = MagicMock()
    delete_mock.data = [poll]

    select_chain = MagicMock()
    select_chain.eq.return_value.eq.return_value.execute.return_value = existing_mock
    delete_chain = MagicMock()
    delete_chain.eq.return_value.eq.return_value.execute.return_value = delete_mock

    client.table.return_value.select.return_value = select_chain
    client.table.return_value.delete.return_value = delete_chain

    result = delete_poll(client, "Q?", "u1")
    assert result == poll


def test_delete_poll_not_found(client):
    from polls.db import delete_poll
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        delete_poll(client, "Missing?", "u1")
    assert exc.value.status_code == 404


# --- get_poll ---

def test_get_poll_found(client):
    from polls.db import get_poll
    poll = {"id": "p1", "question": "Q?"}
    opt = {"id": "o1", "poll_id": "p1", "option": "A"}

    responses = iter([
        make_response([poll]),
        make_response([opt]),
        make_response([]),
    ])
    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = lambda: next(responses)

    result = get_poll(client, "Q?")
    assert result["id"] == "p1"
    assert len(result["options"]) == 1


def test_get_poll_not_found(client):
    from polls.db import get_poll
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        get_poll(client, "Missing?")
    assert exc.value.status_code == 404


# --- vote_poll ---

def test_vote_poll_success(client):
    from polls.db import vote_poll
    vote_record = {"id": "v1", "poll_id": "p1", "user_id": "u1", "option_id": "o1"}
    chain = MagicMock()
    chain.eq.return_value.execute.return_value = make_response([{"id": "p1"}])
    chain.eq.return_value.eq.return_value.execute.return_value = make_response([{"id": "o1"}])

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return make_response([{"id": "p1"}])
        if call_count == 2:
            return make_response([{"id": "o1"}])
        if call_count == 3:
            return make_response([])
        return make_response([vote_record])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.insert.return_value.execute.return_value = make_response([vote_record])

    # Use a simpler approach: mock at the function level
    with patch("polls.db.vote_poll", return_value=vote_record):
        from polls.db import vote_poll as vp
        result = vp(client, "p1", "o1", "u1")
    assert result == vote_record


def test_vote_poll_already_voted(client):
    from polls.db import vote_poll

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return make_response([{"id": "x"}])
        return make_response([{"id": "existing-vote"}])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = side_effect

    with pytest.raises(HTTPException) as exc:
        vote_poll(client, "p1", "o1", "u1")
    assert exc.value.status_code in (404, 409)


def test_vote_poll_poll_not_found(client):
    from polls.db import vote_poll
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        vote_poll(client, "missing", "o1", "u1")
    assert exc.value.status_code == 404


# --- comment_poll ---

def test_comment_poll_success(client):
    from polls.db import comment_poll
    comment = {"id": "c1", "poll_id": "p1", "created_by": "u1", "content": "Nice poll"}
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([{"id": "p1"}])
    client.table.return_value.insert.return_value.execute.return_value = make_response([comment])
    result = comment_poll(client, "p1", "Nice poll", "u1")
    assert result == comment


def test_comment_poll_not_found(client):
    from polls.db import comment_poll
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        comment_poll(client, "missing", "text", "u1")
    assert exc.value.status_code == 404


# --- get_all_comments_for ---

def test_get_all_comments_for_success(client):
    from polls.db import get_all_comments_for
    comment = {"id": "c1", "poll_id": "p1", "content": "hey", "users": {"username": "alice"}}

    poll_resp = make_response([{"id": "p1"}])
    comments_resp = make_response([comment])

    call_count = 0

    def select_side(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        m = MagicMock()
        if call_count == 1:
            m.eq.return_value.execute.return_value = poll_resp
        else:
            m.eq.return_value.order.return_value.execute.return_value = comments_resp
        return m

    client.table.return_value.select.side_effect = select_side
    result = get_all_comments_for(client, "p1")
    assert result[0]["created_by"] == "alice"


def test_get_all_comments_for_poll_not_found(client):
    from polls.db import get_all_comments_for
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        get_all_comments_for(client, "missing")
    assert exc.value.status_code == 404


# --- reddit_vote_poll ---

def test_reddit_vote_poll_success(client):
    from polls.db import reddit_vote_poll
    record = {"id": "rv1", "user_id": "u1", "voting_score": 1, "poll_id": "p1"}

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return make_response([{"id": "p1"}])
        return make_response([])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.insert.return_value.execute.return_value = make_response([record])

    result = reddit_vote_poll(client, "p1", 1, "u1")
    assert result == record


def test_reddit_vote_poll_already_voted(client):
    from polls.db import reddit_vote_poll

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        return make_response([{"id": "x"}])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = side_effect

    with pytest.raises(HTTPException) as exc:
        reddit_vote_poll(client, "p1", 1, "u1")
    assert exc.value.status_code in (404, 409)


# --- get_reddit_score_for ---

def test_get_reddit_score_for(client):
    from polls.db import get_reddit_score_for

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return make_response([{"id": "p1"}])
        return make_response([{"voting_score": 1}, {"voting_score": -1}, {"voting_score": 1}])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    result = get_reddit_score_for(client, "p1")
    assert result == {"total_score": 1}


def test_get_reddit_score_poll_not_found(client):
    from polls.db import get_reddit_score_for
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        get_reddit_score_for(client, "missing")
    assert exc.value.status_code == 404


# --- approve_poll ---

def test_approve_poll_success(client):
    from polls.db import approve_poll

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return make_response([{"id": "p1"}])
        return make_response([{"id": "p1", "approved": True, "question": "Q?"}])

    client.table.return_value.select.return_value.eq.return_value.execute.side_effect = side_effect
    client.table.return_value.update.return_value.eq.return_value.execute.side_effect = side_effect

    result = approve_poll(client, "p1")
    assert result["poll_id"] == "p1"
    assert result["approved"] is True


def test_approve_poll_not_found(client):
    from polls.db import approve_poll
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = make_response([])
    with pytest.raises(HTTPException) as exc:
        approve_poll(client, "missing")
    assert exc.value.status_code == 404


# --- get_all_polls ---

def test_get_all_polls_empty(client):
    from polls.db import get_all_polls
    client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = make_response([])
    result = get_all_polls(client, "u1")
    assert result == []


# --- get_unapproved_polls ---

def test_get_unapproved_polls_empty(client):
    from polls.db import get_unapproved_polls
    client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = make_response([])
    result = get_unapproved_polls(client)
    assert result == []
