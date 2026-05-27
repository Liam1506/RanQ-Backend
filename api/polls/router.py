from fastapi import APIRouter, Depends, status

from auth.schemas import (
    AllCommentsCreate,
    AllCommentsResponse,
    CommentCreate,
    CommentResponse,
    PollCreate,
    PollResponse,
    VoteCreate,
    VoteResponse,
    RedditVoteResponse,
    RedditVoteCreate,
    RedditScoreCreate,
    RedditScoreResponse,
    ApprovePollResponse,
    ApprovePollCreate
)
from db.connect import db
from polls.db import (
    comment_poll,
    create_poll,
    delete_poll,
    get_all_polls,
    get_poll,
    get_reddit_score_for,
    vote_poll,
    get_all_comments_for,
    reddit_vote_poll,
    approve_poll
)
from auth.authUser import auth_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=PollResponse
)
def create(payload: PollCreate, user: str = Depends(auth_user)):
    return create_poll(db, payload.question, payload.options, user)


@router.delete("/delete", status_code=status.HTTP_200_OK, response_model=PollResponse)
def delete(payload: PollCreate, user: str = Depends(auth_user)):
    return delete_poll(db, payload.question, user)


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


@router.post(
    "/comment", status_code=status.HTTP_201_CREATED, response_model=CommentResponse
)
def comment(payload: CommentCreate, user: str = Depends(auth_user)):
    return comment_poll(db, payload.poll_id, payload.comment, user)


@router.get(
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


@router.get(
    "/redditScore", status_code=status.HTTP_200_OK, response_model=RedditScoreResponse
)
def reddit_score(payload: RedditScoreCreate, user: str = Depends(auth_user)):
    return get_reddit_score_for(db, payload.poll_id)

@router.post(
    "/approvePoll", status_code=status.HTTP_200_OK, response_model=ApprovePollResponse
)
def approvePoll(payload: ApprovePollCreate, user: str = Depends(auth_user)):
    return approve_poll(db, payload.poll_id)
