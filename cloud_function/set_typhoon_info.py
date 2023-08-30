from firebase import DB

from datetime import datetime
from zoneinfo import ZoneInfo

import pyproj

grs80 = pyproj.Geod(ellps='GRS80')

def get_event_by_date(date_str):
    try:
        event_subcollection_ref = DB.collection_group(date_str)
        docs = event_subcollection_ref.get()
        return True, docs
    except Exception as e:
        print(e)
        return False, e

def typhoon_check(docs,typhoon_info):
    for doc in docs:
        doc_data = doc.to_dict();path = doc.reference.path;event_ref = DB.document(path)
        event_type = doc_data.get('eventtype')
        if event_type == 'event':
            event_location =  doc_data.get('location')
            event_longitude = event_location.longitude;event_latitude = event_location.latitude
            for typhoon_dict in typhoon_info:
                typhoon_longitude,typhoon_latitude = typhoon_dict["台風"]["位置"]; radius = typhoon_dict["台風"]["半径"] * 1000
                if is_typhoon_warning(typhoon_longitude,typhoon_latitude,event_longitude,event_latitude,radius):
                    event_ref.set({"date_section_flag":{typhoon_dict["時刻"]["value"]:True}},merge=True)
                else:
                    event_ref.set({"date_section_flag":{typhoon_dict["時刻"]["value"]:False}},merge=True)
        elif event_type == 'train':
            stations = doc_data.get('stations')
            for station in stations:
                station_location = station.get('location')
                station_longitude = station_location.longitude;station_latitude = station_location.latitude
                for typhoon_dict in typhoon_info:
                    typhoon_longitude,typhoon_latitude = typhoon_dict["台風"]["位置"]; radius = typhoon_dict["台風"]["半径"] * 1000
                    station.setdefault("date_section_flag",dict())
                    if is_typhoon_warning(typhoon_longitude,typhoon_latitude,station_longitude,station_latitude,radius):
                        station["date_section_flag"][typhoon_dict["時刻"]["value"]] = True
                        station["warning"]= True
                    else:
                        station["date_section_flag"][typhoon_dict["時刻"]["value"]] = False
                        station["warning"]= False
            event_ref.set({"stations":stations},merge=True)
        else:
            pass

def classfy_date(typhoon_info_list):
    typhoon_info_bydate_dict = dict()
    for info in typhoon_info_list:
        time = info["時刻"]["value"];date_time = str_to_datetime(time)
        typhoon_info_bydate_dict.setdefault(date_time.date(),[])
        typhoon_info_bydate_dict[date_time.date()].append(info)
    return typhoon_info_bydate_dict

def str_to_datetime(str):
    return datetime.strptime(str, "%Y-%m-%dT%H:%M:%S%z")

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp.timestamp()).astimezone(ZoneInfo("Asia/Tokyo"))

def is_typhoon_warning(long1,lat1,long2,lat2,r):
    _,_,distance = grs80.inv(long1,lat1,long2,lat2)
    return distance <= r

def set_typhoon_info(typhoon_data):
    try:
        typhoon_info_bydata = classfy_date(typhoon_data)
        for key_date in typhoon_info_bydata.keys():
            typhoon_info = typhoon_info_bydata[key_date]
            date_str = key_date.strftime('%Y-%m-%d')
            get_flag, docs = get_event_by_date(date_str)
            if get_flag:
                typhoon_check(docs,typhoon_info)
        return True, "complete"
    except Exception as e:
        return False, e