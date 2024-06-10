import os
from venv import logger
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import string
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# region
message_counts = {}
welcome_messages = {}

BAD_WORDS = ["hmm", "no", "nabil"]
# SCHEDULED_MESSAGES = [
#     {
#         "text": "First message",
#         "post_at": (datetime.now() + timedelta(seconds=40)).timestamp(),
#         "channel": "C0754PPGDLK",
#     },
#     {
#         "text": "Second message",
#         "post_at": (datetime.now() + timedelta(seconds=50)).timestamp(),
#         "channel": "C0754PPGDLK",
#     },
# ]


def check_if_bad_word(message):
    message = message.lower()
    message = message.translate(str.maketrans("", "", string.punctuation))

    return any(word in message for word in BAD_WORDS)


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
        # self.icon_emoji = ":robot_face:"
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


@app.event("message")
def eval_message(payload: dict, say):
    # It is possible to also get the whole event by using event argument
    # whole event == sample events
    # The "payload" argument just gives the event itself as in
    # the "event" array in the sample
    thread_ts = payload["ts"]
    user_id = payload["user"]
    text = payload["text"]
    if text.lower() == "start":
        send_welcome_message(f"@{user_id}", user_id)


def send_welcome_message(channel, user):
    if channel not in welcome_messages:
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]:
        return

    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = app.client.chat_postMessage(**message)
    welcome.timestamp = response.get("ts")

    welcome_messages[channel][user] = welcome


# def schedule_messages(messages):
#     ids = []
#     for msg in messages:
#         try:
#             response = client.chat_postMessage(
#                 channel=msg["channel"], text=msg["text"], post_at=msg["post_at"]
#             )
#             if response.get("ok"):
#                 logging.debug("Sent")
#                 ids.append(response["id"])
#             else:
#                 logging.error(f"Failed {response["id"]}")
#         except slack.errors.SlackApiError as e:
#             logging.error(f"API Error {str(e.response["error"])}")
#     return ids


@app.event("reaction_added")
def reaction(payload):
    # print(payload)
    logger.debug(payload)
    # event = payload["event"]
    channel = payload["item"]["channel"]
    thread_ts = payload["item"]["ts"]
    user_id = payload["user"]
    # text = event["text"]

    if f"@{user_id}" not in welcome_messages:
        return

    welcome: WelcomeMessage = welcome_messages[f"@{user_id}"][user_id]
    welcome.completed = True
    # * The channel ID needs updating here
    # * This is because to send a DM we can use @USER_ID
    # * However when we react, there is a new CHANNEL_ID 😕
    # * which starts with `D` and then some text which is NOT USER_ID
    # * IDK why tf that happens, aber das passiert halt 🤷‍♂️
    # * So we update the channel_id we get from the payload for the message
    welcome.channel = channel
    message = welcome.get_message()
    updated_message = app.client.chat_update(**message)
    welcome.timestamp = updated_message.get("ts")


# @app.route("/message-count", methods=["POST"])
# def message_count():
#     data = request.form
#     # print(data)
#     user_id = data["user_id"]
#     channel_id = data["channel_id"]
#     message_count = message_counts.get(user_id, 0)
#     client.chat_postMessage(
#         channel=channel_id, text=f"You have sent {message_count} message(s)"
#     )
#     return (Response(), 200)


# @slack_event_adapter.on("team-join") --> CHECK THIS LATER!
# endregion
@app.message(":wave:")
def say_hello(message, say):
    user = message["user"]
    say(f"Hi there, <@{user}>!")


@app.message("knock knock")
def ask_who(message, say):
    say("_Who's there?_")


@app.event("message")
def check_bad_words(body, say):
    logger.debug(body)
    event = body["event"]
    thread_ts = event.get("thread_ts", event["ts"])

    if check_if_bad_word(event["text"]):
        say(text="You can't say that!", thread_ts=thread_ts)


if __name__ == "__main__":
    # schedule_messages(SCHEDULED_MESSAGES)
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
