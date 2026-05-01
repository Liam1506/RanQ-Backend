from fastapi import APIRouter, Depends, status

from auth.schemas import PollCreate, PollResponse, VoteCreate, VoteResponse
from db.connect import db
from polls.db import create_poll, delete_poll, get_all_polls, get_poll, vote_poll
from auth.authUser import auth_user

router = APIRouter(prefix="/api/polls", tags=["polls"])


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=PollResponse)
def create(payload: PollCreate, user: str = Depends(auth_user)):
    return create_poll(db, payload.question, payload.options, user)


@router.delete("/delete", status_code=status.HTTP_200_OK, response_model=PollResponse)
def delete(payload: PollCreate, user: str = Depends(auth_user)):
    return delete_poll(db, payload.question, user)


@router.get("/get", status_code=status.HTTP_200_OK, response_model=PollResponse)
def get(question: str, user: str = Depends(auth_user)):
    return get_poll(db, question)

@router.get("/getAll", status_code=status.HTTP_200_OK, response_model=list[PollResponse])
def get_all(user: str = Depends(auth_user)):
    return get_all_polls(db)


@router.post("/vote", status_code=status.HTTP_201_CREATED, response_model=VoteResponse)
def vote(payload: VoteCreate, user: str = Depends(auth_user)):
    return vote_poll(db, payload.poll_id, payload.option_id, user)
