import sys
from struct import pack, unpack


class CabFormatError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class PatchLengthError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Cab:
    def __init__(self, data):
        self.CFHEADER = CFHeader(data)
        self.CFFOLDER = CFFolder(data)
        self.CFFILE = CFFile(data)
        self.CFFDATA = CFFData(data, start=self.CFFILE.end_offset)

    @staticmethod
    def seek_null(data, start=0, chunk_size=24):
        chunk = data[start:start + chunk_size]
        index = chunk.find(b"\x00")
        return start + index if index > 0 else -1

    def change_set_id(self, value: int):
        self.CFHEADER.setID = value

    def zero_out_signature(self):
        self.CFFDATA.csum = 0

    def change_coff_cab_start(self, value: int):
        self.CFFOLDER.coffCabStart = value

    def change_ccfdata_count(self, value: int):
        self.CFFOLDER.cCFData = value

    def change_cffile_cbfile(self, value: int):
        self.CFFILE.cbFile = value

    def make_file_read_only(self):
        self.CFFILE.attribs |= 0x1
        self.CFFILE.attribs |= 0x2
        self.CFFILE.attribs |= 0x4

    def change_bytes(self, offset, size, value):
        if len(value) < size:
            raise PatchLengthError
        _bytes = bytearray(self.to_bytes())
        _bytes[offset:offset + size] = value[:size]
        return bytes(_bytes)

    def to_string(self):
        return rf"""
CFHeader: {self.CFHEADER.to_string()}
CFFolder: {self.CFFOLDER.to_string()}
CFFile: {self.CFFILE.to_string()}
CFFData: {self.CFFDATA.to_string()}
        """

    def to_bytes(self):
        return self.CFHEADER.to_bytes() + self.CFFOLDER.to_bytes() + self.CFFILE.to_bytes() + self.CFFDATA.to_bytes()


class CFHeader:
    def __init__(self, data):
        self.raw = data[:24]
        self.signature_display = data[:4].decode()
        self.signature = unpack("BBBB", data[:4])
        if self.signature_display != "MSCF":
            raise CabFormatError("Unknown signature")
        self.reserved1 = unpack("<I", data[4:8])[0]
        self.cbCabinet = unpack("<I", data[0x8:0xC])[0]
        self.reserved2 = unpack("<I", data[0xC:0x10])[0]
        self.coffFiles = unpack("<I", data[0x10:0x14])[0]
        self.reserved3 = unpack("<I", data[0x14:0x18])[0]
        self.versionMajor, self.versionMinor = unpack("BB", data[0x18:0x1A])
        self.cFolders = unpack("H", data[0x1A:0x1C])[0]
        self.cFiles = unpack("H", data[0x1C:0x1E])[0]
        self.flags = unpack("H", data[0x1E:0x20])[0]
        self.setID = unpack("H", data[0x20:0x22])[0]
        self.iCabinet = unpack("H", data[0x22:0x24])[0]

    def to_bytes(self):
        _to_bytes = pack("BBBB", self.signature[0], self.signature[1], self.signature[2], self.signature[3])
        _to_bytes += pack("<I", self.reserved1)
        _to_bytes += pack("<I", self.cbCabinet)
        _to_bytes += pack("<I", self.reserved2)
        _to_bytes += pack("<I", self.coffFiles)
        _to_bytes += pack("<I", self.reserved3)
        _to_bytes += pack("B", self.versionMajor)
        _to_bytes += pack("B", self.versionMinor)
        _to_bytes += pack("H", self.cFolders)
        _to_bytes += pack("H", self.cFiles)
        _to_bytes += pack("H", self.flags)
        _to_bytes += pack("H", self.setID)
        _to_bytes += pack("H", self.iCabinet)
        return _to_bytes

    def to_string(self):
        return rf"""
    Signature: {self.signature_display}
    Reserved1: {self.reserved1}
    CbCabinet: {self.cbCabinet}
    Reserved2: {self.reserved2}
    CoffFiles: {self.coffFiles}
    Reserved3: {self.reserved3}
    Version: {self.versionMajor}.{self.versionMinor}
    CFolders: {self.cFolders}
    CFiles: {self.cFiles}
    Flags: {self.flags}
    SetID: {self.setID}
    ICabinet: {self.iCabinet}
        """


