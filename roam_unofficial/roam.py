from functools import wraps
import datetime as dt
import requests
import json
from typing import List, Optional, Any, Dict, TypedDict


class RoamGroup(TypedDict):
    addressId: str
    roamId: int
    accountId: int
    groupType: str
    name: str
    accessMode: str
    groupManagement: str
    enforceThreadedMode: str
    dateCreated: str
    imageUrl: str


class Roam:
    """
    Represents a Roam Bot. And has several functions / helper functions
    for program management.

    :param str bot_name:
        Display Name for your bot.
    :param str bot_id:
        Id for your bot.
    :param str image_url:
        Public URL to an image for your bots icon.
    :param str token:
        Your API Key for the Application Bearer Header.
    :param Dict[str, str] | None headers:
        Add or overwrite the default headers.
    :param List[str] | None channels:
        Set default channels to be included in all messages.
    """

    def __init__(
        self,
        bot_name: str,
        bot_id: str,
        image_url: str,
        token: str,
        headers: Optional[Dict[str, str]] = None,
        channels: Optional[List[str]] = None,
    ) -> None:
        self.bot_name = bot_name
        self.bot_id = bot_id
        self.image_url = image_url
        self.token = token

        # Prerender consistent values
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        if headers is not None:
            self.headers |= headers

        self.base: Dict[str, Any] = {
            "sender": {
                "id": self.bot_id,
                "name": self.bot_name,
                "imageUrl": self.image_url,
            },
        }

        if isinstance(channels, list):
            self.channels = channels
        elif channels is None:
            self.channels = None
        else:
            raise ValueError("Channels can only be passed as a list.")

    def send_message(
        self,
        message: str,
        channels: Optional[List[str]] = None,
    ):
        """
        Send a message from your bot to the specified channels.

        :param str message: the message that is sent on failure. opt args below.
        :param List[str] channels: channel ids to send the messages to.
        """
        url = "https://api.ro.am/v1/chat.sendMessage"

        payload = self.base.copy()

        payload |= {"text": message}
        if channels is None:
            channels = self.channels
        elif self.channels is not None:
            channels = list(set([*self.channels, *channels]))
        else:
            raise ValueError(
                "No Channel passed at init or during message building."
            )

        payload["recipients"] = channels

        requests.request(
            "POST", url, headers=self.headers, data=json.dumps(payload)
        )

    def list_channels(
        self,
    ) -> List[RoamGroup]:
        channels = json.loads(
            requests.get(
                "https://api.ro.am/v1/groups.list",
                headers=self.headers,
                data={},
            ).text
        )

        if isinstance(channels, list):
            return [RoamGroup(channel) for channel in channels]
        else:
            raise ValueError("Unexpected Response from Roam Server")

    def test_connection(self) -> bool:
        resp = json.loads(
            requests.get(
                "https://api.ro.am/v1/test", headers=self.headers, data={}
            ).text
        )
        return resp.get("status") == "ok"

    def notify(
        self,
        message: str,
        channels: Optional[List[str]] = None,
        message_success: Optional[str] = None,
    ):
        """
        Send messages based on runtime to any number of Roam channels.

        :param str message:
            The message that is sent on failure. opt args below.
        :param list[str] channels:
            Channel ids to send the messages to.
        :param str | None message_success:
            Optional message to send on Success.

        message and message_success can use additonal format variables from the
        function and ones built into this decorator.

        In order to pass additional values they must be passed as kwargs.

        ```python
        "{func_name}: Time-{func_start_time}. {table} failed {func_exception}"
        ```

        In this example only "table" is user defined

        Message Format Variables:
            func_name: The name of the function.
            func_start_time: is the timestamp for the function start.
            func_end_time: is the timestamp for completion.
            func_exception: The exception if the function fails.

        Examples:

            ```python
            @roam.notify(
                channels=[my_secret_channel_id],
                message="{func_name}:{func_start_time} {table}: <{func_exception}>"
            def my_func(table: str):
                # Do Stuff
                ...

            # You must use "table=" for the decorator to pass it forward.
            my_func(table="SomeTable")

            ```

            This will send the following message only on failure:

            "my_func:2023-08-30 14:35:35 SomeTable: <exception>"

            ----------------------------------------

            ```python
            @roam.notify(
                channels=[my_secret_channel_id, my_other_channel],
                message="{func_name}:{func_start_time}. Failed <{func_exception}>"
                message_success="{func_name}: {func_start_time} - {func_end_time}"
            def mission_critical_func():
                # Do Stuff
                ...

            mission_critical_func()
            ```

            This will send to passed channels on success.
            "mission_critical_func:2023-08-30 14:35:35 - 2023-08-30 14:39:42"

            But will also send the following on failure:
            "my_mission_critical_func:2023-08-30 14:35:35 Failed <exception>"

            -----------------------------------------
        """

        def wrapper(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                func_start_time = dt.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                try:
                    val = func(*args, **kwargs)
                    func_end_time = dt.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if message_success is not None:
                        self.send_message(
                            message=message_success.format(
                                **kwargs,
                                func_start_time=func_start_time,
                                func_end_time=func_end_time,
                                func_exception="DID NOT FAIL",
                                func_name=func.__name__,
                            ),
                            channels=channels,
                        )
                    return val

                except Exception as e:
                    self.send_message(
                        message=message.format(
                            **kwargs,
                            func_start_time=func_start_time,
                            func_end_time="DID NOT COMPLETE",
                            func_exception=e,
                            func_name=func.__name__,
                        ),
                        channels=channels,
                    )
                    raise e

            return wrapped

        return wrapper
