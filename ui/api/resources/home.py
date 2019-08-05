# Copyright 2019 Blue Marble Analytics LLC. All rights reserved.

from flask_restful import Resource


class ServerStatus(Resource):
    """
    Server status; response will be 'running'; if HTTP error is caught,
    server status will be set to 'down'
    """

    @staticmethod
    def get():
        return 'running'
