class ImageSong:
    def __init__(self, file_extension: str, image_data: bytes) -> None:
        self.file_extension: str = file_extension
        self.image_data: bytes = image_data


class DecodedSong:
    """
    A class to represent a decoded song with its metadata and audio data.

    Attributes:
        title (str): The title of the song.
        artist (str): The artist of the song.
        album (str): The album of the song.
        genre (str | None): The genre of the song.
        audio_data (bytes): The audio data of the song.
        image (ImageSong): An instance of ImageSong containing image information.

    Methods:
        from_dict(data: dict) -> "DecodedSong":
    """

    def __init__(
        self,
        title: str,
        artist: str,
        album: str,
        audio_data: bytes,
        image: ImageSong = None,
        genre: str | None = None,
    ) -> None:
        self.title: str = title
        self.artist: str = artist
        self.genre: str | None = genre
        self.album: str = album
        self.audio_data: bytes = audio_data
        self.image: ImageSong = image

    def get_metadata(self):
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "image": {
                "mime_type": self.image.file_extension,
                "image_data": self.image.image_data,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecodedSong":
        """
        Creates an instance of DecodedSong from a dictionary.

        Args:
            data (dict): A dictionary containing song information with keys:
                - "title" (str): The title of the song.
                - "artist" (str): The artist of the song.
                - "album" (str): The album of the song.
                - "genre" (str): The genre of the song.
                - "audio_data" (bytes): The audio data of the song.
                - "image" (dict): A dictionary containing image information with keys:
                    - "mime_type" (str): The MIME type of the image.
                    - "image_data" (bytes): The image data.

        Returns:
            DecodedSong: An instance of DecodedSong populated with the provided data.
        """
        cls.title = data["title"]
        cls.artist = data["artist"]
        cls.album = data["album"]
        cls.genre = data["genre"]
        cls.audio_data = data["audio_data"]
        cls.image = ImageSong(data["image"]["mime_type"], data["image"]["image_data"])


class Mp3Decoder:
    """
    Mp3Decoder is a utility class for decoding MP3 files and extracting metadata.
    Methods:
        decode(_bytes: bytes) -> tuple:
            Supports both ID3v1 and ID3v2 metadata formats.
    """

    @staticmethod
    def _syncsafe_to_int(syncsafe: bytes) -> int:
        """ """
        return (
            (syncsafe[0] << 21) + (syncsafe[1] << 14) + (syncsafe[2] << 7) + syncsafe[3]
        )

    @staticmethod
    def parse_id3v2_frames(data: bytes) -> dict:
        """ """
        metadata = {}
        pointer = 0

        while pointer < len(data) - 10:
            frame_id: str = data[pointer : pointer + 4].decode("latin-1").strip()
            frame_size: int = int.from_bytes(
                data[pointer + 4 : pointer + 8], byteorder="big"
            )
            if not frame_size > 0:
                break
            frame_content: bytes = data[pointer + 10 : pointer + 10 + frame_size]
            encoding: str = "utf-16" if frame_content[0] == 1 else "latin-1"
            frame_content = (
                frame_content[1:] if frame_content[0] == 1 else frame_content
            )
            if frame_id == "TIT2":  # title label
                metadata["title"] = frame_content.decode(encoding).strip("\x00")
            elif frame_id == "TPE1":  # artist label
                metadata["artist"] = frame_content.decode(encoding).strip("\x00")
            elif frame_id == "TALB":  # album label
                metadata["album"] = frame_content.decode(encoding).strip("\x00")
            elif frame_id == "TCON":  # genre label
                metadata["genre"] = frame_content.decode(encoding).strip("\x00")
            elif frame_id == "APIC":  # image label
                mime_end: int = frame_content.find(b"\x00")
                mime_type: str = frame_content[:mime_end].decode("latin-1")
                image_data: bytes = frame_content[
                    mime_end + 2 :
                ]  # Saltar descripción y tipo de imagen
                metadata["image"] = {
                    "mime_type": mime_type,
                    "image_data": image_data,
                }
            pointer += 10 + frame_size

        return metadata

    @staticmethod
    def parse_id3v1(data: bytes):
        """
        Parse a ID3v1 tag to extract metadata.
        """
        enconding = "latin-1"
        genre: str = data[127:].decode(enconding).strip("\x00")
        metadata: dict[str, str | None] = {
            "title": data[:30].decode(enconding).strip("\x00"),
            "artist": data[30:60].decode(enconding).strip("\x00"),
            "album": data[60:90].decode(enconding).strip("\x00"),
            "genre": None if genre == "" else id3v1_predefined_genres[int(genre)],
        }
        return metadata

    @staticmethod
    def decode(_bytes: bytes) -> DecodedSong:
        """
        Decodes MP3 bytes to extract metadata and audio data.

        This function processes the given MP3 bytes to extract metadata from ID3v2 and ID3v1 tags, if present,
        and returns a DecodedSong object containing the metadata and audio data.

        Args:
            _bytes (bytes): The MP3 file bytes to decode.

        Returns:
            DecodedSong: An object containing the extracted metadata and audio data.

        Raises:
            ValueError: If the metadata format is incorrect or required metadata is missing.
        """

        metadata: dict = {}
        audio_data: bytes = _bytes

        if _bytes[:3] == b"ID3":
            # ID3v2
            version = _bytes[3:5]
            flags = _bytes[5]
            size = Mp3Decoder._syncsafe_to_int(_bytes[6:10])
            id3v2_data = _bytes[10 : 10 + size]

            # Procesar los marcos ID3v2
            id3v2_metadata: dict = Mp3Decoder.parse_id3v2_frames(id3v2_data)
            metadata.update(id3v2_metadata)
            audio_data = _bytes[10 + size :]

        if _bytes[-128:-125] == b"TAG":
            id3v1_data: bytes = _bytes[-125:]
            id3v1_metadata: dict[str, str | None] = Mp3Decoder.parse_id3v1(id3v1_data)

            for key, value in id3v1_metadata.items():
                if key not in metadata:
                    metadata[key] = value

        metadata["audio_data"] = audio_data

        # TODO - manage errors in metadata format with try-except and verify that all the metadata required are present
        return DecodedSong.from_dict(metadata)


id3v1_predefined_genres: dict[int, str] = {
    0: "Blues",
    1: "Classic Rock",
    2: "Country",
    3: "Dance",
    4: "Disco",
    5: "Funk",
    6: "Grunge",
    7: "Hip-Hop",
    8: "Jazz",
    9: "Metal",
    10: "New Age",
    11: "Oldies",
    12: "Other",
    13: "Pop",
    14: "R&B",
    15: "Rap",
    16: "Reggae",
    17: "Rock",
    18: "Techno",
    19: "Industrial",
    20: "Alternative",
    21: "Ska",
    22: "Death Metal",
    23: "Pranks",
    24: "Soundtrack",
    25: "Euro-Techno",
    26: "Ambient",
    27: "Trip-Hop",
    28: "Vocal",
    29: "Jazz+Funk",
    30: "Fusion",
    31: "Trance",
    32: "Classical",
    33: "Instrumental",
    34: "Acid",
    35: "House",
    36: "Game",
    37: "Sound Clip",
    38: "Gospel",
    39: "Noise",
    40: "AlternRock",
    41: "Bass",
    42: "Soul",
    43: "Punk",
    44: "Space",
    45: "Meditative",
    46: "Instrumental Pop",
    47: "Instrumental Rock",
    48: "Ethnic",
    49: "Gothic",
    50: "Darkwave",
    51: "Techno-Industrial",
    52: "Electronic",
    53: "Pop-Folk",
    54: "Eurodance",
    55: "Dream",
    56: "Southern Rock",
    57: "Comedy",
    58: "Cult",
    59: "Gangsta",
    60: "Top 40",
    61: "Christian Rap",
    62: "Pop/Funk",
    63: "Jungle",
    64: "Native American",
    65: "Cabaret",
    66: "New Wave",
    67: "Psychadelic",
    68: "Rave",
    69: "Showtunes",
    70: "Trailer",
    71: "Lo-Fi",
    72: "Tribal",
    73: "Acid Punk",
    74: "Acid Jazz",
    75: "Polka",
    76: "Retro",
    77: "Musical",
    78: "Rock & Roll",
    79: "Hard Rock",
    80: "Folk",
    81: "Folk-Rock",
    82: "National Folk",
    83: "Swing",
    84: "Fast Fusion",
    85: "Bebop",
    86: "Latin",
    87: "Revival",
    88: "Celtic",
    89: "Bluegrass",
    90: "Avantgarde",
    91: "Gothic Rock",
    92: "Progressive Rock",
    93: "Psychedelic Rock",
    94: "Symphonic Rock",
    95: "Slow Rock",
    96: "Big Band",
    97: "Chorus",
    98: "Easy Listening",
    99: "Acoustic",
    100: "Humour",
    101: "Speech",
    102: "Chanson",
    103: "Opera",
    104: "Chamber Music",
    105: "Sonata",
    106: "Symphony",
    107: "Booty Bass",
    108: "Primus",
    109: "Porn Groove",
    110: "Satire",
    111: "Slow Jam",
    112: "Club",
    113: "Tango",
    114: "Samba",
    115: "Folklore",
    116: "Ballad",
    117: "Power Ballad",
    118: "Rhythmic Soul",
    119: "Freestyle",
    120: "Duet",
    121: "Punk Rock",
    122: "Drum Solo",
    123: "A Capella",
    124: "Euro-House",
    125: "Dance Hall",
    126: "Goa",
    127: "Drum & Bass",
    128: "Club-House",
    129: "Hardcore",
    130: "Terror",
    131: "Indie",
    132: "BritPop",
    133: "Negerpunk",
    134: "Polsk Punk",
    135: "Beat",
    136: "Christian Gangsta Rap",
    137: "Heavy Metal",
    138: "Black Metal",
    139: "Crossover",
    140: "Contemporary Christian",
    141: "Christian Rock",
    142: "Merengue",
    143: "Salsa",
    144: "Thrash Metal",
    145: "Anime",
    146: "JPop",
    147: "Synthpop",
    148: "Abstract",
    149: "Art Rock",
    150: "Baroque",
    151: "Bhangra",
    152: "Big Beat",
    153: "Breakbeat",
    154: "Chillout",
    155: "Downtempo",
    156: "Dub",
    157: "EBM",
    158: "Eclectic",
    159: "Electro",
    160: "Electroclash",
    161: "Emo",
    162: "Experimental",
    163: "Garage",
    164: "Global",
    165: "IDM",
    166: "Illbient",
    167: "Industro-Goth",
    168: "Jam Band",
    169: "Krautrock",
    170: "Leftfield",
    171: "Lounge",
    172: "Math Rock",
    173: "New Romantic",
    174: "Nu-Breakz",
    175: "Post-Punk",
    176: "Post-Rock",
    177: "Psytrance",
    178: "Shoegaze",
    179: "Space Rock",
    180: "Trop Rock",
    181: "World Music",
    182: "Neoclassical",
    183: "Audiobook",
    184: "Audio Theatre",
    185: "Neue Deutsche Welle",
    186: "Podcast",
    187: "Indie Rock",
    188: "G-Funk",
    189: "Dubstep",
    190: "Garage Rock",
    191: "Psybient",
}
