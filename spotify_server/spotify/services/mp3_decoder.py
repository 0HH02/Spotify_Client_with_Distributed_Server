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
        duration: float,
        album: str,
        image: ImageSong = None,
        genre: str | None = None,
    ) -> None:
        self.title: str = title
        self.artist: str = artist
        self.duration = duration
        self.genre: str | None = genre
        self.album: str = album
        self.image: ImageSong = image

    def get_metadata(self):
        return {
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "album": self.album,
            "genre": self.genre,
            "image": {
                "mime_type": self.image.file_extension,
                "image_data": self.image.image_data,
            },
        }

    @staticmethod
    def from_dict(data: dict) -> "DecodedSong":
        """
        Creates an instance of DecodedSong from a dictionary.

        Args:
            data (dict): A dictionary containing song information with keys:
                - "title" (str): The title of the song.
                - "artist" (str): The artist of the song.
                - "album" (str): The album of the song.
                - "genre" (str | None): The genre of the song.
                - "audio_data" (bytes): The audio data of the song.
                - "image" (dict | None): A dictionary containing image information with keys:
                    - "mime_type" (str): The MIME type of the image.
                    - "image_data" (bytes): The image data.

        Returns:
            DecodedSong: An instance of DecodedSong populated with the provided data.
        """
        title = data.get("title", "")
        artist = data.get("artist", "")
        duration = data.get("duration", 0)
        album = data.get("album", "")
        genre = data.get("genre", None)

        # Handle optional image data
        image_data = data.get("image")
        if image_data:
            image = ImageSong(
                file_extension=image_data.get("image_format", ""),
                image_data=image_data.get("image_data", b""),
            )
        else:
            image = None

        return DecodedSong(
            title=title,
            artist=artist,
            duration=duration,
            album=album,
            genre=genre,
            image=image,
        )


