// import React, { useState, useRef, useEffect } from "react";
// import { motion } from "framer-motion";
// import {
//   Search,
//   Music,
//   User,
//   Disc,
//   Album,
//   Upload,
//   ArrowLeft,
//   Mic, // Importamos el icono del micrófono
//   MicOff, // Importamos el icono de micrófono apagado
// } from "lucide-react";
// import serverManager from "@/middleware/ServerManager";
// import Image from "next/image";
// import axios from "axios";

// interface Song {
//   id: string;
//   title: string;
//   artist: string;
//   genre: string;
//   album: string;
//   coverUrl: string;
// }

// interface SongListProps {
//   songs: Song[];
//   currentSongId: string;
//   onSongSelect: (songId: string) => void;
//   onSongUpload: (file: File) => void;
//   sortType: string;
//   searchTerm: string;
//   onSortTypeChange: (type: "all" | "artist" | "genre" | "album") => void;
//   onSearchTermChange: (term: string) => void;
//   onHide: () => void;
// }

// type SortType = "all" | "artist" | "genre" | "album";

// // Servicio para manejar la búsqueda por voz
// const voiceSearchService = {
//   // Función para procesar el audio con Whisper
//   async processAudioWithWhisper(audioBlob: Blob): Promise<string> {
//     try {
//       const server = await serverManager.getAvailableServer();
//       const formData = new FormData();
//       formData.append("audio", audioBlob, "recording.webm");

//       const response = await axios.post(`${server}/api/whisper/`, formData, {
//         headers: {
//           "Content-Type": "multipart/form-data",
//         },
//       });

//       return response.data.text;
//     } catch (error) {
//       console.error("Error al procesar audio con Whisper:", error);
//       throw new Error("No se pudo procesar el audio");
//     }
//   },

//   // Función para analizar el texto con Gemini
//   async analyzeTextWithGemini(
//     text: string
//   ): Promise<{ filter: SortType; query: string }> {
//     try {
//       const server = await serverManager.getAvailableServer();
//       const response = await axios.post(`${server}/api/gemini/`, {
//         prompt: `Analiza el siguiente comando de voz para buscar música: "${text}". 
//                 Devuelve un JSON con el formato {"filter": "tipo de filtro", "query": "término de búsqueda"}.
//                 El filtro debe ser uno de los siguientes: "all", "artist", "genre", "album".
//                 Si no se menciona un filtro específico, usa "all".`,
//       });

//       return response.data;
//     } catch (error) {
//       console.error("Error al analizar texto con Gemini:", error);
//       // Si falla, devolvemos valores predeterminados
//       return { filter: "all" as SortType, query: text };
//     }
//   },
// };

// export const SongList: React.FC<SongListProps> = ({
//   songs,
//   currentSongId,
//   onSongSelect,
//   onSongUpload,
//   sortType,
//   searchTerm,
//   onSortTypeChange,
//   onSearchTermChange,
//   onHide,
// }) => {
//   const [isDragging, setIsDragging] = useState(false);
//   const [isRecording, setIsRecording] = useState(false);
//   const [isProcessing, setIsProcessing] = useState(false);
//   const fileInputRef = useRef<HTMLInputElement>(null);
//   const mediaRecorderRef = useRef<MediaRecorder | null>(null);
//   const audioChunksRef = useRef<Blob[]>([]);

//   // Función para iniciar la grabación
//   const startRecording = async () => {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//       const mediaRecorder = new MediaRecorder(stream);
//       mediaRecorderRef.current = mediaRecorder;
//       audioChunksRef.current = [];

//       mediaRecorder.ondataavailable = (event) => {
//         if (event.data.size > 0) {
//           audioChunksRef.current.push(event.data);
//         }
//       };

//       mediaRecorder.onstop = async () => {
//         setIsProcessing(true);
//         try {
//           const audioBlob = new Blob(audioChunksRef.current, {
//             type: "audio/webm",
//           });

//           // Procesar con Whisper
//           const transcribedText =
//             await voiceSearchService.processAudioWithWhisper(audioBlob);
//           console.log("Texto transcrito:", transcribedText);

//           // Analizar con Gemini
//           const { filter, query } =
//             await voiceSearchService.analyzeTextWithGemini(transcribedText);
//           console.log("Análisis Gemini:", { filter, query });

