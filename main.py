import os
import slack
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
slack_event_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app
)

client = slack.WebClient(token=os.environ["SLACK_BOT_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

message_counts = {}

# Test sending message
# client.chat_postMessage(channel="#test", text="Hello!")


# Message event
# https://api.slack.com/events/message
# {
# 	"type": "message",
# 	"channel": "C123ABC456",
# 	"user": "U123ABC456",
# 	"text": "Hello world",
# 	"ts": "1355517523.000005"
# }
@slack_event_adapter.on("message")
def message(payload: dict):
    event = payload.get("event", {})
    channel_id = event["channel"]
    user_id = event["user"]
    text = event["text"]
    if user_id != BOT_ID:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        # client.chat_postMessage(channel=channel_id, text=text)


@app.route("/message-count", methods=["POST"])
def message_count():
    data = request.form
    # print(data)
    user_id = data["user_id"]
    channel_id = data["channel_id"]
    message_count = message_counts.get(user_id, 0)
    client.chat_postMessage(
        channel=channel_id, text=f"You have sent {message_count} message(s)"
    )
    return (Response(), 200)


if __name__ == "__main__":
    app.run(debug=True)
