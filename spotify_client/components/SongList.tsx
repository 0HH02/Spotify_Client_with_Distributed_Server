import React, { useState, useRef } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Music,
  User,
  Disc,
  Album,
  Upload,
  ArrowLeft,
} from "lucide-react"; // Importar ArrowLeft
import serverManager from "@/middleware/ServerManager";
import Image from "next/image";

interface Song {
  id: string;
  title: string;
  artist: string;
  genre: string;
  album: string;
  coverUrl: string;
}

interface SongListProps {
  songs: Song[];
  currentSongId: string;
  onSongSelect: (songId: string) => void;
  onSongUpload: (file: File) => void;
  sortType: string;
  searchTerm: string;
  onSortTypeChange: (type: "all" | "artist" | "genre" | "album") => void;
  onSearchTermChange: (term: string) => void;
  onHide: () => void; // Nueva prop para ocultar la lista
}

type SortType = "all" | "artist" | "genre" | "album";

export const SongList: React.FC<SongListProps> = ({
  songs,
  currentSongId,
  onSongSelect,
  onSongUpload,
  sortType,
  searchTerm,
  onSortTypeChange,
  onSearchTermChange,
  onHide,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (file && file.type === "audio/mpeg") {
      try {
        const formData = new FormData();
        formData.append("file", file); // 'file' es el nombre esperado por el servidor
        const server = await serverManager.getAvailableServer("none", "none");
        const response = await fetch(`${server}/api/upload/`, {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          alert("Archivo subido correctamente.");
          onSongUpload(file); // Actualiza el estado local
        } else {
          const errorData = await response.json();
          alert(
            `Error en la subida: ${errorData.message || "Error desconocido"}`
          );
        }
      } catch (error) {
        console.error("Error al subir el archivo:", error);
        alert("Ocurrió un error al subir el archivo.");
      }
    } else {
      alert("Por favor, selecciona un archivo MP3 válido.");
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type === "audio/mpeg") {
      onSongUpload(file);
    } else {
      alert("Por favor, suelta un archivo MP3 válido.");
    }
  };

  const SortIcon = ({
    type,
    icon: Icon,
  }: {
    type: SortType;
    icon: React.ElementType;
  }) => (
    <motion.div
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={() => onSortTypeChange(type)}
      className={`cursor-pointer p-2 rounded-full ${
        sortType === type ? "bg-purple-600" : "bg-purple-800"
      }`}
    >
      <Icon size={20} className="text-white" />
    </motion.div>
  );

  return (
    <div className="bg-gradient-to-b from-purple-900 to-indigo-800 h-full overflow-hidden flex flex-col relative">
      <div className="p-6 pb-0 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Playlist</h2>
        {/* Botón para ocultar la lista en todas las pantallas */}
        <button
          className="p-2 bg-purple-700 rounded-full text-white"
          onClick={onHide}
          aria-label="Hide Playlist"
        >
          <ArrowLeft size={20} />
        </button>
      </div>
      <div className="p-6">
        <div className="relative mb-4 flex items-center">
          <input
            type="text"
            placeholder="Buscar..."
            value={searchTerm}
            onChange={(e) => onSearchTermChange(e.target.value)}
            className="w-full bg-purple-800 text-white placeholder-purple-300 border border-purple-600 rounded-md py-2 pl-10 pr-12 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <Search
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-300"
            size={20}
          />
        </div>
        <div className="flex justify-between mb-4">
          <SortIcon type="all" icon={Music} />
          <SortIcon type="artist" icon={User} />
          <SortIcon type="genre" icon={Disc} />
          <SortIcon type="album" icon={Album} />
        </div>
      </div>
      <div className="overflow-y-auto flex-grow hide-scrollbar px-6 pb-6">
        {songs.map((song, index) => (
          <motion.div
            key={song.title + "-" + song.artist}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`flex items-center space-x-4 p-3 rounded-lg cursor-pointer mb-4 ${
              song.id === currentSongId
                ? "bg-purple-700"
                : "hover:bg-purple-800"
            }`}
            onClick={() => onSongSelect(song.title + "-" + song.artist)}
          >
            <Image
              src={song.coverUrl}
              alt={song.title}
              width={480}
              height={480}
              className="w-16 h-16 rounded-md object-cover"
            />
            <div className="flex-grow overflow-hidden">
              <p className="text-white font-semibold truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
                {song.title}
              </p>
              <p className="text-purple-300 text-sm truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
                {song.artist}
              </p>
              <p className="text-purple-400 text-xs truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
                {sortType === "genre" ? song.genre : song.album}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
      <div
        className={`p-4 border-t border-purple-700 ${
          isDragging ? "bg-purple-700" : "bg-purple-800"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          accept="audio/mpeg"
          onChange={handleFileChange}
          className="hidden"
          ref={fileInputRef}
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="flex items-center justify-center cursor-pointer text-white hover:text-purple-300 transition-colors"
        >
          <Upload size={20} className="mr-2" />
          <span>{isDragging ? "Suelta el MP3 aquí" : "Subir MP3"}</span>
        </label>
      </div>
    </div>
  );
};

const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
`;

if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = hideScrollbarStyle;
  document.head.appendChild(style);
}
