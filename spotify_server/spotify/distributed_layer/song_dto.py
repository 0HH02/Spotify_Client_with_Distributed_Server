class SongKey:

    def __init__(self, title: str, artist: str):
        self.title: str = title
        self.artist: str = artist

    @staticmethod
    def from_string(key: str) -> "SongKey":
        title, artist = key.split("-")
        return SongKey(title, artist)

    def __str__(self) -> str:
        return f"{self.title}-{self.artist}"

    def key(self) -> tuple[str, str]:
        return self.title, self.artist


class ImageSongDto:
    def __init__(self, file_extension: str, image_data: bytes):
        self.file_extension: str = file_extension
        self.image_data: bytes = image_data

    @staticmethod
    def from_dict(data: dict):
        return ImageSongDto(data["file_extension"], data["image_data"])

    def to_dict(self) -> dict:
        return {"file_extension": self.file_extension, "image_data": self.image_data}


class SongDto:
    def __init__(
        self,
        title: str,
        artist: str,
        album: str,
        genre: str,
        year: str,
        duration: float,
        size: int,
        image: ImageSongDto,
        audio_data: bytes,
    ):
        self.title: str = title
        self.artist: str = artist
        self.album: str = album
        self.genre: str = genre
        self.year: str = year
        self.duration: float = duration
        self.size: int = size
        self.image: ImageSongDto = image
        self.audio_data: bytes = audio_data

    @staticmethod
    def from_dict(data: dict):
        try:
            return SongDto(
                title=data["title"],
                artist=data["artist"],
                album=data["album"],
                genre=data["genre"],
                year=data["year"],
                duration=data["duration"],
                size=data["size"],
                image=ImageSongDto.from_dict(data["image"]),
                audio_data=data["audio_data"],
            )
        except KeyError:
            print(f"Error al crear el objeto SongDto with {data}")
            return None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "year": self.year,
            "duration": self.duration,
            "size": self.size,
            "image": self.image.to_dict(),
            "audio_data": self.audio_data,
        }

    @property
    def metadata(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "year": self.year,
            "duration": self.duration,
            "size": self.size,
            "image": self.image.to_dict(),
        }

    @property
    def key(self) -> SongKey:
        return SongKey(self.title, self.artist)
