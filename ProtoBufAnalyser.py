#!/usr/bin/python
# -*- coding: latin-1 -*-
# Code made for Python 2.6 on Linux
import sys
from struct import unpack

class ProtoBufAnalyserError(Exception):
    """
    Class for error in the parameters provided to this script
    """
    def __init__(self, msg):    
        print "ERROR : " + msg
        sys.exit(1)
        pass

class ProtoBufAnalyser(object):
    '''
    This class is designed to analyse a protobuf content without proto file
    All details in https://developers.google.com/protocol-buffers/docs/encoding
    '''
    def __init__(self, protobuf):
        '''
        Initialize analyser
        protobuf : protobuf to analyse in string coding the protobuf content in hexadecimal 
        '''
        self._data = protobuf
        self._readIdx = 0
        self._wireTypes = ['Varint','64-bit','Length-delimited','Start group','End group','32-bit']

    def analyse(self):
        '''
        Analyse the protobuf
        '''
        stop  = False
        while stop == False:
            fieldNum, wireType = self.readKey()
            if wireType >= 0 and wireType <= 5:
                 print "fieldNum=" + repr(fieldNum) + " wire type=" + repr(wireType) + " ("  + self._wireTypes[wireType] + ")"
            if wireType == 0: #Varint
                val = self.readVarint()
                print "    Read Varint: " + repr(val)
            elif wireType == 1: #64-bit (16 hex char)
                signedFixed, unsignedFixed, floatingPoint = self.readFixedLen(16)
                print "    Read 64-bit: " + repr(signedFixed) + " (fixed64) " + repr(unsignedFixed) + " (unsigned fixed64) " + repr(floatingPoint) + " (float64) "
            elif wireType == 2: #Length-delimited
                val = self.readDelimited()
                try:
                    asciiVal = " (ASCII): " + val.decode('hex')
                except TypeError as e:
                    raise ProtoBufAnalyserError("Odd hexadecimal data lengh which doesn't correspond to bytes : " + str(e) )
                print "    Read Length-delimited (hex): " + repr(val) + asciiVal
            elif wireType == 3: #Start group (deprecated)
                stop  = True
                raise ProtoBufAnalyserError("Start group field detected but this is a depricated protobuf field not supported by this script" )
            elif wireType == 4: #End group (deprecated)
                stop  = True
                raise ProtoBufAnalyserError("End group field detected but this is a depricated protobuf field not supported by this script" )
            elif wireType == 5: #32-bit (8 hex char)
                signedFixed, unsignedFixed, floatingPoint = self.readFixedLen(8)
                print "    Read 32-bit: " + repr(signedFixed) + " (fixed32) " + repr(unsignedFixed) + " (unsigned fixed32) " + repr(floatingPoint) + " (float32) "
            else:
                stop = True
                raise ProtoBufAnalyserError("Invalid wire type detected : " + repr(wireType) + " with field number: " + repr(fieldNum) )
            if self._readIdx >= len(self._data):
                stop = True
                print "End of protobuf reached without error"

    def readKey(self):
        '''
        Read protobuf key and return field num and wire type
        '''
        key = format(self.readVarint(),'08b')
        if not len(key) :
            raise ProtoBufAnalyserError("Invalid key value: " + key)
        # Read the specified variable lengh field (lengh is twice the specified value due to hexadecimal representation)        
        wireType = int(key[-3:],2)
        fieldNum = int(key[:-3],2)
        return fieldNum, wireType

    def readDelimited(self):
        '''
        Read a Length-delimited from index and return its value
        '''
        lengh = self.readVarint()
        # Check if data lengh correspond to specified field lengh
        if len(self._data) < ( self._readIdx+(2*lengh) ):
            if (len(self._data)-self._readIdx) > 0:
                raise ProtoBufAnalyserError("Length-delimited field specified lengh is " + repr(2*lengh) + " hex characters and given data lengh is " + repr(len(self._data)-self._readIdx) )
            else:
                raise ProtoBufAnalyserError("Length-delimited field specified lengh is " + repr(2*lengh) + " the end of given data has been reached" )
        # Read the specified variable lengh field (lengh is twice the specified value due to hexadecimal representation)
        value = self._data[self._readIdx:self._readIdx+(2*lengh)]
        # Update read index
        self._readIdx = self._readIdx + (2*lengh)
        return value

    def readFixedLen(self,lengh):
        '''
        Read a fix lengh value from index and return its value as hexadecimal in a str
        Protobuf implementation use this coding for
        Lengh = 32 for fixed32, sfixed32, float
        Lengh = 64 for fixed64, sfixed64, double
        return signedFixed, unsignedFixed and floatingPoint versions of the read data
        '''
        #Fix lengh value are little endiand (LSB first)
        StrVal = ""
        # Check if data lengh correspond to specified field lengh
        if len(self._data) < ( self._readIdx+(lengh) ):
            if (len(self._data)-self._readIdx) > 0:
                raise ProtoBufAnalyserError("FixedLength field specified lengh is " + repr(lengh) + " hex characters and given data lengh is " + repr(len(self._data)-self._readIdx) )
            else:
                raise ProtoBufAnalyserError("FixedLength field specified lengh is " + repr(lengh) + " and the end of given data has been reached" )
        # Read the hexadecimal data 2 characters at a time to actually read a byte of data
        for i in range(lengh/2):
            # Decode from little endian, first bytes are less significants
            StrVal = self._data[self._readIdx:self._readIdx+2] + StrVal
            # Get the next byte of varint (2 step because of byte size in hexa coded in string)
            self._readIdx = self._readIdx + 2
        # Generate the fixed point signed and unsigned and floating point result depending on data width
        if lengh == 16 : # 64 bits
            signedFixed = unpack('!q', StrVal.decode('hex'))[0]
            unsignedFixed = unpack('!Q', StrVal.decode('hex'))[0]
            floatingPoint = unpack('!d', StrVal.decode('hex'))[0]
        if lengh == 8 : # 32 bits
            signedFixed = unpack('!l', StrVal.decode('hex'))[0]
            unsignedFixed = unpack('!L', StrVal.decode('hex'))[0]
            floatingPoint = unpack('!f', StrVal.decode('hex'))[0]
        return signedFixed, unsignedFixed, floatingPoint
        
        
    def readVarint(self):
        '''
        Read a Varint from index and return its value as int
        '''
        retVarint = ""
        # Read at index and get binary representation in string
        # taking chars 2 by 2 because of hexadecimal representation of bytes
        isLast, binaryVal = self.getBinValFromVarintByte(self._data[self._readIdx:self._readIdx+2])
        retVarint = binaryVal + retVarint
        # Get the next byte of varint (2 step because of byte size in hexa coded in string)
        self._readIdx = self._readIdx + 2
        # The byte is not the last of the varint
        while not isLast:
            isLast, binaryVal = self.getBinValFromVarintByte(self._data[self._readIdx:self._readIdx+2])
            retVarint = binaryVal + retVarint
            # Get the next byte of varint (2 step because of byte size in hexa coded in string)
            self._readIdx = self._readIdx + 2
        return int(retVarint,2)
        
    def getBinValFromVarintByte(self, varint):
        '''
        Get partial binary value of varint value from a byte and isLast flag
        Return isLast as bool and value as string representing binary
        '''
        if not len(varint):
            raise ProtoBufAnalyserError("Invalid lengh of data to decode this varint value")
        isLast = True
        binaryVal = bin(int(varint, 16))[2:].zfill(8)
        if binaryVal[0] == "1":
            isLast = False
        # Drop the msb
        return isLast, binaryVal[1:]
        
                

if __name__ == '__main__':
    
    if len(sys.argv) == 2:
        myAnalyser = ProtoBufAnalyser(sys.argv[1])
        myAnalyser.analyse()
    else:
        print('Missing parameter  : Protobuf in hexadecimal representation in string')
