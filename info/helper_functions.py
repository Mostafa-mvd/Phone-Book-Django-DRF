

def add_to_session(session, action_message, action_input):
    user_activities = session.get("user_activities", [])

    user_activities.append(
        (action_input, action_message)
    )

    session["user_activities"] = user_activities
    session.save()
