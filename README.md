# Protobuf Analyser

## Usage

This code has been created to debug the content of [protocol buffers](https://developers.google.com/protocol-buffers/docs/encoding).

As protobuf is created from a schema, and, in case of a bug, its content may not be according to any schema, it is interesting to have a code like this one, able to translate as far as possible a protobuf content without any schema, only based on the protobuf specification.

This script is used by calling it with the hexadecimal data to analyse:

    $ ProtoBufAnalyser.py 0a070880f0bfc1932e120208001a070880f0bfc1932e22177a150a13302e333131373433393138383538323437373648005a020801
    fieldNum=1 wire type=2 (Length-delimited)
        Read Length-delimited (hex): '0880f0bfc1932e' (ASCII): b'\x08\x80\xf0\xbf\xc1\x93.'
    fieldNum=2 wire type=2 (Length-delimited)
        Read Length-delimited (hex): '0800' (ASCII): b'\x08\x00'
    fieldNum=3 wire type=2 (Length-delimited)
        Read Length-delimited (hex): '0880f0bfc1932e' (ASCII): b'\x08\x80\xf0\xbf\xc1\x93.'
    fieldNum=4 wire type=2 (Length-delimited)
        Read Length-delimited (hex): '7a150a13302e3331313734333931383835383234373736' (ASCII): b'z\x15\n\x130.31174391885824776'
    fieldNum=9 wire type=0 (Varint)
        Read Varint: 0
    fieldNum=11 wire type=2 (Length-delimited)
        Read Length-delimited (hex): '0801' (ASCII): b'\x08\x01'
    End of protobuf reached without error
 
 Well note that because of the protobuf specification, a "Length-delimited" field can be interpreted again to check if another type is not encapsulated in it, as for the first field in the example above.
 
 We can provide as in input the hex value of the fieldNum=1 of the script output, to try to decode it and check if another field is not encapsulated in it:
 
    $ ProtoBufAnalyser.py 0880f0bfc1932e
    fieldNum=1 wire type=0 (Varint)
        Read Varint: 1585785600000
    End of protobuf reached without error
 
 To add the necessary debug code to print the protobuf content, use the following code:
 
 In C++:
 
    void traceData(void * dataPtr, int dataSize, std::string message)
    {
            if( dataPtr && dataSize ){
                    char dataStr[2*dataSize+1];
                    dataStr[2*dataSize] = 0;
                    unsigned char * memPtr = (unsigned char*) dataPtr;
                    for(int i=0;i<dataSize;i++) sprintf(&dataStr[2*i],"%02x",memPtr[i]);
                    std::cout << "DEBUG " << message << " size : " << dataSize << " data : " << dataStr << std::endl;
            } else {
                    std::cout << "DEBUG " << message << " data invalid, size: " << dataSize << " pointer: " << (unsigned long)(dataPtr) << std::endl;
            }
    }
  
  In Python:
  
      print("DEBUG proto of size {} and payload : {}".format(len(proto_content_as_bytearray),''.join(format(n, '02x') for n in proto_content_as_bytearray)))
      
## Limitations

Even if this script can return errors, if this script doesn't return any error, it doesn't mean that data is correct.

If the length of data match the specified protocol buffers fields, a meaning will be found for almost any binary values, even if the data doesn't match it intended defintion from its \*.proto file.

The next limitation of this script is that it translate Varint protocol buffers type as python int, which may lead to strange values in some cases, because protocol buffers specification also allow translation into : int32, int64, uint32, uint64, sint32, sint64, bool et enum.

Thus, it is possible that the value printed by this scipt for a Varint field doesn't correspond to the one given when decoding with the correct \*.proto file.
