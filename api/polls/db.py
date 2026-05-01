import uuid

from fastapi import HTTPException
from supabase import Client


def create_poll(client: Client, question: str, options: list[str], created_by: str):
    poll_id = str(uuid.uuid4())

    poll_resp = client.table("polls").insert({
        "id": poll_id,
        "created_by": created_by,
        "question": question,
        "approved": False,
    }).execute()

    if not options:
        raise HTTPException(status_code=400, detail="At least one option is required")

    client.table("options").insert([
        {"poll_id": poll_id, "option": opt} for opt in options
    ]).execute()

    return poll_resp.data[0]


def delete_poll(client: Client, question: str, created_by: str):
    existing = client.table("polls").select("*").eq("question", question).eq("created_by", created_by).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = client.table("polls").delete().eq("question", question).eq("created_by", created_by).execute()
    return response.data[0]


def get_poll(client: Client, question: str):
    response = client.table("polls").select("*").eq("question", question).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = response.data[0]

    options = client.table("options").select("*").eq("poll_id", poll["id"]).execute()
    votes = client.table("poll_votes").select("option_id").eq("poll_id", poll["id"]).execute()

    vote_counts: dict[str, int] = {}
    for v in votes.data:
        vote_counts[v["option_id"]] = vote_counts.get(v["option_id"], 0) + 1

    poll["options"] = [
        {**opt, "votes": vote_counts.get(opt["id"], 0)}
        for opt in options.data
    ]

    return poll


def vote_poll(client: Client, poll_id: str, option_id: str, user_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    option = client.table("options").select("id").eq("id", option_id).eq("poll_id", poll_id).execute()
    if not option.data:
        raise HTTPException(status_code=404, detail="Option not found for this poll")

    existing = client.table("poll_votes").select("id").eq("poll_id", poll_id).eq("user_id", user_id).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Already voted on this poll")

    response = client.table("poll_votes").insert({
        "poll_id": poll_id,
        "user_id": user_id,
        "option_id": option_id,
    }).execute()

    return response.data[0]