from fastapi import APIRouter, Depends, status

from auth.schemas import (
    AllCommentsCreate,
    AllCommentsResponse,
    CommentCreate,
    CommentResponse,
    PollCreate,
    PollDelete,
    PollResponse,
    RemoveVoteCreate,
    RemoveVoteResponse,
    RetractVoteCreate,
    RetractVoteResponse,
    VoteCreate,
    VoteResponse,
    RedditVoteResponse,
    RedditVoteCreate,
    RedditScoreCreate,
    RedditScoreResponse,
    ApprovePollResponse,
    ApprovePollCreate,
)
from db.connect import db
from polls.db import (
    comment_poll,
    create_poll,
    delete_poll,
    get_all_polls,
    get_my_polls,
    get_poll,
    get_reddit_score_for,
    remove_vote,
    retract_vote,
    vote_poll,
    get_all_comments_for,
    reddit_vote_poll,
    approve_poll,
    get_unapproved_polls,
)
from auth.authUser import auth_user, auth_admin, auth_user_with_role

router = APIRouter(prefix="/api/polls", tags=["polls"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=PollResponse
)
def create(payload: PollCreate, user: str = Depends(auth_user)):
    return create_poll(db, payload.question, payload.options, user)


@router.delete("/delete", status_code=status.HTTP_200_OK, response_model=PollResponse)
def delete(payload: PollDelete, user: str = Depends(auth_user)):
    return delete_poll(db, payload.id, user)


@router.get("/get", status_code=status.HTTP_200_OK, response_model=PollResponse)
def get(question: str, user: str = Depends(auth_user)):
    return get_poll(db, question)


@router.get(
    "/getAll", status_code=status.HTTP_200_OK, response_model=list[PollResponse]
)
def get_all(user: str = Depends(auth_user)):
    return get_all_polls(db, user)


@router.post("/vote", status_code=status.HTTP_201_CREATED, response_model=VoteResponse)
def vote(payload: VoteCreate, user: str = Depends(auth_user)):
    return vote_poll(db, payload.poll_id, payload.option_id, user)


@router.delete(
    "/deleteVote", status_code=status.HTTP_200_OK, response_model=RetractVoteResponse
)
def retract(payload: RetractVoteCreate, user: str = Depends(auth_user)):
    return retract_vote(db, payload.poll_id, user)


@router.post(
    "/comment", status_code=status.HTTP_201_CREATED, response_model=CommentResponse
)
def comment(payload: CommentCreate, user: str = Depends(auth_user)):
    return comment_poll(db, payload.poll_id, payload.comment, user)


@router.post(
    "/getAllComments",
    status_code=status.HTTP_200_OK,
    response_model=list[AllCommentsResponse],
)
def all_comments(payload: AllCommentsCreate, user: str = Depends(auth_user)):
    return get_all_comments_for(db, payload.poll_id)


@router.post(
    "/redditVote",
    status_code=status.HTTP_201_CREATED,
    response_model=RedditVoteResponse,
)
def reddit_vote(payload: RedditVoteCreate, user: str = Depends(auth_user)):
    return reddit_vote_poll(db, payload.poll_id, payload.voting_score, user)


@router.post(
    "/redditScore", status_code=status.HTTP_200_OK, response_model=RedditScoreResponse
)
def reddit_score(payload: RedditScoreCreate, user: str = Depends(auth_user)):
    return get_reddit_score_for(db, payload.poll_id)


@router.get(
    "/getMyPolls", status_code=status.HTTP_200_OK, response_model=list[PollResponse]
)
def get_my(user: str = Depends(auth_user)):
    return get_my_polls(db, user)


@router.post(
    "/approvePoll", status_code=status.HTTP_200_OK, response_model=ApprovePollResponse
)
def approvePoll(payload: ApprovePollCreate, user: str = Depends(auth_admin)):
    return approve_poll(db, payload.poll_id)


@router.get(
    "/getUnapproved", status_code=status.HTTP_200_OK, response_model=list[PollResponse]
)
def get_unapproved(user: str = Depends(auth_admin)):
    return get_unapproved_polls(db)


@router.delete(
    "/deleteVote", status_code=status.HTTP_200_OK, response_model=RemoveVoteResponse
)
def remove(payload: RemoveVoteCreate, user_role: tuple = Depends(auth_user_with_role)):
    user, is_admin = user_role
    return remove_vote(db, payload.poll_vote_id, user, is_admin)