//           // Actualizar los filtros y realizar la búsqueda
//           if (filter !== sortType) {
//             onSortTypeChange(filter);
//           }
//           onSearchTermChange(query);
//         } catch (error) {
//           console.error("Error al procesar la grabación:", error);
//           alert("No se pudo procesar la grabación de voz");
//         } finally {
//           setIsProcessing(false);

//           // Detener todas las pistas del stream
//           stream.getTracks().forEach((track) => track.stop());
//         }
//       };

//       mediaRecorder.start();
//       setIsRecording(true);
//     } catch (error) {
//       console.error("Error al iniciar la grabación:", error);
//       alert("No se pudo acceder al micrófono");
//     }
//   };

//   // Función para detener la grabación
//   const stopRecording = () => {
//     if (mediaRecorderRef.current && isRecording) {
//       mediaRecorderRef.current.stop();
//       setIsRecording(false);
//     }
//   };

//   // Limpiar recursos cuando el componente se desmonte
//   useEffect(() => {
//     return () => {
//       if (mediaRecorderRef.current && isRecording) {
//         mediaRecorderRef.current.stop();
//       }
//     };
//   }, [isRecording]);

//   const handleFileChange = async (
//     event: React.ChangeEvent<HTMLInputElement>
//   ) => {
//     const file = event.target.files?.[0];
//     if (file && file.type === "audio/mpeg") {
//       try {
//         const formData = new FormData();
//         formData.append("file", file); // 'file' es el nombre esperado por el servidor
//         const server = await serverManager.getAvailableServer();

//         const response = await axios.post(`${server}/api/upload/`, formData, {
//           headers: {
//             "Content-Type": "multipart/form-data",
//           },
//         });

//         alert("Archivo subido correctamente.");
//         onSongUpload(file); // Actualiza el estado local
//       } catch (error) {
//         console.error("Error al subir el archivo:", error);
//         alert(
//           `Error en la subida: ${(error as any).response?.data?.message || "Error desconocido"
//           }`
//         );
//       }
//     } else {
//       alert("Por favor, selecciona un archivo MP3 válido.");
//     }
//   };

//   const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
//     event.preventDefault();
//     setIsDragging(true);
//   };

//   const handleDragLeave = () => {
//     setIsDragging(false);
//   };

//   const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
//     event.preventDefault();
//     setIsDragging(false);
//     const file = event.dataTransfer.files[0];
//     if (file && file.type === "audio/mpeg") {
//       onSongUpload(file);
//     } else {
//       alert("Por favor, suelta un archivo MP3 válido.");
//     }
//   };

//   const SortIcon = ({
//     type,
//     icon: Icon,
//   }: {
//     type: SortType;
//     icon: React.ElementType;
//   }) => (
//     <motion.div
//       whileHover={{ scale: 1.1 }}
//       whileTap={{ scale: 0.9 }}
//       onClick={() => onSortTypeChange(type)}
//       className={`cursor-pointer p-2 rounded-full ${sortType === type ? "bg-purple-600" : "bg-purple-800"
//         }`}
//     >
//       <Icon size={20} className="text-white" />
//     </motion.div>
//   );

//   for (const s in songs) {
//     console.log("song: " + s)
//   }

//   return (
//     <div className="bg-gradient-to-b from-purple-900 to-indigo-800 h-full overflow-hidden flex flex-col relative">
//       <div className="p-6 pb-0 flex items-center justify-between">
//         <h2 className="text-2xl font-bold text-white">Playlist</h2>
//         <button
//           className="p-2 bg-purple-700 rounded-full text-white"
//           onClick={onHide}
//           aria-label="Hide Playlist"
//         >
//           <ArrowLeft size={20} />
//         </button>
//       </div>
//       <div className="p-6">
//         <div className="relative mb-4 flex items-center">
//           <input
//             type="text"
//             placeholder="Buscar..."
//             value={searchTerm}
//             onChange={(e) => onSearchTermChange(e.target.value)}
//             className="w-full bg-purple-800 text-white placeholder-purple-300 border border-purple-600 rounded-md py-2 pl-10 pr-12 focus:outline-none focus:ring-2 focus:ring-purple-500"
//           />
//           <Search
//             className="absolute left-3 top-1/2 transform -translate-y-1/2 text-purple-300"
//             size={20}
//           />

