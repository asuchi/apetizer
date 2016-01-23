'''
Created on 17 mars 2015

@author: rux
'''
import json


def API_json_parser(obj):
    """Default JSON serializer."""
    import calendar
    import datetime

    if isinstance(obj, datetime.date):
        return str(obj)

    elif isinstance(obj, datetime.datetime):
        # TODO
        # set iso 8601
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    else:
        raise TypeError("Unserializable object %s of type %s" % (obj, type(obj)
                                                                 ))

def load_json(value):
    """
    Unserialize json string
    """
    try:
        return json.loads(value)
    except:
        return {}

def dump_json(value):
    """Serialize json string"""
    return json.dumps(value, default=API_json_parser)


