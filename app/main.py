from datetime import datetime, timedelta

from get_typhoon_info import get_typhoon_info
from set_typhoon_info import set_typhoon_info

if __name__ == "__main__":
    utc_now = datetime.utcnow();jst_offset = timedelta(hours=9);jst_now = utc_now + jst_offset
    target_date = jst_now - timedelta(days=1)
    print(jst_now.strftime("%Y-%m-%d %H:%M:%S"))
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