//           {/* Botón de búsqueda por voz */}
//           <button
//             className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full focus:outline-none ${isRecording
//               ? "bg-red-500 animate-pulse"
//               : isProcessing
//                 ? "bg-yellow-500"
//                 : "bg-purple-600 hover:bg-purple-500"
//               }`}
//             onClick={isRecording ? stopRecording : startRecording}
//             disabled={isProcessing}
//             aria-label={isRecording ? "Detener grabación" : "Buscar por voz"}
//           >
//             {isRecording ? (
//               <MicOff size={18} className="text-white" />
//             ) : (
//               <Mic size={18} className="text-white" />
//             )}
//           </button>
//         </div>
//         <div className="flex justify-between mb-4">
//           <SortIcon type="all" icon={Music} />
//           <SortIcon type="artist" icon={User} />
//           <SortIcon type="genre" icon={Disc} />
//           <SortIcon type="album" icon={Album} />
//         </div>
//       </div>
//       <div className="overflow-y-auto flex-grow hide-scrollbar px-6 pb-6">
//         {songs.map((song, index) => (
//           <motion.div
//             key={song.title + "-" + song.artist}
//             initial={{ opacity: 0, y: 20 }}
//             animate={{ opacity: 1, y: 0 }}
//             transition={{ delay: index * 0.1 }}
//             className={`flex items-center space-x-4 p-3 rounded-lg cursor-pointer mb-4 ${song.id === currentSongId
//               ? "bg-purple-700"
//               : "hover:bg-purple-800"
//               }`}
//             onClick={() => onSongSelect(song.title + "-" + song.artist)}
//           >
//             <Image
//               src={song.coverUrl || "/default_image.jpg"}
//               alt={song.title}
//               width={480}
//               height={480}
//               className="w-16 h-16 rounded-md object-cover"
//             />
//             <div className="flex-grow overflow-hidden">
//               <p className="text-white font-semibold truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
//                 {song.title}
//               </p>
//               <p className="text-purple-300 text-sm truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
//                 {song.artist}
//               </p>
//               <p className="text-purple-400 text-xs truncate w-full whitespace-nowrap overflow-hidden text-ellipsis">
//                 {sortType === "genre" ? song.genre : song.album}
//               </p>
//             </div>
//           </motion.div>
//         ))}
//       </div>
//       <div
//         className={`p-4 border-t border-purple-700 ${isDragging ? "bg-purple-700" : "bg-purple-800"
//           }`}
//         onDragOver={handleDragOver}
//         onDragLeave={handleDragLeave}
//         onDrop={handleDrop}
//       >
//         <input
//           type="file"
//           accept="audio/mpeg"
//           onChange={handleFileChange}
//           className="hidden"
//           ref={fileInputRef}
//           id="file-upload"
//         />
//         <label
//           htmlFor="file-upload"
//           className="flex items-center justify-center cursor-pointer text-white hover:text-purple-300 transition-colors"
//         >
//           <Upload size={20} className="mr-2" />
//           <span>{isDragging ? "Suelta el MP3 aquí" : "Subir MP3"}</span>
//         </label>
//       </div>
//     </div>
//   );
// };

// const hideScrollbarStyle = `
//   .hide-scrollbar::-webkit-scrollbar {
//     display: none;
//   }
//   .hide-scrollbar {
//     -ms-overflow-style: none;
//     scrollbar-width: none;
//   }
// `;

// if (typeof document !== "undefined") {
//   const style = document.createElement("style");
//   style.textContent = hideScrollbarStyle;
//   document.head.appendChild(style);
// }


import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Music,
  User,
  Disc,
  Album,
  Upload,
  ArrowLeft,
  Mic,
  MicOff,
} from "lucide-react";
import serverManager from "@/middleware/ServerManager";
import Image from "next/image";
import axios from "axios";

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
  onHide: () => void;
}

type SortType = "all" | "artist" | "genre" | "album";

// Componente auxiliar para obtener la imagen mediante una petición GET
const FetchedImage: React.FC<{
  srcUrl: string;
  alt: string;
  width: number;
  height: number;
  className?: string;
}> = ({ srcUrl, alt, width, height, className }) => {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let objectUrl: string | null = null;

    const fetchImage = async () => {
      try {
        const response = await axios.get(srcUrl, { responseType: "blob" });
        const blob = response.data;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      } catch (error) {
        console.error("Error fetching image:", error);
        setSrc("/default_image.jpg");
      }
    };

    if (srcUrl) {
      fetchImage();
    }

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [srcUrl]);

  return (
    <Image
      src={src || "/default_image.jpg"}
      alt={alt}
      width={width}
      height={height}
      className={className}
    />
  );
};

