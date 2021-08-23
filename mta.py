from secrets import secrets
import urllib.request
import json
import contextlib
import datetime
import gtfs_realtime_pb2

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


# Minimal API wrapper, reuses the MTA Feed
class Feed:
    def __init__(self):
        request = urllib.request.Request(_FEED_URLS[3])
        request.add_header('x-api-key', secrets['mta-api-key'])

        with contextlib.closing(urllib.request.urlopen(request)) as r:
            data = r.read()
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(data)

        # Persist feed
        self.feed = feed

    # Get estimates in readable format for a given stop_id. Departure estimated shown in time from now
    def get_estimates(self, stop_id):
        res = {
            'uptown': [],
            'downtown': []
        }

        for entity in self.feed.entity:
            # print([field.name for field in entity.DESCRIPTOR.fields], type(entity))
            # print("Trip Updateeryert    : ", entity.trip_update)
            if entity.HasField('trip_update'):
                # print("TRIPUPDATE: ", entity.trip_update)
                # print("STOPTIME:", entity.trip_update.stop_time_update)

                for stopTimeUpdate in entity.trip_update.stop_time_update:
                    if stop_id in stopTimeUpdate.stop_id:

                        time_from_now = datetime.datetime.fromtimestamp(stopTimeUpdate.departure.time) - datetime.datetime.now()

                        departure = {
                            'route_id': entity.trip_update.trip.route_id,
                            'departs_in':  (time_from_now.seconds//60) % 60

                        }
                        if 'S' in stopTimeUpdate.stop_id:
                            res['uptown'].append(departure)
                        else:
                            res['downtown'].append(departure)

        # Sort both uptown and downtown lists by departure time
        res = {k: sorted(v, key=lambda departure: departure['departs_in']) for k, v in res.items()}

        print(json.dumps(res, indent=4))


def main():
    f = Feed()

    # D19 is 14th and 6
    f.get_estimates('D19')


if __name__ == '__main__':
    main()
