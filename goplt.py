import serial
import os
from serial.serialutil import PortNotOpenError

"""
GOP-LT/CT通信コマンド処理用ライブラリ
DATE 2022/2/3
Note
    *WriteTMem追加
    *Enqの戻り値をバイト配列ではなく文字列とするよう修正
    *文字列のエンコードを変更できるように修正
"""
def tohex(c):
    if(c>=b'0' and c<=b'9'):
        return ord(c)-ord(b'0')
    elif(c>=b'a' and c<=b'f'):
        return ord(c)-ord(b'a')+0x0a
    elif(c>=b'A' and c<=b'F'):
        return ord(c)-ord(b'A')+0x0a
    else:
        return 0
class Goplt:
    myser=None
    DATASIZE=256
    enc='sjis'
    def __init__(self,compath=None,baud=115200,encode_mode='sjis'):
        if(compath is None):
            compath='/dev/ttyACM0'
        enc=encode_mode
        try:
            self.myser=serial.Serial(compath,baud,timeout=0)
        except serial.SerialException:
            raise



    def sendpack(self,s):
        es=s.encode(self.enc)
        pack=b'\x02'
        sum=0
        for c in es:
            sum^=c
        pack+=es
        pack+=b'\x03'
        pack+=("%02x"%sum).encode(self.enc)
        pack+=b'\x0d'
        self.myser.write(pack)
        return s

    def recvpack(self):
        ret=b''
        issum=False
        while True:
            c = self.myser.read(1)
            if c == b'':
                continue
            elif c == b'\r':
                if(issum):
                    if(rsum==sum):
                        return ret
                    else:
                        return b'err'
                else:
                    return ret
            else:
                if c==b'\x02':
                    sum=0
                elif c==b'\x03':
                    issum=True
                    rsum=0
                elif c==b'\x06':
                    ret=b'[ack]'
                elif c==b'\x15':
                    ret=b'[nak]'
                else:
                    if(issum==False):
                        sum^=ord(c)
                        ret+=c
                    else:
                        rsum=rsum*0x10+tohex(c)
    def ReadMem(self,memname,num=1):
        if(num==1):
            sstr="RN "+memname
            self.sendpack(sstr)
            rstr=self.recvpack()
            if rstr!=b'err' and rstr!=b'[nak]':
                pos=rstr.find(b'=')
                return int(rstr[pos+1:])
            else:
                raise ValueError(memname+" error")
        else:
            sstr="RNB "+str(num)+","+memname
            self.sendpack(sstr)
            rstr=self.recvpack()
            if rstr!=b'err' and rstr!=b'[nak]':
                s=rstr[1:]
                tok=s.decode().split(',')
                if(int(tok[0])==num):
                    r=()
                    for i in range(0,num):
                        a=(int(tok[i+2]),)
                        r=r+a
                    return r
                else:
                    raise ValueError(memname+" error")
            else:
                raise ValueError(memname+" error")
    def ReadTMem(self,memname):
        sstr="RN "+memname
        self.sendpack(sstr)
        rstr=self.recvpack()
        if rstr!=b'err' and rstr!=b'[nak]':
            pos=rstr.find(b'=')
            return rstr[pos+1:].decode(encoding=self.enc)
        else:
            raise ValueError(memname+" error")
    def WriteMem(self,memname,*value):
        if(len(value)==1):
            sstr="WN "+memname+" "+str(value[0])
            self.sendpack(sstr)
            rstr=self.recvpack()
            if rstr==b'[ack]':
                return
            else:
                raise ValueError(memname+" error")
        else:
            sstr="WNB "+str(len(value))+","+memname
            for v in value:
                sstr=sstr+","+str(int(v))
            self.sendpack(sstr)
            rstr=self.recvpack()
            if rstr==b'[ack]':
                return
            else:
                raise ValueError(memname+" error")
    def WriteTMem(self,memname,s):
        sstr="WN "+memname+" "+s
        self.sendpack(sstr)
        rstr=self.recvpack()
        if rstr==b'[ack]':
            return
        else:
            raise ValueError(memname+" error")

            
    def Enq(self):
        self.sendpack("ENQ")
        rstr=self.recvpack()
        if rstr[0:2]==b'A$':
            return rstr[2:].decode(encoding=self.enc)
        elif rstr[0:1]==b'N':
            return ""
        else:
            raise ValueError("ENQ error")
#GOP-CT専用
    def RamUpload(self,startblock,fname):
        ret=True
        if os.path.exists(fname):
            sz=os.path.getsize(fname)
            sndcmd="RAMUPLOAD %04x %d"%(startblock,sz)
            self.sendpack(sndcmd)
            rstr=self.recvpack()
            if(rstr==b'[ack]'):          
                f=open(fname,"rb")
                buf=f.read()
                pos=0
                while pos<sz:
                    senddata=bytearray(4+self.DATASIZE+3+1)
                    senddata[0]=0x02
                    senddata[1]=pos&0x000000ff
                    senddata[2]=(pos>>8)&0x000000ff
                    senddata[3]=(pos>>16)&0x000000ff
                    senddata[4]=(pos>>24)&0x000000ff
                    i=0
                    while i<self.DATASIZE:
                        if pos<sz:
                            senddata[5+i]=buf[pos]
                        else:
                            senddata[5+i]=0
                        pos+=1
                        i+=1
                    sum=0
                    for i in range(1,self.DATASIZE+4+1):
                        sum^=senddata[i]
                    senddata[self.DATASIZE+5]=0x03
                    senddata[self.DATASIZE+6]=sum
                    senddata[self.DATASIZE+7]=0x0d
                    self.myser.write(senddata)
                    rstr=self.recvpack()
                    if(rstr!=b'[ack]'):
                        ret=False
                        break
                f.close()
            else:
                ret=False
        else:
            ret=False
        return ret
