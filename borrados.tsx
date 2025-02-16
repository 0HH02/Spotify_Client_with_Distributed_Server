import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Play, Pause, SkipBack, SkipForward } from "lucide-react";
import serverManager from "../middleware/ServerManager";
import Image from "next/image";
import { time } from "console";

const CHUNK_SIZE = 1024 * 512; // 512 KB chunk size

interface RetroMusicPlayerProps {
  songs: {
    id: string;
    title: string;
    artist: string;
    genre: string;
    album: string;
    coverUrl: string;
    duration: number;
    fileSize: number;
  }[];
  currentSongId: string;
  onSongSelect: (songId: string) => void;
  loading: boolean; // Nuevo prop para manejar el estado de carga
}

interface Song {
  id: string;
  title: string;
  artist: string;
  genre: string;
  album: string;
  coverUrl: string;
  duration: number;
  fileSize: number;
}

export const RetroMusicPlayer: React.FC<RetroMusicPlayerProps> = ({
  songs,
  currentSongId,
  onSongSelect,
  loading,
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [mediaSource, setMediaSource] = useState<MediaSource | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [sourceBuffer, setSourceBuffer] = useState<SourceBuffer | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [chunkList, setChunkList] = useState<{ index: number }[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isFetching, setIsFetching] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars

  const chunkListRef = useRef<{ index: number }[]>([]);
  const isFetchingRef = useRef(false);

  const currentSong =
    songs.find((song) => song.id === currentSongId) || ({} as Song);
  const [isDurationLoaded, setIsDurationLoaded] = useState(false);
  useEffect(() => {
    if (currentSong?.duration) {
      setIsDurationLoaded(true);
    }
  }, [currentSong]);

  useEffect(() => {
    if (!loading && currentSong.id) {
      const fetchAudioStream = async () => {
        if ("MediaSource" in window) {
          const mediaSrc = new MediaSource();
          setMediaSource(mediaSrc);

          mediaSrc.addEventListener("sourceopen", () => {
            if (mediaSrc.readyState !== "open") {
              console.warn("MediaSource is not open.");
              return;
            }
            const srcBuffer = mediaSrc.addSourceBuffer("audio/mpeg");
            setSourceBuffer(srcBuffer);

            if (audioRef.current) {
              audioRef.current.addEventListener("timeupdate", () => {
                setCurrentTime(audioRef.current?.currentTime || 0);
                monitorBuffer(srcBuffer, mediaSrc);
              });
            }

            // Cargar el primer chunk para obtener metadatos
            fetchAndAppendChunk(srcBuffer, 0, mediaSrc);
          });

          if (audioRef.current) {
            audioRef.current.src = URL.createObjectURL(mediaSrc);
          }
        } else {
          console.error("MediaSource API is not supported in this browser");
        }
      };

      fetchAudioStream();
    }
  }, [currentSong.id, loading]);

  useEffect(() => {
    if (audioRef.current && isPlaying) {
      audioRef.current.play().catch((e) => console.error("Play failed:", e));
    }
  }, [currentSongId, isPlaying]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onCanPlayThrough = () => {
      if (isPlaying) {
        audio.play().catch((e) => console.error("Play error:", e));
      }
    };

    audio.addEventListener("canplaythrough", onCanPlayThrough);

    return () => {
      audio.removeEventListener("canplaythrough", onCanPlayThrough);
    };
  }, [isPlaying, currentSongId]);

  function isTimeBuffered(time: number, srcBuffer: SourceBuffer): boolean {
    if (!srcBuffer?.buffered) return false;

    for (let i = 0; i < srcBuffer.buffered.length; i++) {
      const start = srcBuffer.buffered.start(i);
      const end = srcBuffer.buffered.end(i);
      if (time >= start && time <= end) {
        return true;
      }
    }
    return false;
  }

  const monitorBuffer = async (
    srcBuffer: SourceBuffer | null,
    mediaSrc: MediaSource
  ) => {
    if (!srcBuffer || mediaSrc.readyState !== "open") return;

    try {
      const nowTime = audioRef.current?.currentTime || 0;

      // 1. Checar si el tiempo actual está bufferizado:
      if (!isTimeBuffered(nowTime, srcBuffer)) {
        console.log(
          "El usuario saltó a un punto no bufferizado. Descargando chunk adecuado..."
        );

        const chunkIndex = timeToChunkIndex(
          nowTime,
          currentSong.duration,
          currentSong.fileSize,
          CHUNK_SIZE
        );
        console.log("New Chunk index:", chunkIndex);
        // ↑ Tienes que implementar la lógica de esta función (al final del ejemplo verás un pseudo-ejemplo).

        if (!isFetchingRef.current) {
          await fetchAndAppendChunk(srcBuffer, chunkIndex, mediaSrc);
        }
        return;
      }

      // 2. Si sí está bufferizado, aplicas la lógica que ya tenías de "descarga si me estoy quedando sin buffer"
      const bufferEnd =
        srcBuffer.buffered.length > 0 ? srcBuffer.buffered.end(0) : 0;
      if (!isFetchingRef.current && bufferEnd - nowTime < 5) {
        const lastChunkIndex =
          chunkListRef.current.length > 0
            ? chunkListRef.current[chunkListRef.current.length - 1].index
            : -1;
        const nextChunkIndex = lastChunkIndex + 1;
        console.log(
          "Buffer is running low. Fetching next chunk:",
          nextChunkIndex
        );
        await fetchAndAppendChunk(srcBuffer, nextChunkIndex, mediaSrc);
      }
    } catch (error) {
      console.error("Error while accessing the SourceBuffer:", error);
    }
  };

  const fetchAndAppendChunk = async (
    srcBuffer: SourceBuffer,
    chunkIndex: number,
    mediaSrc: MediaSource
  ) => {
    if (mediaSrc.readyState !== "open") return;

    try {
      setIsFetching(true);
      isFetchingRef.current = true;

      const rangeStart = chunkIndex * CHUNK_SIZE;
      const rangeEnd = (chunkIndex + 1) * CHUNK_SIZE - 1;

      // Middleware para manejar el stream
      const chunk = await serverManager.fetchStream(
        currentSong.id,
        rangeStart,
        rangeEnd
      );

      if (!chunk) {
        console.warn("No se pudo cargar el chunk, intentando de nuevo...");
        return await fetchAndAppendChunk(srcBuffer, chunkIndex, mediaSrc);
      }

      // Espera a que el SourceBuffer termine de actualizarse
      await new Promise<void>((resolve) => {
        if (!srcBuffer.updating) resolve();
        else
          srcBuffer.addEventListener("updateend", () => resolve(), {
            once: true,
          });
      });

      srcBuffer.appendBuffer(chunk);

      setChunkList((prev) => {
        const updatedChunks = [...prev, { index: chunkIndex }];
        chunkListRef.current = updatedChunks;
        return updatedChunks;
      });
    } catch (error) {
      console.error("Error al cargar el chunk:", error);
    } finally {
      setIsFetching(false);
      isFetchingRef.current = false;
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current && !loading) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleNextSong = () => {
    if (!songs || songs.length === 0) return;
    const currentIndex = songs.findIndex((song) => song.id === currentSongId);

    if (currentIndex >= 0 && currentIndex < songs.length - 1) {
      const nextSong = songs[currentIndex + 1];
      onSongSelect(nextSong.id);
      setIsPlaying(true); // Reproducir automáticamente
    } else {
      const firstSong = songs[0];
      onSongSelect(firstSong.id);
      setIsPlaying(true);
    }
  };

  const handlePreviousSong = () => {
    if (!songs || songs.length === 0) return;
    const currentIndex = songs.findIndex((song) => song.id === currentSongId);

    if (currentIndex > 0) {
      const prevSong = songs[currentIndex - 1];
      onSongSelect(prevSong.id);
      setIsPlaying(true); // Reproducir automáticamente
    } else {
      const lastSong = songs[songs.length - 1];
      onSongSelect(lastSong.id);
      setIsPlaying(true);
    }
  };

  const handleSeek = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current || !currentSong) return;

    const newTime = parseFloat(e.target.value);

    // 1. Pausar temporalmente para evitar "saltos" o "congelamientos".
    audioRef.current.pause();
    setIsPlaying(false);

    // 2. Determinar el chunk necesario para la nueva posición.
    const chunkIndex = timeToChunkIndex(
      newTime,
      currentSong.duration,
      currentSong.fileSize,
      CHUNK_SIZE
    );

    // 3. Verificar si NO está en buffer. Si no lo está, forzar la descarga.
    if (sourceBuffer && mediaSource?.readyState === "open") {
      if (!isTimeBuffered(newTime, sourceBuffer)) {
        await fetchAndAppendChunk(sourceBuffer, chunkIndex, mediaSource);
      }
    }

    // 4. Actualizar el tiempo y reanudar la reproducción.
    audioRef.current.currentTime = newTime;
    await audioRef.current.play().catch((err) => console.error(err));
    setIsPlaying(true);
  };

  function timeToChunkIndex(
    time: number,
    duration: number,
    fileSize: number,
    CHUNK_SIZE: number
  ): number {
    if (duration <= 0 || fileSize <= 0) return 0;
    const byteOffset = Math.floor((time / duration) * fileSize); // tiempo -> bytes
    return Math.floor(byteOffset / CHUNK_SIZE);
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex-1 bg-gradient-to-b from-purple-800 to-indigo-900 p-8 rounded-xl overflow-hidden flex flex-col justify-center items-center">
      <div className="w-full max-w-md">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="relative aspect-square mb-8 overflow-hidden rounded-lg"
        >
          <Image
            src={currentSong.coverUrl || "https://via.placeholder.com/300"}
            alt={`${currentSong.title || "No song loaded"} cover`}
            width={300} // Ancho requerido
            height={300} // Alto requerido
            className="w-full h-full object-cover"
            priority
          />
        </motion.div>
        <motion.h2
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-3xl font-bold text-white mb-2 truncate text-center"
        >
          {currentSong.title || "Loading..."}
        </motion.h2>
        <motion.p
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="text-purple-200 mb-6 text-center"
        >
          {currentSong.artist || "Loading..."}
        </motion.p>
        <div className="flex items-center justify-between mb-4">
          <span className="text-purple-200 text-sm">
            {formatTime(currentTime)}
          </span>
          <input
            type="range"
            min={0}
            max={
              currentSong?.duration &&
              Math.floor(currentSong?.duration) * 60 +
                currentSong?.duration -
                Math.floor(currentSong?.duration)
            }
            value={currentTime}
            onChange={handleSeek}
            className="w-full mx-2 accent-purple-500"
            disabled={loading || !isDurationLoaded} // Deshabilitar durante la carga
          />
          <span className="text-purple-200 text-sm">
            {currentSong.duration
              ? Math.floor(currentSong?.duration).toString() +
                ":" +
                (Math.floor(
                  (currentSong?.duration - Math.floor(currentSong?.duration)) *
                    100
                ).toString().length == 1
                  ? "0" +
                    Math.floor(
                      (currentSong?.duration -
                        Math.floor(currentSong?.duration)) *
                        100
                    ).toString()
                  : Math.floor(
                      (currentSong?.duration -
                        Math.floor(currentSong?.duration)) *
                        100
                    ).toString())
              : ""}
          </span>
        </div>
        <div className="flex justify-center items-center space-x-6">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="text-white p-3 rounded-full bg-purple-700 hover:bg-purple-600 transition-colors"
            onClick={handlePreviousSong} // Agregar esta función
          >
            <SkipBack size={24} />
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className={`text-white p-5 rounded-full ${
              loading
                ? "bg-gray-600 cursor-not-allowed"
                : "bg-purple-600 hover:bg-purple-500"
            } transition-colors`}
            onClick={togglePlayPause}
            disabled={loading} // Botón deshabilitado durante la carga
          >
            {isPlaying ? <Pause size={36} /> : <Play size={36} />}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="text-white p-3 rounded-full bg-purple-700 hover:bg-purple-600 transition-colors"
            onClick={handleNextSong} // Agregar esta función
          >
            <SkipForward size={24} />
          </motion.button>
        </div>
        <audio ref={audioRef} />
      </div>
    </div>
  );
};

