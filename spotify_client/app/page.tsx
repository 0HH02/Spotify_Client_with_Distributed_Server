"use client";

import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { RetroMusicPlayer } from "@/components/RetroMusicPlayer";
import { SongList } from "@/components/SongList";
import { Menu } from "lucide-react"; // Importar ArrowRight
import serverManager from "@/middleware/ServerManager";

interface Song {
  title: string;
  artist: string;
  genre: string;
  album: string;
  image: string;
  duration: number;
  size: number;
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
      const base_server = server?.substring(0, server?.lastIndexOf("/"));
      const apiSongs = response.data.data.songs.map((song: Song) => ({
        title: song.title,
        artist: song.artist,
        genre: song.genre,
        album: song.album,
        coverUrl: `${base_server}/${song.image}`,
        duration: song.duration,
        fileSize: song.size,
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
      console.log(response.data.data);
      const base_server = server?.substring(0, server?.lastIndexOf("/"));
      const apiSongs = response.data.data.songs.map((song: Song) => ({
        title: song.title,
        artist: song.artist,
        genre: song.genre,
        album: song.album,
        coverUrl: `${base_server}/${song.image}`,
        duration: song.duration,
        fileSize: song.size,
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
          onSongUpload={async (file) => {
            // Implementa aquí la lógica de subir canción
            console.log("Subiendo archivo:", file.name);
            await fetchAllSongs();
          }}
          onHide={() => {
            setShowSongList(false);
            console.log("Slider ocultado");
          }}
        />
      </div>

      {/* Contenedor del Reproductor, ajusta el margen izquierdo según la visibilidad del slider */}
      <div
        className={`flex-1 flex justify-center items-center p-4 transition-all duration-300 ${showSongList ? "md:ml-80" : "md:ml-0"
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
