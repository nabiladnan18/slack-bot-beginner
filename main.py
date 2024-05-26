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
welcome_messages = {}


class WelcomeMessage:
    START_TEXT = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Welcome to this awesome channel! \n\n"
            "*Get started by completing the following tasks!*",
        },
    }

    DIVIDER = {"type": "divider"}

    def __init__(self, channel, user) -> None:
        self.channel = channel
        self.user = user
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.completed = False

    def get_message(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            # * Removing the `username` and `icon_emoji`
            # * This allows Starter Bot to send DMs
            # * Otherwise, "Slackbot" sends it
            # "username": "Welcome Robot!",
            # "icon_emoji": self.icon_emoji,
            "blocks": [self.START_TEXT, self.DIVIDER, self._get_reaction_task()],
        }

    def _get_reaction_task(self):
        checkmark = ":white_check_mark:"
        if not self.completed:
            checkmark = ":white_large_square:"

        text = f"{checkmark} *React to this message!*"

        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


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
    user_id = event.get("user")
    text = event["text"]
    if user_id is not None and user_id != BOT_ID:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        # client.chat_postMessage(channel=channel_id, text=text)
        if text.lower() == "start":
            # send_welcome_message(channel_id, user_id) --> Sends message to channel
            send_welcome_message(f"@{user_id}", user_id)


def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response["ts"]

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome


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


# @slack_event_adapter.on("team-join") --> CHECK THIS LATER!

if __name__ == "__main__":
    app.run(debug=True)
