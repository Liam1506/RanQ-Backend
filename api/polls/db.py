from os import stat
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


# TODO maybe add admin auth or only created_by user can delete?
def delete_poll(client: Client, poll_id: str, created_by: str):
    existing = (
        client.table("polls")
        .select("*")
        .eq("id", poll_id)
        .eq("created_by", created_by)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("polls")
        .delete()
        .eq("id", poll_id)
        .eq("created_by", created_by)
        .execute()
    )
    return response.data[0]


def get_all_polls(client: Client, user_id: str):
    polls = (
        client.table("polls")
        .select("*")
        .eq("approved", True)
        .order("created_at", desc=True)
        .execute()
    )
    if not polls.data:
        return []

    poll_ids = [p["id"] for p in polls.data]
    category_ids = [p["category_id"] for p in polls.data if p.get("category_id")]
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
    up_down_votes = (
        client.table("up_down_votes")
        .select("id", "poll_id", "voting_score")
        .in_("poll_id", poll_ids)
        .execute()
    )
    up_down_user_votes = (
        client.table("up_down_votes")
        .select("*")
        .in_("poll_id", poll_ids)
        .eq("user_id", user_id)
        .execute()
    )
    poll_categorys = (
        client.table("poll_category").select("*").in_("id", category_ids).execute()
        if category_ids
        else type("obj", (), {"data": []})()
    )
    users = (
        client.table("users").select("id, username").in_("id", creator_ids).execute()
    )
    score_by_poll: dict[str, int] = {}
    for v in up_down_votes.data:
        score_by_poll[v["poll_id"]] = (
            score_by_poll.get(v["poll_id"], 0) + v["voting_score"]
        )

    category_by_poll: dict[str, str] = {}
    for c in poll_categorys.data:
        category_by_poll[c["id"]] = c["title"]

    user_up_down_by_poll: dict[str, int] = {
        v["poll_id"]: v["voting_score"] for v in up_down_user_votes.data
    }

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
        poll["total_up_down_score"] = score_by_poll.get(poll["id"], 0)
        poll["user_vote_up_down"] = user_up_down_by_poll.get(poll["id"])
        poll["category"] = category_by_poll.get(poll["category_id"])

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


def retract_vote(client: Client, poll_id: str, user_id: str):
    response = (
        client.table("poll_votes")
        .delete()
        .eq("poll_id", poll_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="No vote found for this poll")
    return response.data[0]


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
        .select("id, option_id, poll_id, user_id")
        .eq("poll_id", poll_id)
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        existing_vote = existing.data[0]
        client.table("poll_votes").delete().eq("id", existing_vote["id"]).execute()
        if existing_vote["option_id"] == option_id:
            return existing_vote

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
        .select("id, voting_score")
        .eq("poll_id", poll_id)
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        existing_vote = existing.data[0]
        if existing_vote["voting_score"] == score:
            return existing_vote
        client.table("up_down_votes").delete().eq("id", existing_vote["id"]).execute()

    response = (
        client.table("up_down_votes")
        .insert({"user_id": user_id, "voting_score": score, "poll_id": poll_id})
        .execute()
    )

    return response.data[0]


def get_reddit_score_for(client: Client, poll_id: str, user_id: str):
    poll = client.table("polls").select("id").eq("id", poll_id).execute()
    if not poll.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    response = (
        client.table("up_down_votes")
        .select("voting_score")
        .eq("poll_id", poll_id)
        .execute()
    )
    votes = user_id in response.data["user_id"]
    total = sum(item["voting_score"] for item in response.data)
    print(total)
    return {"total_score": total}


def get_unapproved_polls(client: Client):
    polls = (
        client.table("polls")
        .select("*")
        .eq("approved", False)
        .order("created_at", desc=True)
        .execute()
    )
    if not polls.data:
        return []

    poll_ids = [p["id"] for p in polls.data]
    creator_ids = list({p["created_by"] for p in polls.data})

    options = client.table("options").select("*").in_("poll_id", poll_ids).execute()
    users = (
        client.table("users").select("id, username").in_("id", creator_ids).execute()
    )

    username_by_id: dict[str, str] = {u["id"]: u["username"] for u in users.data}

    options_by_poll: dict[str, list] = {}
    for opt in options.data:
        options_by_poll.setdefault(opt["poll_id"], []).append({**opt, "votes": 0})

    for poll in polls.data:
        poll["options"] = options_by_poll.get(poll["id"], [])
        poll["voted_option_id"] = None
        poll["creator_username"] = username_by_id.get(poll["created_by"])

    return polls.data


def get_my_polls(client: Client, user_id: str):
    polls = (
        client.table("polls")
        .select("*")
        .eq("created_by", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    if not polls.data:
        return []

    poll_ids = [p["id"] for p in polls.data]

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
        poll["creator_username"] = None  # always the requesting user

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


def remove_vote(
    client: Client, poll_vote_id: str, requesting_user: str, is_admin: bool
):
    poll_vote = (
        client.table("poll_votes")
        .select("id, poll_id")
        .eq("id", poll_vote_id)
        .execute()
    )
    if not poll_vote.data:
        raise HTTPException(status_code=404, detail="Vote not found")

    if not is_admin:
        poll = (
            client.table("polls")
            .select("created_by")
            .eq("id", poll_vote.data[0]["poll_id"])
            .execute()
        )
        if not poll.data or poll.data[0]["created_by"] != requesting_user:
            raise HTTPException(
                status_code=403, detail="Not authorized to remove this vote"
            )

    response = client.table("poll_votes").delete().eq("id", poll_vote_id).execute()
    return response.data[0]