class CFFolder:
    def __init__(self, data):
        self.raw = data[0x24:0x2B]
        self.coffCabStart = unpack("<I", data[0x24:0x28])[0]
        self.cCFData = unpack("H", data[0x28:0x2A])[0]
        self.typeCompress = unpack("H", data[0x2A:0x2C])[0]

    def to_bytes(self):
        _to_bytes = pack("<I", self.coffCabStart)
        _to_bytes += pack("H", self.cCFData)
        _to_bytes += pack("H", self.typeCompress)
        return _to_bytes

    def to_string(self):
        return rf"""
    CoffCabStart: {self.coffCabStart}
    CCFData: {self.cCFData}
    TypeCompress: {self.typeCompress}
            """


class CFFile:
    def __init__(self, data):
        self.raw = data[0x2C:0x44]
        self.cbFile = unpack("<I", data[0x2C:0x30])[0]
        self.uoffFolderStart = unpack("<I", data[0x30:0x34])[0]
        self.iFolder = unpack("H", data[0x34:0x36])[0]
        self.date = unpack("H", data[0x36:0x38])[0]
        self.time = unpack("H", data[0x38:0x3A])[0]
        self.attribs = unpack("H", data[0x3A:0x3C])[0]
        self.end_offset = Cab.seek_null(data, start=0x3C + 0x1, chunk_size=128) + 1
        self.szName = data[0x3C:self.end_offset].decode()

    def to_bytes(self):
        _to_bytes = pack("<I", self.cbFile)
        _to_bytes += pack("<I", self.uoffFolderStart)
        _to_bytes += pack("H", self.iFolder)
        _to_bytes += pack("H", self.date)
        _to_bytes += pack("H", self.time)
        _to_bytes += pack("H", self.attribs)
        _to_bytes += self.szName.encode()
        return _to_bytes

    def to_string(self):
        return rf"""
    CbFile: {self.cbFile}
    UoffFolderStart: {self.uoffFolderStart}
    IFolder: {self.iFolder}
    Date: {self.date}
    Time: {self.time}
    Attribs: {self.attribs}
    SzName: {self.szName}
            """


class CFFData:
    def __init__(self, data, start):
        self.raw = data[start:]
        self.csum = unpack("<I", data[start:start + 4])[0]
        self.cbData = unpack("H", data[start + 4:start + 6])[0]
        self.cbUncomp = unpack("H", data[start + 6:start + 8])[0]
        self.ab_display = data[start + 8:start + 18] + data[-10:]
        self.ab = self.raw[8:]

    def to_bytes(self):
        _to_bytes = pack("<I", self.csum)
        _to_bytes += pack("H", self.cbData)
        _to_bytes += pack("H", self.cbUncomp)
        _to_bytes += self.raw[8:]
        return _to_bytes

    def to_string(self):
        return rf"""
    Checksum: {self.csum}
    CbData: {self.cbData}
    CbUncompressed: {self.cbUncomp}
    Ab: {self.ab_display}
        """


def parse(file):
    data = open(file, "rb").read()
    cab = Cab(data=data)
    print(cab.to_string())


def change_e_magic(cab: Cab, value: bytes):
    if not value or not isinstance(value, bytes) or len(value) != 4:
        return
    new_cab = cab.change_bytes(offset=0x58, size=4, value=b"MZ\x90\x00")
    print(Cab(new_cab).to_string())


def save(cab: Cab, file: str):
    with open(file, "wb") as out:
        out.write(cab.to_bytes())


if __name__ == "__main__":
    parse(file=sys.argv[1])
