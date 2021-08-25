import urllib.request
import json
import contextlib
import datetime
import gtfs_realtime_pb2
import os

_FEED_URLS = [
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs',  # 123456S
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l',  # L
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw',  # NRQW
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm',  # BDFM
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace',  # ACE
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-7',  # 7
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz',  # JZ
    'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g'  # G
]


def get_departures(event, context):
    # If the API ever gets to be more than one route, this should be abstracted
    request = urllib.request.Request(_FEED_URLS[3])

    mta_api_key = os.getenv('MTA_API_KEY')
    if not mta_api_key:
        return {
            "statusCode": 500,
            "body": "Error couldn't get API key from env"
        }

    stop_id = ''
    if 'stop_id' in event['resource']:
        stop_id = event['path'][1:]

    # Load key from environment variables
    request.add_header('x-api-key', os.getenv('MTA_API_KEY'))

    with contextlib.closing(urllib.request.urlopen(request)) as r:
        data = r.read()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(data)

    body = {
        'uptown': [],
        'downtown': []
    }

    for entity in feed.entity:
        if entity.HasField('trip_update'):
            for stopTimeUpdate in entity.trip_update.stop_time_update:
                if stop_id in stopTimeUpdate.stop_id:
                    time_from_now = datetime.datetime.fromtimestamp(stopTimeUpdate.departure.time) - datetime.datetime.now()

                    # We only care about times under an hour
                    if time_from_now > datetime.timedelta(0, 3600, 0):
                        continue

                    departure = {
                        'route_id': entity.trip_update.trip.route_id,
                        'departs_in':  (time_from_now.seconds//60) % 60,
                    }

                    # MTA adds N or S to signify uptown or downtown parts of the station
                    if 'N' in stopTimeUpdate.stop_id:
                        body['uptown'].append(departure)
                    else:
                        body['downtown'].append(departure)

    # Sort both uptown and downtown lists by departure time
    body = {k: sorted(v, key=lambda departure: departure['departs_in']) for k, v in body.items()}

    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }


if __name__ == '__main__':

    print(
        json.dumps(
            json.loads(
                get_departures(
                    {'resource': '/{stop_id}', 'path': '/D19'}, None)['body']
            ),
            indent=4
        )
    )
