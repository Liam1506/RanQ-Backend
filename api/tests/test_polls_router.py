"""
Integration tests for polls router endpoints (/api/polls/*).

Auth dependencies (auth_user / auth_admin) are overridden via FastAPI's
dependency_overrides so no real JWT / Supabase auth is needed.
All DB functions in polls.db are patched directly.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def polls_client():
    """
    Yield (TestClient, mock_db).

    - auth_user  → always returns "test-user-id"
    - auth_admin → always returns "test-admin-id"
    - db.connect.db replaced with a MagicMock
    """
    mock_db = MagicMock()

    from main import app
    from auth.authUser import auth_user, auth_admin

    app.dependency_overrides[auth_user] = lambda: "test-user-id"
    app.dependency_overrides[auth_admin] = lambda: "test-admin-id"

    with patch("db.connect.db", mock_db), \
         patch("polls.router.db", mock_db):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c, mock_db

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

SAMPLE_POLL = {
    "id": "poll-1",
    "question": "Cats or dogs?",
    "created_by": "test-user-id",
    "creator_username": "alice",
    "created_at": "2024-01-01T00:00:00",
    "approved": True,
    "options": [
        {"id": "opt-1", "option": "Cats", "votes": 3},
        {"id": "opt-2", "option": "Dogs", "votes": 7},
    ],
    "voted_option_id": None,
}


# ---------------------------------------------------------------------------
# POST /api/polls/create
# ---------------------------------------------------------------------------

class TestCreatePoll:

    def test_create_success(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.create_poll", return_value=SAMPLE_POLL):
            resp = client.post("/api/polls/create", json={
                "question": "Cats or dogs?",
                "options": ["Cats", "Dogs"],
            })

        assert resp.status_code == 201
        assert resp.json()["question"] == "Cats or dogs?"

    def test_create_requires_auth(self):
        """Without dependency override the endpoint should reject missing token."""
        from main import app
        app.dependency_overrides.clear()
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/polls/create", json={
                "question": "Q?", "options": ["A"],
            })
        assert resp.status_code == 401

    def test_create_missing_body(self, polls_client):
        client, _ = polls_client
        resp = client.post("/api/polls/create", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/polls/delete
# ---------------------------------------------------------------------------

class TestDeletePoll:

    def test_delete_success(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.delete_poll", return_value=SAMPLE_POLL):
            resp = client.request("DELETE", "/api/polls/delete", json={
                "question": "Cats or dogs?",
                "options": [],
            })

        assert resp.status_code == 200

    def test_delete_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.delete_poll",
                   side_effect=HTTPException(status_code=404, detail="Poll not found")):
            resp = client.request("DELETE", "/api/polls/delete", json={
                "question": "Ghost poll",
                "options": [],
            })

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/polls/get
# ---------------------------------------------------------------------------

class TestGetPoll:

    def test_get_success(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.get_poll", return_value=SAMPLE_POLL):
            resp = client.get("/api/polls/get", params={"question": "Cats or dogs?"})

        assert resp.status_code == 200
        assert resp.json()["id"] == "poll-1"

    def test_get_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.get_poll",
                   side_effect=HTTPException(status_code=404, detail="Poll not found")):
            resp = client.get("/api/polls/get", params={"question": "???"})

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/polls/getAll
# ---------------------------------------------------------------------------

class TestGetAllPolls:

    def test_get_all_returns_list(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.get_all_polls", return_value=[SAMPLE_POLL]):
            resp = client.get("/api/polls/getAll")

        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1

    def test_get_all_empty(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.get_all_polls", return_value=[]):
            resp = client.get("/api/polls/getAll")

        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /api/polls/vote
# ---------------------------------------------------------------------------

class TestVotePoll:

    def test_vote_success(self, polls_client):
        client, _ = polls_client
        vote = {"id": "v1", "poll_id": "poll-1", "user_id": "test-user-id", "option_id": "opt-1"}

        with patch("polls.router.vote_poll", return_value=vote):
            resp = client.post("/api/polls/vote", json={
                "poll_id": "poll-1", "option_id": "opt-1",
            })

        assert resp.status_code == 201
        assert resp.json()["option_id"] == "opt-1"

    def test_vote_already_voted(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.vote_poll",
                   side_effect=HTTPException(status_code=409, detail="Already voted on this poll")):
            resp = client.post("/api/polls/vote", json={
                "poll_id": "poll-1", "option_id": "opt-1",
            })

        assert resp.status_code == 409

    def test_vote_poll_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.vote_poll",
                   side_effect=HTTPException(status_code=404, detail="Poll not found")):
            resp = client.post("/api/polls/vote", json={
                "poll_id": "missing", "option_id": "opt-1",
            })

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/polls/comment
# ---------------------------------------------------------------------------

class TestCommentPoll:

    def test_comment_success(self, polls_client):
        client, _ = polls_client
        comment = {"id": "c1", "poll_id": "poll-1", "created_by": "test-user-id", "content": "Nice"}

        with patch("polls.router.comment_poll", return_value=comment):
            resp = client.post("/api/polls/comment", json={
                "poll_id": "poll-1", "comment": "Nice",
            })

        assert resp.status_code == 201
        assert resp.json()["content"] == "Nice"

    def test_comment_poll_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.comment_poll",
                   side_effect=HTTPException(status_code=404, detail="Poll not found")):
            resp = client.post("/api/polls/comment", json={
                "poll_id": "missing", "comment": "text",
            })

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/polls/getAllComments
# ---------------------------------------------------------------------------

class TestGetAllComments:

    def test_get_all_comments_success(self, polls_client):
        client, _ = polls_client
        comments = [
            {"id": "c1", "poll_id": "poll-1", "created_by": "alice", "content": "Great poll"},
            {"id": "c2", "poll_id": "poll-1", "created_by": "bob", "content": "Agreed"},
        ]

        with patch("polls.router.get_all_comments_for", return_value=comments):
            resp = client.post("/api/polls/getAllComments", json={"poll_id": "poll-1"})

        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_all_comments_empty(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.get_all_comments_for", return_value=[]):
            resp = client.post("/api/polls/getAllComments", json={"poll_id": "poll-1"})

        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /api/polls/redditVote
# ---------------------------------------------------------------------------

class TestRedditVote:

    def test_reddit_vote_success(self, polls_client):
        client, _ = polls_client
        record = {"id": "rv1", "user_id": "test-user-id", "poll_id": "poll-1", "voting_score": 1}

        with patch("polls.router.reddit_vote_poll", return_value=record):
            resp = client.post("/api/polls/redditVote", json={
                "poll_id": "poll-1", "user_id": "test-user-id", "voting_score": 1,
            })

        assert resp.status_code == 201
        assert resp.json()["voting_score"] == 1

    def test_reddit_vote_already_voted(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.reddit_vote_poll",
                   side_effect=HTTPException(status_code=409, detail="Already voted on this poll")):
            resp = client.post("/api/polls/redditVote", json={
                "poll_id": "poll-1", "user_id": "test-user-id", "voting_score": 1,
            })

        assert resp.status_code == 409

    def test_reddit_vote_invalid_score(self, polls_client):
        client, _ = polls_client
        # voting_score must be an int — missing it entirely triggers 422
        resp = client.post("/api/polls/redditVote", json={
            "poll_id": "poll-1", "user_id": "test-user-id",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/polls/approvePoll  (admin only)
# ---------------------------------------------------------------------------

class TestApprovePoll:

    def test_approve_success(self, polls_client):
        client, _ = polls_client
        result = {"poll_id": "poll-1", "approved": True}

        with patch("polls.router.approve_poll", return_value=result):
            resp = client.post("/api/polls/approvePoll", json={"poll_id": "poll-1"})

        assert resp.status_code == 200
        assert resp.json()["approved"] is True

    def test_approve_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch("polls.router.approve_poll",
                   side_effect=HTTPException(status_code=404, detail="Poll not found")):
            resp = client.post("/api/polls/approvePoll", json={"poll_id": "missing"})

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/polls/getUnapproved  (admin only)
# ---------------------------------------------------------------------------

class TestGetUnapproved:

    def test_get_unapproved_success(self, polls_client):
        client, _ = polls_client
        unapproved = [{**SAMPLE_POLL, "approved": False}]

        with patch("polls.router.get_unapproved_polls", return_value=unapproved):
            resp = client.get("/api/polls/getUnapproved")

        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_unapproved_empty(self, polls_client):
        client, _ = polls_client

        with patch("polls.router.get_unapproved_polls", return_value=[]):
            resp = client.get("/api/polls/getUnapproved")

        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# DELETE /api/polls/retractVote
# ---------------------------------------------------------------------------

class TestRetractVote:

    def test_retract_success(self, polls_client):
        client, _ = polls_client
        deleted = {
            "id": "v1",
            "poll_id": "poll-1",
            "user_id": "test-user-id",
            "option_id": "opt-1",
        }

        with patch("polls.router.retract_vote", return_value=deleted):
            resp = client.request(
                "DELETE",
                "/api/polls/retractVote",
                json={"poll_id": "poll-1"},
            )

        assert resp.status_code == 200
        assert resp.json()["id"] == "v1"
        assert resp.json()["poll_id"] == "poll-1"

    def test_retract_poll_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch(
            "polls.router.retract_vote",
            side_effect=HTTPException(status_code=404, detail="Poll not found"),
        ):
            resp = client.request(
                "DELETE",
                "/api/polls/retractVote",
                json={"poll_id": "missing"},
            )

        assert resp.status_code == 404

    def test_retract_no_vote(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client

        with patch(
            "polls.router.retract_vote",
            side_effect=HTTPException(
                status_code=404, detail="No vote found for this poll"
            ),
        ):
            resp = client.request(
                "DELETE",
                "/api/polls/retractVote",
                json={"poll_id": "poll-1"},
            )

        assert resp.status_code == 404

    def test_retract_requires_auth(self):
        """Without dependency override the endpoint should reject missing token."""
        from main import app

        app.dependency_overrides.clear()
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.request(
                "DELETE",
                "/api/polls/retractVote",
                json={"poll_id": "poll-1"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/polls/deleteVote  (creator OR admin)
# ---------------------------------------------------------------------------

class TestDeleteVote:

    def _override_role(self, user_id: str, is_admin: bool):
        """Helper: override auth_user_with_role on the running app."""
        from main import app
        from auth.authUser import auth_user_with_role

        app.dependency_overrides[auth_user_with_role] = lambda: (user_id, is_admin)

    def test_delete_vote_admin_success(self, polls_client):
        client, _ = polls_client
        self._override_role("admin-id", True)
        deleted = {"id": "v1"}

        with patch("polls.router.remove_vote", return_value=deleted) as mock_remove:
            resp = client.request(
                "DELETE",
                "/api/polls/deleteVote",
                json={"poll_vote_id": "v1"},
            )

        assert resp.status_code == 200
        assert resp.json()["id"] == "v1"
        # confirm router forwarded admin flag and user
        args, kwargs = mock_remove.call_args
        # signature: remove_vote(db, poll_vote_id, user, is_admin)
        assert args[1] == "v1"
        assert args[2] == "admin-id"
        assert args[3] is True

    def test_delete_vote_creator_success(self, polls_client):
        client, _ = polls_client
        self._override_role("creator-id", False)
        deleted = {"id": "v1"}

        with patch("polls.router.remove_vote", return_value=deleted) as mock_remove:
            resp = client.request(
                "DELETE",
                "/api/polls/deleteVote",
                json={"poll_vote_id": "v1"},
            )

        assert resp.status_code == 200
        assert resp.json()["id"] == "v1"
        args, _ = mock_remove.call_args
        assert args[2] == "creator-id"
        assert args[3] is False

    def test_delete_vote_forbidden(self, polls_client):
        """Non-admin, non-creator → db layer raises 403, router propagates it."""
        from fastapi import HTTPException

        client, _ = polls_client
        self._override_role("intruder-id", False)

        with patch(
            "polls.router.remove_vote",
            side_effect=HTTPException(
                status_code=403, detail="Not authorized to remove this vote"
            ),
        ):
            resp = client.request(
                "DELETE",
                "/api/polls/deleteVote",
                json={"poll_vote_id": "v1"},
            )

        assert resp.status_code == 403

    def test_delete_vote_not_found(self, polls_client):
        from fastapi import HTTPException

        client, _ = polls_client
        self._override_role("admin-id", True)

        with patch(
            "polls.router.remove_vote",
            side_effect=HTTPException(status_code=404, detail="Vote not found"),
        ):
            resp = client.request(
                "DELETE",
                "/api/polls/deleteVote",
                json={"poll_vote_id": "missing"},
            )

        assert resp.status_code == 404

    def test_delete_vote_requires_auth(self):
        """No bearer token → 401."""
        from main import app

        app.dependency_overrides.clear()
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.request(
                "DELETE",
                "/api/polls/deleteVote",
                json={"poll_vote_id": "v1"},
            )
        assert resp.status_code == 401