// Servicio para manejar la búsqueda por voz
const voiceSearchService = {
  // Función para procesar el audio con Whisper
  async processAudioWithWhisper(audioBlob: Blob): Promise<string> {
    try {
      const server = await serverManager.getAvailableServer();
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const response = await axios.post(`${server}/api/whisper/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return response.data.text;
    } catch (error) {
      console.error("Error al procesar audio con Whisper:", error);
      throw new Error("No se pudo procesar el audio");
    }
  },

  // Función para analizar el texto con Gemini
  async analyzeTextWithGemini(
    text: string
  ): Promise<{ filter: SortType; query: string }> {
    try {
      const server = await serverManager.getAvailableServer();
      const response = await axios.post(`${server}/api/gemini/`, {
        prompt: `Analiza el siguiente comando de voz para buscar música: "${text}". 
                Devuelve un JSON con el formato {"filter": "tipo de filtro", "query": "término de búsqueda"}.
                El filtro debe ser uno de los siguientes: "all", "artist", "genre", "album".
                Si no se menciona un filtro específico, usa "all".`,
      });

      return response.data;
    } catch (error) {
      console.error("Error al analizar texto con Gemini:", error);
      // Si falla, devolvemos valores predeterminados
      return { filter: "all" as SortType, query: text };
    }
  },
};

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
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Función para iniciar la grabación
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        try {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: "audio/webm",
          });

          // Procesar con Whisper
          const transcribedText =
            await voiceSearchService.processAudioWithWhisper(audioBlob);
          console.log("Texto transcrito:", transcribedText);

          // Analizar con Gemini
          const { filter, query } =
            await voiceSearchService.analyzeTextWithGemini(transcribedText);
          console.log("Análisis Gemini:", { filter, query });

          // Actualizar los filtros y realizar la búsqueda
          if (filter !== sortType) {
            onSortTypeChange(filter);
          }
          onSearchTermChange(query);
        } catch (error) {
          console.error("Error al procesar la grabación:", error);
          alert("No se pudo procesar la grabación de voz");
        } finally {
          setIsProcessing(false);

          // Detener todas las pistas del stream
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error al iniciar la grabación:", error);
      alert("No se pudo acceder al micrófono");
    }
  };

  // Función para detener la grabación
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Limpiar recursos cuando el componente se desmonte
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [isRecording]);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (file && file.type === "audio/mpeg") {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const server = await serverManager.getAvailableServer();

        const response = await axios.post(`${server}/api/upload/`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        alert("Archivo subido correctamente.");
        onSongUpload(file);
      } catch (error) {
        console.error("Error al subir el archivo:", error);
        alert(
          `Error en la subida: ${(error as any).response?.data?.message || "Error desconocido"
          }`
        );
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
      className={`cursor-pointer p-2 rounded-full ${sortType === type ? "bg-purple-600" : "bg-purple-800"
        }`}
    >
      <Icon size={20} className="text-white" />
    </motion.div>
  );

  return (
    <div className="bg-gradient-to-b from-purple-900 to-indigo-800 h-full overflow-hidden flex flex-col relative">
      <div className="p-6 pb-0 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Playlist</h2>
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

          {/* Botón de búsqueda por voz */}
          <button
            className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full focus:outline-none ${isRecording
              ? "bg-red-500 animate-pulse"
              : isProcessing
                ? "bg-yellow-500"
                : "bg-purple-600 hover:bg-purple-500"
              }`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            aria-label={isRecording ? "Detener grabación" : "Buscar por voz"}
          >
            {isRecording ? (
              <MicOff size={18} className="text-white" />
            ) : (
              <Mic size={18} className="text-white" />
            )}
          </button>
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
            className={`flex items-center space-x-4 p-3 rounded-lg cursor-pointer mb-4 ${song.id === currentSongId ? "bg-purple-700" : "hover:bg-purple-800"
              }`}
            onClick={() => onSongSelect(song.title + "-" + song.artist)}
          >
            <FetchedImage
              srcUrl={song.coverUrl || "/default_image.jpg"}
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
        className={`p-4 border-t border-purple-700 ${isDragging ? "bg-purple-700" : "bg-purple-800"
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
