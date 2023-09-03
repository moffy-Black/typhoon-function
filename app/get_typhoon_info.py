import requests
import xml.etree.ElementTree as ET
from datetime import datetime,timedelta
import pyproj

grs80 = pyproj.Geod(ellps='GRS80')

def get_typhoon_info()->(bool,list or str):
    JAPAN_METEOROLOGICAL_AGENCY_DISASTER_PREVENTION_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"
    flag, latest_typhoon_xml_list = _get_latest_typhoon_xml(JAPAN_METEOROLOGICAL_AGENCY_DISASTER_PREVENTION_URL)
    if not flag:
        return False,latest_typhoon_xml_list
    typhoon_info_list = []
    for latest_typhoon_xml in latest_typhoon_xml_list:
        flag, latest_typhoon_info = _get_latest_typhoon_info(latest_typhoon_xml)
        if flag:
            typhoon_info_list.append(latest_typhoon_info)
        else:
            print(latest_typhoon_info)
    if len(typhoon_info_list) > 0:
        return True,typhoon_info_list
    else:
        return False, 'get typhoon_xml but not get typhoon_info'
def _get_latest_typhoon_xml(url:str) -> (bool,str):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            xml_data = response.content.decode("utf-8")
            return _extracting_latest_typhoon_xml(xml_data)
        else:
            return False, 'HTTP status code error: '+response.status_code

    except requests.exceptions.RequestException as e:
        return False, 'HTTP get error: '+ e

def _extracting_latest_typhoon_xml(xml_data:str) -> (bool,list or str):
    current_time = datetime.utcnow()
    current_time = current_time.replace(minute=0,second=0,microsecond=0)
    one_hour_ago = current_time - timedelta(hours=1)
    _name_space = "{http://www.w3.org/2005/Atom}"
    _xml_list = []
    try:
        root = ET.fromstring(xml_data)
        for entry in root.findall(f"{_name_space}entry"):
            title = entry.find(f'{_name_space}title')
            if title.text == "台風解析・予報情報（５日予報）（Ｈ３０）":
                updated_str = entry.find(f'.//{_name_space}updated').text
                updated_datetime = _str_to_datetime(updated_str)
                if updated_datetime >= one_hour_ago:
                    _xml = entry.find("{http://www.w3.org/2005/Atom}id").text
                    _xml_list.append(_xml)
        if len(_xml_list) > 0:
            return True, _xml_list
        else:
            return False, "content empty error: This XML does not contain typhoon information."
    except ET.ParseError as e:
        return False, 'XML parse error: '+e

def _str_to_datetime(xml_datetime:str) -> datetime:
    return datetime.strptime(xml_datetime, '%Y-%m-%dT%H:%M:%SZ')

def _get_latest_typhoon_info(url:str) -> (bool,list or str):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            xml_data = response.content.decode("utf-8")
            return _extracting_typhoon_info(xml_data)
        else:
            return False, 'HTTP status code error: '+response.status_code

    except requests.exceptions.RequestException as e:
        return False, 'HTTP get error: '+ e

def _extracting_typhoon_info(xml_data:str) -> (bool,list or str):
    _name_space = "{http://xml.kishou.go.jp/jmaxml1/body/meteorology1/}"
    _jmx_eb_name_space = "{http://xml.kishou.go.jp/jmaxml1/elementBasis1/}"
    typhoon_info = []
    try:
        root = ET.fromstring(xml_data)
        infos = root.findall(f".//{_name_space}MeteorologicalInfo")
        # remark = root.find(f".//{_name_space}Remark").text

        for info in infos:
            data_dict = {"時刻":{"type":"","value":""},"台風":{"位置":(0.0,0.0), "半径":0}}
            date_time = info.find(f"{_name_space}DateTime")
            data_dict["時刻"]["type"] = date_time.attrib["type"];data_dict["時刻"]["value"] = date_time.text

            _extracting_center_position(info,data_dict,_jmx_eb_name_space)
            wind_area_parts = info.findall(f".//{_name_space}WarningAreaPart")
            if len(wind_area_parts) == 0:
                continue
            _flag = _extracting_wind_part(wind_area_parts,data_dict,_jmx_eb_name_space)
            if _flag:
                typhoon_info.append(data_dict)
        return True, typhoon_info
    except ET.ParseError as e:
        return False, 'XML parse error: '+e
    except Exception as e:
        return False, 'some error: '+e

def _extracting_center_position(info,data_dict,name_space):
    if data_dict["時刻"]["type"] in ["実況","推定　１時間後"]:
        coordinates = info.findall(f".//{name_space}Coordinate")
        for coordinate in coordinates:
            if coordinate.attrib["type"] == "中心位置（度）":
                _, latitude, longitude = coordinate.text.strip("/").split("+")
                data_dict["台風"]["位置"] = tuple(map(float,[longitude,latitude]))
    else:
        base_points = info.findall(f".//{name_space}BasePoint")
        for base_point in base_points:
            if base_point.attrib["type"] == "中心位置（度）":
                _, latitude, longitude = base_point.text.strip("/").split("+")
                data_dict["台風"]["位置"] = tuple(map(float,[longitude,latitude]))
    return

def _extracting_wind_part(wind_area_parts,data_dict,name_space) -> bool:
    for wind_area_part in wind_area_parts:
        if wind_area_part.attrib["type"] in ["暴風域","暴風警戒域"]:
            directions = wind_area_part.findall(f".//{name_space}Direction")
            radius = wind_area_part.findall(f".//{name_space}Radius")
            radius_list = []
            for r in radius:
                if r.attrib["unit"] == "km":
                    radius_list.append(r.text)
            if len(radius_list) == 1:
                if radius_list[0] is not None:
                    data_dict["台風"]["半径"] = float(radius_list[0])
                else:
                    return False
            else:
                azimuth = directions[0].text
                radius = (int(radius_list[0]) + int(radius_list[1])) / 2
                k_distance = (int(radius_list[0]) - int(radius_list[1])) / 2
                data_dict["台風"]["半径"] = radius
                data_dict["台風"]["位置"] = _calc_center(data_dict["台風"]["位置"],azimuth,k_distance)
    return True

def _calc_center(lonlat, azimuth, k_distance):
    lon,lat = lonlat
    azimuth_dict = {"北":0,"北東":45,"東":90,"南東":135,"南":180,"南西":225,"西":270,"北西":315}
    distance = k_distance*1000
    r_azimuth = azimuth_dict[azimuth]
    lon, lat, _ = grs80.fwd(lon,lat,r_azimuth,distance)
    lon, lat = round(lon,1), round(lat, 1)
    return lon, lat