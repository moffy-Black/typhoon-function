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
    docs_flags = []
    for doc in docs:
        doc_data = doc.to_dict();path = doc.reference.path;event_ref = DB.document(path)
        doc_flags = []
        event_type = doc_data.get('eventtype')
        if event_type == 'event':
            event_location =  doc_data.get('location')
            event_longitude = event_location.longitude;event_latitude = event_location.latitude
            events = dict();events.setdefault("date_section_flag",dict())

            for typhoon_dict in typhoon_info:
                if "強風" in typhoon_dict:
                    wind_longitude,wind_latitude = typhoon_dict["強風"]["位置"]; wind_radius= typhoon_dict["強風"]["半径"] * 1000
                    if is_typhoon_warning(wind_longitude,wind_latitude,event_longitude,event_latitude,wind_radius):
                        events["strong_wind_flag"] = True
                        docs_flags.append(True)
                typhoon_longitude,typhoon_latitude = typhoon_dict["暴風"]["位置"]; radius = typhoon_dict["暴風"]["半径"] * 1000
                if is_typhoon_warning(typhoon_longitude,typhoon_latitude,event_longitude,event_latitude,radius):
                    events["date_section_flag"][typhoon_dict["時刻"]["value"]] = True
                    doc_flags.append(True)
                else:
                    events["date_section_flag"][typhoon_dict["時刻"]["value"]] = False
                    doc_flags.append(False)
            events["warning"] = any(doc_flags)
            event_ref.set(events,merge=True)
        elif event_type == 'train':
            stations = doc_data.get('stations')
            for station in stations:
                station_location = station.get('location')
                station_longitude = station_location.longitude;station_latitude = station_location.latitude
                station_flags = []
                for typhoon_dict in typhoon_info:
                    typhoon_longitude,typhoon_latitude = typhoon_dict["暴風"]["位置"]; radius = typhoon_dict["暴風"]["半径"] * 1000
                    station.setdefault("date_section_flag",dict())
                    if is_typhoon_warning(typhoon_longitude,typhoon_latitude,station_longitude,station_latitude,radius):
                        station["date_section_flag"][typhoon_dict["時刻"]["value"]] = True
                        station_flags.append(True)
                    else:
                        station["date_section_flag"][typhoon_dict["時刻"]["value"]] = False
                        station_flags.append(False)
                station["warning"] = any(station_flags)
                doc_flags.append(any(station_flags))
            event_ref.set({"stations":stations,"warning":any(doc_flags)},merge=True)
        else:
            pass
        docs_flags.append(any(doc_flags))
    if len(docs_flags) != 0:
        package_ref = DB.collection("travel_package").document(docs[0].reference.parent.parent.id)
        package_ref.set({"warning":any(docs_flags)},merge=True)

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