class Mp3Decoder:
    """
    Mp3Decoder is a class for decoding MP3 files, extracting metadata and duration.
    """

    BIT_RATE_TABLE: list[list[list[int]]] = [
        [
            [32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448],
            [32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],
            [32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
        ],
        [
            [32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
            [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
            [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
        ],
        [
            [32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
            [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
            [8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
        ],
    ]

    SAMPLING_RATE_FREQUENCY: list[list[int]] = [
        [44100, 48000, 32000],
        [22050, 24000, 16000],
        [11025, 12000, 8000],
    ]

    SAMPLES_PER_FRAME: list[list[int]] = [
        [384, 1152, 1152],
        [384, 1152, 576],
        [384, 1152, 576],
    ]

    @staticmethod
    def _syncsafe_to_int(syncsafe: bytes) -> int:
        """Converts a syncsafe integer to a regular integer."""
        return (
            (syncsafe[0] << 21) + (syncsafe[1] << 14) + (syncsafe[2] << 7) + syncsafe[3]
        )

    @staticmethod
    def parse_id3_frames(data: bytes, version=3) -> dict:
        """Parses ID3v2 frames to extract metadata."""

        images_starting_bytes: dict[str, list[bytes]] = {
            "jpeg": [b"\xFF\xD8\xFF\xE0", b"\xFF\xD8\xFF\xE1", b"\xFF\xD8\xFF\xDB"],
            "jpg": [b"\xFF\xD8\xFF\xE0", b"\xFF\xD8\xFF\xE1", b"\xFF\xD8\xFF\xDB"],
            "png": [b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"],
        }

        encoding_map: dict[int, str] = {
            0: "latin-1",
            1: "utf-16",
            2: "utf-16-be",
            3: "utf-8",
        }

        metadata = {}
        pointer = 0

        while pointer < len(data) - 10:

            frame_id: str = data[pointer : pointer + 4].decode("latin-1")
            frame_size: int = (
                int.from_bytes(data[pointer + 4 : pointer + 8], byteorder="big")
                if version == 3
                else (
                    Mp3Decoder._syncsafe_to_int(data[pointer + 4 : pointer + 8])
                    if version == 4
                    else 0
                )
            )
            if not frame_size > 0:
                break
            frame_content: bytes = data[pointer + 10 : pointer + 10 + frame_size]
            encoding: str = encoding_map.get(frame_content[0], "latin-1")
            frame_content = frame_content[1:]

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
                image_format = mime_type.split("/")[-1]

                # picture_type: int = frame_content[mime_end + 1]
                frame_content = frame_content[mime_end + 2 :]
                description_end: int = frame_content.find(
                    b"\x00\x00" if encoding == "utf-16" else b"\x00"
                )

                frame_content = frame_content[
                    description_end + (2 if encoding == "utf-16" else 1) :
                ]

                for s in images_starting_bytes.get(image_format, "jpeg"):
                    if frame_content.startswith(s):
                        metadata["image"] = {
                            "image_format": image_format,
                            "image_data": frame_content,
                        }
                        break
                else:
                    try:
                        image_start: int = frame_content.find(
                            images_starting_bytes[image_format][0]
                        )
                        image_data: bytes = frame_content[image_start:]
                        metadata["image"] = {
                            "mime_type": mime_type,
                            "image_data": image_data,
                        }
                    except Exception:
                        pass

            pointer += 10 + frame_size

        return metadata

    @staticmethod
    def parse_id3v1(data: bytes) -> dict:
        """
        Parse a ID3v1 tag to extract metadata.
        """
        enconding = "latin-1"
        genre: str = data[127:].decode(enconding).strip("\x00")
        metadata: dict[str, str | None] = {
            "title": data[:30].decode(enconding).strip("\x00"),
            "artist": data[30:60].decode(enconding).strip("\x00"),
            "album": data[60:90].decode(enconding).strip("\x00"),
            "genre": None if genre == "" else ID3V1_PREDEFINED_GENRES[int(genre)],
        }
        return metadata

    @staticmethod
    def calculate_duration(data: bytes) -> float:
        """
        Calculates the duration of the song based on MP3 frame headers.

        Args:
            data (bytes): Bytes of the MP3 file.

        Returns:
            float: Duration of the song in seconds.
        """
        pointer: int = 0
        duration: int = 0
        while pointer < len(data) - 1:

            sync: int = (data[pointer] << 3) | (data[pointer + 1] >> 5)
            if sync != 0x7FF:
                pointer += 1
                continue

            frame_header = data[pointer : pointer + 4]

            # This map represents the value of the version bits vs the real version:
            # 00 - MPEG version 2.5,
            # 01 - invalid version,
            # 10 - MPEG version 2,
            # 11 - MPEG version 1,
            version_map: dict[int, int] = {
                0: 3,
                1: -1,
                2: 2,
                3: 1,
            }

            # This map represents the value of the layer bits vs the real layer:
            # 00 - invalid layer,
            # 01 - Layer III,
            # 10 - Layer II,
            # 11 - Layer I,
            layer_map = {
                0: -1,
                1: 3,
                2: 2,
                3: 1,
            }

            # Parse MPEG header
            version: int = version_map.get((frame_header[1] >> 3) & 0x03)
            layer: int = layer_map.get((frame_header[1] >> 1) & 0x03)
            bitrate_index: int = (frame_header[2] >> 4) & 0x0F
            sampling_rate_index: int = (frame_header[2] >> 2) & 0x03
            padding_bit: int = (frame_header[2] >> 1) & 0x01

            if (
                version != -1
                and layer != -1
                and bitrate_index != 0xF
                and bitrate_index != 0x0
                and sampling_rate_index != 3
            ):

                bitrate: int = (
                    Mp3Decoder.BIT_RATE_TABLE[version - 1][layer - 1][bitrate_index - 1]
                    * 1000
                )

                sampling_rate: int = Mp3Decoder.SAMPLING_RATE_FREQUENCY[version][
                    sampling_rate_index
                ]
                samples_per_frame: int = Mp3Decoder.SAMPLES_PER_FRAME[version - 1][
                    layer - 1
                ]

                frame_length = int(
                    12 * bitrate / (sampling_rate + padding_bit) * 4
                    if layer == 1
                    else 144 * bitrate / (sampling_rate + padding_bit)
                )

                frame_duration: float = samples_per_frame / sampling_rate

                duration += frame_duration

                pointer += frame_length
            else:

                print("Invalid or corrupted frame")
                pointer += 4

        duration_in_minutes: float = duration // 60 + duration % 60 / 100

        return duration_in_minutes

    @staticmethod
    def decode(_bytes: bytes) -> dict:
        """
        Decodes MP3 bytes to extract metadata, audio data, and duration.

        Args:
            _bytes (bytes): The MP3 file bytes to decode.

        Returns:
            DecodedSong: An object containing metadata and audio data.

        Raises:
            ValueError: If required metadata is missing.
        """
        metadata: dict = {}

        if _bytes[:3] == b"ID3":

            # ID3v2
            major_version: int = _bytes[3]
            revision_number: int = _bytes[4]

            size = Mp3Decoder._syncsafe_to_int(_bytes[6:10])
            id3v2_data = _bytes[10 : 10 + size]

            # Process ID3v2 frames
            id3v2_metadata: dict = Mp3Decoder.parse_id3_frames(
                id3v2_data, major_version
            )
            metadata.update(id3v2_metadata)

        if _bytes[-128:-125] == b"TAG":
            id3v1_data: bytes = _bytes[-125:]
            id3v1_metadata: dict = Mp3Decoder.parse_id3v1(id3v1_data)

            for key, value in id3v1_metadata.items():
                if key not in metadata:
                    metadata[key] = value

        # Calculate duration
        duration = Mp3Decoder.calculate_duration(_bytes)
        metadata["duration"] = duration

        # Validate required metadata
        required_metadata = ["title", "artist", "album"]
        missing_metadata = [key for key in required_metadata if key not in metadata]
        if missing_metadata:
            raise ValueError(
                f"Missing required metadata: {', '.join(missing_metadata)}"
            )

        return DecodedSong.from_dict(metadata)


ID3V1_PREDEFINED_GENRES: dict[int, str] = {
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
