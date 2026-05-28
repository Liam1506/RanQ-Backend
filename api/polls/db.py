import uuid

from fastapi import HTTPException
from supabase import Client


def create_poll(client: Client, question: str, options: list[str], created_by: str):
    poll_id = str(uuid.uuid4())

    poll_resp = (
        client.table("polls")
        .insert(
            {
                "id": poll_id,
                "created_by": created_by,
                "question": question,
                "approved": False,
            }
        )
        .execute()
    )

    if not options:
        raise HTTPException(status_code=400, detail="At least one option is required")

    client.table("options").insert(
        [{"poll_id": poll_id, "option": opt} for opt in options]
    ).execute()

    return poll_resp.data[0]


def delete_poll(client: Client, question: str, created_by: str):
    existing = (
        client.table("polls")
        .select("*")
        .eq("question", question)
        .eq("created_by", created_by)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("polls")
        .delete()
        .eq("question", question)
        .eq("created_by", created_by)
        .execute()
    )
    return response.data[0]


def get_all_polls(client: Client, user_id: str):
    polls = client.table("polls").select("*").eq("approved", True).order("created_at", desc=True).execute()
    if not polls.data:
        return []

    poll_ids = [p["id"] for p in polls.data]
    creator_ids = list({p["created_by"] for p in polls.data})

    options = client.table("options").select("*").in_("poll_id", poll_ids).execute()
    votes = (
        client.table("poll_votes")
        .select("option_id, poll_id")
        .in_("poll_id", poll_ids)
        .execute()
    )
    user_votes = (
        client.table("poll_votes")
        .select("poll_id, option_id")
        .in_("poll_id", poll_ids)
        .eq("user_id", user_id)
        .execute()
    )
    users = (
        client.table("users").select("id, username").in_("id", creator_ids).execute()
    )

    username_by_id: dict[str, str] = {u["id"]: u["username"] for u in users.data}

    vote_counts: dict[str, int] = {}
    for v in votes.data:
        vote_counts[v["option_id"]] = vote_counts.get(v["option_id"], 0) + 1

    user_vote_by_poll: dict[str, str] = {
        v["poll_id"]: v["option_id"] for v in user_votes.data
    }

    options_by_poll: dict[str, list] = {}
    for opt in options.data:
        options_by_poll.setdefault(opt["poll_id"], []).append(
            {**opt, "votes": vote_counts.get(opt["id"], 0)}
        )

    for poll in polls.data:
        poll["options"] = options_by_poll.get(poll["id"], [])
        poll["voted_option_id"] = user_vote_by_poll.get(poll["id"])
        poll["creator_username"] = username_by_id.get(poll["created_by"])

    return polls.data


def get_poll(client: Client, question: str):
    response = client.table("polls").select("*").eq("question", question).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = response.data[0]

    options = client.table("options").select("*").eq("poll_id", poll["id"]).execute()
    votes = (
        client.table("poll_votes")
        .select("option_id")
        .eq("poll_id", poll["id"])
        .execute()
    )

    vote_counts: dict[str, int] = {}
    for v in votes.data:
        vote_counts[v["option_id"]] = vote_counts.get(v["option_id"], 0) + 1

    poll["options"] = [
        {**opt, "votes": vote_counts.get(opt["id"], 0)} for opt in options.data
    ]

    return poll


def vote_poll(client: Client, poll_id: str, option_id: str, user_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    option = (
        client.table("options")
        .select("id")
        .eq("id", option_id)
        .eq("poll_id", poll_id)
        .execute()
    )
    if not option.data:
        raise HTTPException(status_code=404, detail="Option not found for this poll")

    existing = (
        client.table("poll_votes")
        .select("id")
        .eq("poll_id", poll_id)
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Already voted on this poll")

    response = (
        client.table("poll_votes")
        .insert(
            {
                "poll_id": poll_id,
                "user_id": user_id,
                "option_id": option_id,
            }
        )
        .execute()
    )

    return response.data[0]


def comment_poll(client: Client, poll_id: str, comment: str, user_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("comments")
        .insert({"created_by": user_id, "poll_id": poll_id, "content": comment})
        .execute()
    )

    return response.data[0]


# TODO add username
def get_all_comments_for(client: Client, poll_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("comments")
        .select("*, users!inner(username)")
        .eq("poll_id", poll_id)
        .order("created_at", desc=True)
        .execute()
    )

    for data in response.data:
        users = data.pop("users", None)
        data["created_by"] = (users or {}).get("username")
    return response.data


def reddit_vote_poll(client: Client, poll_id: str, score: int, user_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    existing = (
        client.table("up_down_votes")
        .select("id")
        .eq("poll_id", poll_id)
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Already voted on this poll")

    response = (
        client.table("up_down_votes")
        .insert({"user_id": user_id, "voting_score": score, "poll_id": poll_id})
        .execute()
    )

    return response.data[0]


def get_reddit_score_for(client: Client, poll_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("up_down_votes")
        .select("voting_score")
        .eq("poll_id", poll_id)
        .execute()
    )
    total = sum(item["voting_score"] for item in response.data)
    print(total)
    return {"total_score": total}


def get_unapproved_polls(client: Client):
    polls = client.table("polls").select("*").eq("approved", False).order("created_at", desc=True).execute()
    if not polls.data:
        return []

    poll_ids = [p["id"] for p in polls.data]
    creator_ids = list({p["created_by"] for p in polls.data})

    options = client.table("options").select("*").in_("poll_id", poll_ids).execute()
    users = client.table("users").select("id, username").in_("id", creator_ids).execute()

    username_by_id: dict[str, str] = {u["id"]: u["username"] for u in users.data}

    options_by_poll: dict[str, list] = {}
    for opt in options.data:
        options_by_poll.setdefault(opt["poll_id"], []).append({**opt, "votes": 0})

    for poll in polls.data:
        poll["options"] = options_by_poll.get(poll["id"], [])
        poll["voted_option_id"] = None
        poll["creator_username"] = username_by_id.get(poll["created_by"])

    return polls.data


def approve_poll(client: Client, poll_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("polls").update({"approved": True}).eq("id", poll_id).execute()
    )

    data = response.data[0]
    data["poll_id"] = data.pop("id")
    return data
