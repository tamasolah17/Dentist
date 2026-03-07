# memory.py

conversation_store = {}

def get_history(user_id):
    return conversation_store.get(user_id, [])

def add_message(user_id, role, content):
    if user_id not in conversation_store:
        conversation_store[user_id] = []

    conversation_store[user_id].append({
        "role": role,
        "content": content
    })

    # keep last 10 messages only (important)
    conversation_store[user_id] = conversation_store[user_id][-10:]
