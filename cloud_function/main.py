import functions_framework

from get_typhoon_info import get_typhoon_info
from set_typhoon_info import set_typhoon_info


@functions_framework.cloud_event
def hello_cloud_event(cloud_event):
    flag,typhoon_info_list = get_typhoon_info()
    if not flag:
        print(typhoon_info_list)
    else:
        for typhoon_info in typhoon_info_list:
            flag,message = set_typhoon_info(typhoon_info)
            if not flag:
                print("can't set typhoon_info to firestore: ",message)
            else:
                print(message)