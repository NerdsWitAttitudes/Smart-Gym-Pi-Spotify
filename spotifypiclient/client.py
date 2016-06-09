import argparse
import base64
import configparser
import json
import logging
import logging.config
import sys
import requests
import threading

import spotify

from spotify.error import LibError

log = logging.getLogger()

redis_client = None

parser = argparse.ArgumentParser(
    description="""
        Plays a spotify playlist for a gym
    """
)

parser.add_argument(
    '--config', default='settings.ini', type=str,
    help="Argument that takes a configuration file"
)


class Client(object):

    def __init__(self):
        self.session = spotify_session
        self.playlist = self.session.get_playlist(
            config['spotify']['playlist.uri'])
        self.auth_header = self.get_auth_header()
        self.remote_url = config['app:main']['remote_url']
        self.client_address = config['app:main']['local_MAC_address']

    def main(self):
        self.play_track()

    def play_track(self):
        # create event for checking if the track is complete
        end_of_track = threading.Event()

        def on_end_of_track(self):
            end_of_track.set()
        spotify_session.on(spotify.SessionEvent.END_OF_TRACK, on_end_of_track)
        # load the playlist
        self.playlist = self.playlist.load()
        try:
            track = self.playlist.tracks[0].load()
            self.session.player.load(track)
            self.session.player.play()
            self.remove_track(track)
            self.add_track()

            # Wait for track to complete
            try:
                while not end_of_track.wait(0.1):
                    pass
            except KeyboardInterrupt:
                pass
        except IndexError:
            # this happends when the playlist is empty
            self.add_track()
        except LibError:
            # this happends when the track is not available
            self.remove_track(track)
            self.add_track()

        self.play_track()

    def add_track(self):
        requests.post(self.remote_url,
                      data=json.dumps(
                          {'client_address': self.client_address}),
                      headers=self.auth_header)

    def remove_track(self, track):
        requests.delete(self.remote_url,
                        data=json.dumps({'uri': str(track.link),
                                         'client_address':
                                             self.client_address}),
                        headers=self.auth_header)

    def get_auth_header(self):
        try:
            client_id = config['oauth']['client_id']
            client_secret = config['oauth']['client_secret']
            token_url = config['oauth']['access_token_url']
        except KeyError:
            log.critical("OAuth settings not correctly specified",
                         exc_info=True)
            sys.exit()

        client_credentials = '{}:{}'.format(
            client_id, client_secret)

        # b64 encode expects bytes. After that we convert from bytes to string
        encoded_client_credentials = base64.b64encode(
            client_credentials.encode('utf-8')).decode('utf-8')
        client_auth_header = {
            'Authorization': 'Basic {}'.format(encoded_client_credentials)
        }
        request_body = {'grant_type': 'client_credentials'}

        access_token_request = requests.post(token_url,
                                             json=request_body,
                                             headers=client_auth_header)

        if access_token_request.status_code != 200:
            # Without the access code we can't persist any devices
            log.critical("Can't get access token")
            log.critical(access_token_request.status_code)
            sys.exit()

        response_body = access_token_request.json()

        auth_header = {
            'Authorization': '{} {}'.format(
                response_body['token_type'],
                response_body['access_token'])
        }

        return auth_header

if __name__ == "__main__":
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(args.config)
    logging.config.fileConfig(config)

    # spotify
    spotify_config = spotify.Config()
    spotify_config.user_agent = 'Spotify client'
    spotify_session = spotify.Session(spotify_config)

    # Process events in the background
    loop = spotify.EventLoop(spotify_session)
    loop.start()

    # Connect an audio sink
    audio = spotify.AlsaSink(spotify_session)

    logged_in_event = threading.Event()

    def connection_state_listener(session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            logged_in_event.set()

    spotify_session.on(
        spotify.SessionEvent.CONNECTION_STATE_UPDATED,
        connection_state_listener)
    spotify_session.login(
        config['spotify']['username'], config['spotify']['password'])
    while not logged_in_event.wait(0.1):
        spotify_session.process_events()

    client = Client()
    client.main()
