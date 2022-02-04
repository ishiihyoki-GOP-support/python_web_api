import requests
import xml.etree.ElementTree as ET
import goplt


def get_address(zipcode):
    url = "http://zip.cgis.biz/xml/zip.php"
    payload = {"zn": str(zipcode)}
    r = requests.get(url, params=payload)
    root=ET.fromstring(r.text)
    state=''
    city=''
    address=''
    for value in root.iter('value'):
        for item in value.attrib:
            if(item=='state'):
                state= value.attrib[item]
            elif(item=='city'):
                city= value.attrib[item]
            elif(item=='address'):
                address= value.attrib[item]
    if(state==''):
        state='存在しません'
    return state,city,address


def main():
    gop=goplt.Goplt('/dev/ttyACM0')
    while True:
        s=gop.Enq()
        if(s=='ZIP'):
            zipcode=gop.ReadMem('zipcode',1) 
            state,city,address=get_address(zipcode)
            gop.WriteTMem('state',state)
            gop.WriteTMem('city',city)
            gop.WriteTMem('address',address)
                
main()
    
        