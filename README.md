# Unofficial Roam API

This is not official.

This is a simple class based implementation for interacting with Roam in a bot like fashion via Python.

It includes convenient wrappers for the end-points shared on their [docs page](https://developer.ro.am/docs/intro).

## Installation:

Git https:

```bash
pip install git+https://github.com/Zethtren/RoamUnofficial.git
```

Git ssh:

```bash
pip install git+ssh://git@github.com/Zethtren/RoamUnofficial.git
```

## Usage:

```python
from roam_unofficial import Roam

# Create your bot
bot = Roam(
    bot_name="MyBot",
    bot_id="BotID",
    image_url="https://link_to_public_image",
    token="SUPER_SECRET_API_KEY",
    channels=["secret_channel_1", "secret_channel_2"],
)

# List Channels
for channel in bot.list_channels():
    print(channel)

# Send a Message to bot channels.
bot.send_message(
    message="Hello",
)

# Send a Message to bot channels + additional channel.
bot.send_message(
    message="Hello",
    channels=["another_channel"]
)

# Send messages based on success of other functions.
@bot.notify(
  message="{func_name}:{func_start_time}: At {arg1} -> <{func_exception}>",
  message_success="{func_name}:{func_start_time}-{func_end_time}",
  channels=["additional channel"]
)
def function(arg1: str) -> None:
    ...

# If this function succeeds it will send the message_success message.
function(arg1="Hello")
# message_success is optional
# If it fails it will send message.
```

"notify" accepts format strings.

You can pass any argument to the function in this string as well as some built in internals:

- func_start_time: When the function started formatted "%Y-%m-%d %H:%M:%S"
- func_end_time: When the function ended formatted "%Y-%m-%d %H:%M:%S" (Defaults to DID NOT COMPLETE on failure)
- func_name: The name of the function. In this example "function"
- func_exception: The Exception raised (Defaults to DID NOT FAIL on success)
