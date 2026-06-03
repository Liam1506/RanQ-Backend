from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class VerifyList(BaseModel):
    id: str
    verId: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    verified: bool
    admin: bool


class PollCreate(BaseModel):
    question: str
    options: list[str]


class OptionResponse(BaseModel):
    id: str
    option: str
    votes: int


class PollResponse(BaseModel):
    id: str
    question: str
    created_by: str
    creator_username: Optional[str] = None
    created_at: Optional[str] = None
    approved: bool
    options: list[OptionResponse] = []
    voted_option_id: Optional[str] = None


class VoteCreate(BaseModel):
    poll_id: str
    option_id: str


class VoteResponse(BaseModel):
    id: str
    poll_id: str
    user_id: str
    option_id: str


class CommentResponse(BaseModel):
    id: str
    poll_id: str
    created_by: str
    content: str


class CommentCreate(BaseModel):
    poll_id: str
    comment: str


class AllCommentsResponse(BaseModel):
    id: str
    created_by: str
    poll_id: str
    content: str


class AllCommentsCreate(BaseModel):
    poll_id: str


class RedditVoteResponse(BaseModel):
    id: str
    user_id: str
    poll_id: str
    voting_score: int


class RedditVoteCreate(BaseModel):
    poll_id: str
    user_id: str
    voting_score: int


class RedditScoreCreate(BaseModel):
    poll_id: str


class RedditScoreResponse(BaseModel):
    total_score: int


class ApprovePollCreate(BaseModel):
    poll_id: str


class ApprovePollResponse(BaseModel):
    poll_id: str
    approved: bool


class RemoveVoteCreate(BaseModel):
    poll_vote_id: str


class RemoveVoteResponse(BaseModel):
    id: str
