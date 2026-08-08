from contextvars import ContextVar

# Who is acting on the current request, populated
# by the auth dependencies and read by the request
# logging middleware.
request_actor: ContextVar[dict] = ContextVar(
    "request_actor",
    default={},
)


def bind_actor(
    user_id=None,
    session_id=None,
) -> None:
    """
    Record the authenticated identity for the
    duration of the request.
    """

    actor = {}

    if user_id:
        actor["user_id"] = str(user_id)

    if session_id:
        actor["session_id"] = str(session_id)

    request_actor.set(actor)


def current_actor() -> dict:
    return request_actor.get()
