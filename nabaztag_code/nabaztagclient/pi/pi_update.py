import threading
import json
import logging
import requests


class UpdateThread(threading.Thread):

    """A class enabling updates from interactions with the Nabaztag to be sent to the server.

    Messages to be sent to the server are read from the update_queue queue, and posted
    to the corresponding URL on the server. Due to restrictions with django-websocket-redis,
    it was decided that POSTing was the simplest way to implement communication back to the server.
    Ideally, the websocket would be used correctly (bi-directionally) and updates would be sent to
    the server over the same websocket connection as commands are received from.
    """

    def __init__(self, url, update_queue, name):

        """Create an instance of the UpdateThread class

        :param url: The base portion of the URL to post updates to.
        :param name: The name of the thread to identify it in the logs.
        """

        threading.Thread.__init__(self, name=name)
        self.update_queue = update_queue
        self.post_url = url

    def run(self):

        """Start the UpdateThread thread.

        Whilst running, the UpdateThread does a blocking get from the update_queue queue, determines
        the URL suffix that messages should be posted to, and posts the message as the JSON body of
        the request, logging the message sent and the response received.
        """

        # Tell the server to expect JSON content in the body of the request.
        headers = {'content-type': 'application/json'}

        while True:
            update = self.update_queue.get()

            if "moved" in update:
                r = requests.post(
                    self.post_url + 'ear',
                    data=json.dumps(update),
                    headers=headers
                )
                self.log(json.dumps(update), r.text)
            if "button" in update:
                r = requests.post(
                    self.post_url + 'button',
                    data=json.dumps(update),
                    headers=headers
                )
                self.log(json.dumps(update), r.text)
            if "location" in update:
                r = requests.post(
                    self.post_url + 'location',
                    data=json.dumps(update),
                    headers=headers
                )
                self.log(json.dumps(update), r.text)

    def log(self, message, response):

        """Log the message sent and reponse recieved to the application-wide log.
        """

        logging.info(
            "{threadname} - Message sent: {message}".format(
                threadname=self.name,
                message=message
            )
        )
        logging.info(
            "{threadname} - Message response: {response}".format(
                threadname=self.name,
                response=response
            )
        )