import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { RetroMusicPlayer } from "@/components/RetroMusicPlayer";
import { SongList } from "@/components/SongList";
import { Menu } from "lucide-react"; // Importar ArrowRight
import serverManager from "@/middleware/ServerManager";

interface Song {
  id: number;
  title: string;
  artist: string;
  genre: string;
  album: string;
  image: string;
  duration: number;
  fileSize: number;
}

export default function Home() {
  const [songs, setSongs] = useState([]);
  const [currentSongId, setCurrentSongId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortType, setSortType] = useState<
    "all" | "artist" | "genre" | "album"
  >("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showSongList, setShowSongList] = useState(true); // Inicialmente visible

  useEffect(() => {
    fetchAllSongs();
  }, []);

  const fetchAllSongs = async () => {
    setLoading(true);
    try {
      const server = await serverManager.getAvailableServer();
      const response = await axios.get(`${server}/api/songs/`);
      const apiSongs = response.data.data.map((song: Song) => ({
        id: song.id.toString(),
        title: song.title,
        artist: song.artist,
        genre: song.genre,
        album: song.album,
        coverUrl: `${server}${song.image}`,
        duration: song.duration,
      }));
      setSongs(apiSongs);
      if (apiSongs.length > 0) setCurrentSongId(apiSongs[0].id);
    } catch (error) {
      console.error("Error fetching songs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSongsBySearch = async (type: string, term: string) => {
    setLoading(true);
    try {
      const searchBy = type === "all" ? "title" : type;
      const server = await serverManager.getAvailableServer();
      const response = await axios.get(
        `${server}/api/search/?searchBy=${searchBy}&query=${encodeURIComponent(
          term
        )}`
      );
      const apiSongs = response.data.data.map((song: Song) => ({
        id: song.id.toString(),
        title: song.title,
        artist: song.artist,
        genre: song.genre,
        album: song.album,
        coverUrl: "default_image.jpg",
      }));
      setSongs(apiSongs);
      if (apiSongs.length > 0) setCurrentSongId(apiSongs[0].id);
    } catch (error) {
      console.error("Error searching songs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchCriteriaChange = useCallback(
    (newSortType: string, newSearchTerm: string) => {
      if (newSearchTerm.trim() === "") {
        fetchAllSongs();
      } else {
        fetchSongsBySearch(newSortType, newSearchTerm);
      }
    },
    []
  );

  const updateSortType = (type: "all" | "artist" | "genre" | "album") => {
    setSortType(type);
    handleSearchCriteriaChange(type, searchTerm);
  };

  const updateSearchTerm = (term: string) => {
    setSearchTerm(term);
    handleSearchCriteriaChange(sortType, term);
  };

  return (
    <main className="flex flex-col md:flex-row min-h-screen bg-gradient-to-br from-indigo-900 to-purple-900 relative">
      {/* Botón para abrir la lista en dispositivos móviles (solo visible cuando el slider está oculto) */}
      {!showSongList && (
        <button
          className="absolute top-4 left-4 z-50 p-2 bg-purple-700 rounded-md text-white "
          onClick={() => setShowSongList(true)}
          aria-label="Mostrar Playlist"
        >
          <Menu size={24} />
        </button>
      )}

      {/* Contenedor de la lista de canciones */}
      <div
        className={`
          fixed top-0 left-0 h-full bg-purple-900 transform transition-transform duration-300 
          ${showSongList ? "translate-x-0" : "-translate-x-full"} 
          md:w-80 w-64 z-40
        `}
      >
        <SongList
          songs={songs}
          currentSongId={currentSongId || ""}
          onSongSelect={setCurrentSongId}
          sortType={sortType}
          searchTerm={searchTerm}
          onSortTypeChange={updateSortType}
          onSearchTermChange={updateSearchTerm}
          onSongUpload={(file) => {
            // Implementa aquí la lógica de subir canción
            console.log("Subiendo archivo:", file.name);
          }}
          onHide={() => {
            setShowSongList(false);
            console.log("Slider ocultado");
          }}
        />
      </div>

      {/* Contenedor del Reproductor, ajusta el margen izquierdo según la visibilidad del slider */}
      <div
        className={`flex-1 flex justify-center items-center p-4 transition-all duration-300 ${
          showSongList ? "md:ml-80" : "md:ml-0"
        }`}
      >
        <RetroMusicPlayer
          songs={songs}
          currentSongId={currentSongId || ""}
          onSongSelect={setCurrentSongId}
          loading={loading}
        />
      </div>
    </main>
  );
}
