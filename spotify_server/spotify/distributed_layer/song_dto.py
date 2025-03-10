from ..logs import write_log


class SongKey:

    def __init__(self, title: str, artist: str):
        self.title: str = title
        self.artist: str = artist

    @staticmethod
    def from_string(key: str):
        info = key.split("-")
        if len(info) != 2:
            return None
        return SongKey(info[0], info[1])

    @property
    def key(self):
        return self.title, self.artist

    def __str__(self) -> str:
        return f"{self.title}-{self.artist}"

    def __eq__(self, value):
        return isinstance(value, SongKey) and str(self) == str(value)

    def __hash__(self):
        return hash(str(self))


class ImageSongDto:
    def __init__(self, file_extension: str, image_data: bytes):
        self.file_extension: str = file_extension
        self.image_data: bytes | None = image_data

    @staticmethod
    def from_dict(data: dict):
        try:
            return ImageSongDto(
                data["file_extension"],
                data["image_data"] if data["image_data"] else None,
            )
        except KeyError:
            write_log(f"Error al crear el objeto ImageSongDto with {data}", 3)
            return None
        except Exception as e:
            write_log(f"Error al crear imagenSongDto from dict {e}", 3)

    def to_dict(self) -> dict:
        return {
            "file_extension": self.file_extension,
        }

    def __str__(self) -> str:
        dct = self.to_dict()
        dct["image_data"] = "a lot of bytes"
        return dct.__str__()

    def __repr__(self):
        return self.__str__()


class SongDto:
    def __init__(
        self,
        title: str,
        artist: str,
        album: str,
        genre: str,
        duration: float,
        size: int,
        image: ImageSongDto,
        audio_data: bytes,
    ):
        self.title: str = title
        self.artist: str = artist
        self.album: str = album
        self.genre: str = genre
        self.duration: float = duration
        self.size: int = size
        self.image: ImageSongDto | None = image
        self.audio_data: bytes | None = audio_data

    @staticmethod
    def from_dict(data: dict):
        try:
            song = SongDto(
                title=data["title"],
                artist=data["artist"],
                album=data.get("album", "unknown"),
                genre=data.get("genre", "unknown"),
                duration=data["duration"],
                size=data["size"],
                image=ImageSongDto.from_dict(data["image"]),
                audio_data=data["audio_data"] if data["audio_data"] else None,
            )
            return song
        except Exception as e:
            write_log(f"Error al crear el objeto SongDto with : {e}", 3)
            return None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "duration": self.duration,
            "size": self.size,
            "image": self.image.to_dict() if self.image else None,
        }

    @property
    def key(self) -> SongKey:
        return SongKey(self.title, self.artist)

    def __str__(self):
        dct = self.to_dict()
        dct["audio_data"] = "a lot of bytes"
        dct["image"]["image_data"] = "a lot of bytes"
        return dct.__str__()

    def __repr__(self):
        return self.__str__()

    def __eq__(self, value):
        return isinstance(value, SongDto) and self.key == value.key

    def __hash__(self):
        return self.key.__hash__()


class SongMetadataDto:
    def __init__(
        self,
        title: str,
        artist: str,
        album: str,
        genre: str,
        duration: float,
        size: int,
        image_url: str,
    ):
        self.title: str = title
        self.artist: str = artist
        self.album: str = album
        self.genre: str = genre
        self.duration: float = duration
        self.size: int = size
        self.image_url: str = image_url

    @staticmethod
    def from_dict(data: dict):
        try:
            return SongMetadataDto(
                title=data["title"],
                artist=data["artist"],
                album=data["album"],
                genre=data["genre"],
                duration=data["duration"],
                size=data["size"],
                image_url=data["image"],
            )
        except KeyError:
            write_log(f"Error al crear el objeto SongMetadataDto with {data}", 3)
            return None

        except Exception as e:
            write_log(f"Error al crear SongMetadataDto from dict :{e}", 3)
            return None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "duration": self.duration,
            "size": self.size,
            "image": self.image_url,
        }

    @property
    def key(self) -> SongKey:
        return SongKey(self.title, self.artist)

    def __eq__(self, value):
        return isinstance(value, SongMetadataDto) and self.key == value.key

    def __hash__(self):
        return hash(self.key)

    def __str__(self):
        return self.key.__str__()

    def __repr__(self):
        return self.__str__()
