import threading
import json
import logging
import requests


class UpdateThread(threading.Thread):

    """A class enabling updates from interactions with the Nabaztag to be sent to the server.

    Messages to be sent to the server are read from the update_queue queue, and posted
    to the corresponding URL on the server. Due to limitations with django-websocket-redis,
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

        Whilst running, the UpdateThread does a blocking get from the update_queue queue
        and posts the message as the JSON body of the request, logging the message sent
        and the response received.
        """

        # Tell the server to expect JSON content in the body of the request.
        headers = {'content-type': 'application/json'}

        while True:
            update = self.update_queue.get()
            url = self.generate_url(update, self.post_url)
            if url is not None:
                response = requests.post(
                    url,
                    data=json.dumps(update),
                    headers=headers
                )
                self.log_update_reponse(update, response.json(), url)

    @staticmethod
    def generate_url(update, baseurl):

        """Depending on the contents of update, return the correct POST url.

        :param update: A JSON object containing the update message.
        :param baseurl: A string containing the base POST url.
        """

        if "moved" in update:
            baseurl += 'ear'
        elif "button" in update:
            baseurl += 'button'
        elif "location" in update:
            baseurl += 'location'
        else:
            baseurl = None

        return baseurl

    def log_update_reponse(self, update, response, url):

        """Log the message sent and reponse recieved to the application-wide log.

        :param update: The update message that was sent.
        :param response: The response received from sending the update.
        """

        logging.info(
            "{threadname} - POSTed {update} to {url}".format(
                threadname=self.name,
                update=json.dumps(update),
                url=url
            )
        )
        logging.info(
            "{threadname} - Response: {response}".format(
                threadname=self.name,
                response=json.dumps(response)
            )
        )