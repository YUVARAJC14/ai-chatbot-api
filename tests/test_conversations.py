def test_create_conversation(client, test_user):
    response = client.post(
        "/conversations",
        json={"title": "Test Conversation"},
        headers={"X-API-Key": test_user.api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert "id" in data

def test_create_conversation_requires_auth(client):
    response = client.post(
        "/conversations",
        json={"title": "Test Conversation"}
    )
    assert response.status_code in (401, 422)

def test_create_message(client, test_user, test_conversation, mocker):
    mocker.patch("app.main.get_ai_reply", return_value="This is a mocked AI reply.")

    response = client.post(
        f"/conversations/{test_conversation.id}/messages",
        json={"content": "Hello, AI!"},
        headers={"X-API-Key": test_user.api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert data["content"] == "This is a mocked AI reply."

def test_create_message_conversation_not_found(client, test_user):
    response = client.post(
        "/conversations/9999/messages",
        json={"content": "Hello"},
        headers={"X-API-Key": test_user.api_key}
    )
    assert response.status_code == 404


    