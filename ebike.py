#used libraries are mentioned below
import serial #serial port library for taking data over GPIO
raspberry_port = "/dev/ttyAMA0" #using serial port ttyAMA0 of Raspberry PI
#libraries for PubNub SDK mentioned below
#Reference for using this approach: https://www.pubnub.com/docs/sdks/python/api-reference/configuration and https://github.com/pubnub/python-quickstart-platform
from pubnub.pnconfiguration import PNConfiguration
from pubnub.enums import PNStatusCategory
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException

#publish_key and subscribe_key below is PubNub authentication data to our account in PubNub
pubnub_channel = "ebike_locator" #it is the same channel name for PubNub API which also mentioned in ebike.html
pubnub_authentication=PNConfiguration()
pubnub_authentication.subscribe_key='your_PubNub_subscribe_key'
pubnub_authentication.publish_key='your_PubNub_publish_key'
pubnub_authentication.uuid='ebike_loc_sending' #it is an unique id for the raspberry PI device which is sending location
pubnub_data=PubNub(pubnub_authentication)
pubnub_data.subscribe().channels(pubnub_channel).with_presence().execute()

#read_GPS() function is for parsing gps data after reading gps module for nmea $GPGGA - Global Positioning System Fix Data ref: http://aprs.gids.nl/nmea/#gga
def read_GPS(data):
    if data[0:6] == "$GPGGA":
        satelite_data = data.split(",")
        if satelite_data[7] == '0' or satelite_data[7]=='00':
            print ("satellite data not available")
            return
            
        latitude = find(satelite_data[2])
        longitude = find(satelite_data[4])
        return  latitude,longitude

#In below the find() function is a library for decoding the calculation for finding latitude and longittude from the gps data, reference: https://github.com/wahajmurtaza/Python3-NEO-6M-GPS-Raspberry-Pi/blob/master/GPS.py
def find(coordinates):
    values = list(coordinates)
    for i in range(0,len(values)-1):
            if values[i] == "." :
                    break
    base_get = values[0:i-2] #for converting base point from GPGGA
    degi_get = values[i-2:i] #for converting integer point from GPGGA
    degd_get = values[i+1:]  #for converting degree point from GPGGA
    base_integer = int("".join(base_get))
    degi_integer = int("".join(degi_get))
    degd_integer = float("".join(degd_get))
    degd_integer = degd_integer / (10**len(degd_get))
    degs_integer = degi_integer + degd_integer
    total = float(base_integer) + (degs_integer/60)
    return total
		
#In below, data_from_PI variable is taking the data stream from GPS module using serial port of Raspberry PI
data_from_PI = serial.Serial(raspberry_port,9600,timeout = 2)

while True:
    try:
        data_stream = data_from_PI.readline().decode()
        satellite = read_GPS(data_stream)
        if(type(satellite) is tuple):
            final_latitude=satellite[0]
            final_longitude=satellite[1]
            envelope = pubnub_data.publish().channel(pubnub_channel).message({'lat':final_latitude,'lng':final_longitude}).sync() #sending latitude and longitude value to pubnub API 
            print("publish timetoken: %d" % envelope.result.timetoken) #timestamp for keeping records
        else:
            print("Error")
            
    except PubNubException as not_end:
        handle_exception(not_end)