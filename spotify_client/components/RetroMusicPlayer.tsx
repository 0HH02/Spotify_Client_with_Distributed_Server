"use client";

import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import serverManager from "../middleware/ServerManager";
import Image from 'next/image';



const CHUNK_SIZE = 1024 * 512; // 512 KB chunk size

interface RetroMusicPlayerProps {
  songs: {
    id: string;
    title: string;
    artist: string;
    genre: string;
    album: string;
    coverUrl: string;
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
  const [songSize, setSongSize] = useState<number | null>(null);

  const chunkListRef = useRef<{ index: number }[]>([]);
  const isFetchingRef = useRef(false);

  const currentSong = songs.find((song) => song.id === currentSongId) || {} as Song;

  useEffect(() => {
    if (!loading && currentSong.id) {
      const fetchAudioStream = async () => {
        if ('MediaSource' in window) {
          const mediaSrc = new MediaSource();
          setMediaSource(mediaSrc);

          try {
            // Obtener el tamaño del archivo de la canción
            const server = await serverManager.getAvailableServer();
            const response = await axios.head(
              `${server}/api/stream/${currentSong.id}/`
            );
            const contentLength = response.headers['content-length'];
            if (contentLength) {
              const fileSize = parseInt(contentLength, 10);

              setSongSize(fileSize);

              // Calcular duración aproximada basado en tasa de bits
              const bitrate = 128000; // 128 kbps como ejemplo
              const calculatedDuration = fileSize / (bitrate / 8); // Duración en segundos

              setDuration(calculatedDuration);
            }
          } catch (error) {
            console.error('Error fetching song size:', error);
          }
          

          mediaSrc.addEventListener('sourceopen', () => {
            if (mediaSrc.readyState !== 'open') {
              console.warn('MediaSource is not open.');
              return;
            }
            const srcBuffer = mediaSrc.addSourceBuffer('audio/mpeg');
            setSourceBuffer(srcBuffer);
          
            if (audioRef.current) {
              audioRef.current.addEventListener('timeupdate', () => {
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
          console.error('MediaSource API is not supported in this browser');
        }
      };

      fetchAudioStream();
    }
  }, [currentSong.id, loading]);

  useEffect(() => {
    if (audioRef.current && isPlaying) {
      audioRef.current.play().catch((e) => console.error('Play failed:', e));
    }
  }, [currentSongId, isPlaying]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
  
    const onCanPlayThrough = () => {
      if (isPlaying) {
        audio.play().catch((e) => console.error('Play error:', e));
      }
    };
  
    audio.addEventListener('canplaythrough', onCanPlayThrough);
  
    return () => {
      audio.removeEventListener('canplaythrough', onCanPlayThrough);
    };
  }, [isPlaying, currentSongId]);

  const monitorBuffer = async (srcBuffer: SourceBuffer | null, mediaSrc: MediaSource) => {
    if (!srcBuffer) {
      console.warn('SourceBuffer is not initialized yet.');
      return; // Salir si srcBuffer aún no está disponible
    }
  
    // Verifica que el MediaSource esté abierto
    if (mediaSrc.readyState !== 'open') {
      console.warn('MediaSource is not open.');
      return;
    }
  
    try {
      const currentTime = audioRef.current?.currentTime || 0;
      const bufferEnd = srcBuffer.buffered.length > 0 ? srcBuffer.buffered.end(0) : 0;
  
      if (!isFetchingRef.current && bufferEnd - currentTime < 5) {
        const lastChunkIndex =
          chunkListRef.current.length > 0 ? chunkListRef.current[chunkListRef.current.length - 1].index : -1;
        const nextChunkIndex = lastChunkIndex + 1;
        await fetchAndAppendChunk(srcBuffer, nextChunkIndex, mediaSrc);
      }
    } catch (error) {
      // Manejo del caso donde el SourceBuffer ha sido eliminado
      console.error('Error while accessing the SourceBuffer:', error);
    }
  };

  const fetchAndAppendChunk = async (
  srcBuffer: SourceBuffer,
  chunkIndex: number,
  mediaSrc: MediaSource
) => {
  if (mediaSrc.readyState !== 'open') return;

  try {
    setIsFetching(true);
    isFetchingRef.current = true;

    const rangeStart = chunkIndex * CHUNK_SIZE;
    const rangeEnd = (chunkIndex + 1) * CHUNK_SIZE - 1;

    // Middleware para manejar el stream
    const chunk = await serverManager.fetchStream(currentSong.id, rangeStart, rangeEnd);

    if (!chunk) {
      console.warn('No se pudo cargar el chunk, intentando de nuevo...');
      return await fetchAndAppendChunk(srcBuffer, chunkIndex, mediaSrc);
    }

    // Espera a que el SourceBuffer termine de actualizarse
    await new Promise<void>((resolve) => {
      if (!srcBuffer.updating) resolve();
      else srcBuffer.addEventListener('updateend', () => resolve(), { once: true });
    });

    srcBuffer.appendBuffer(chunk);

    setChunkList((prev) => {
      const updatedChunks = [...prev, { index: chunkIndex }];
      chunkListRef.current = updatedChunks;
      return updatedChunks;
    });
  } catch (error) {
    console.error('Error al cargar el chunk:', error);
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
    const currentIndex = songs.findIndex(song => song.id === currentSongId);

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
    const currentIndex = songs.findIndex(song => song.id === currentSongId);

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


  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current && !loading) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };


  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
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
            src={currentSong.coverUrl || 'https://via.placeholder.com/300'}
            alt={`${currentSong.title || 'No song loaded'} cover`}
            className="w-full h-full object-cover"
          />
        </motion.div>
        <motion.h2
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-3xl font-bold text-white mb-2 truncate text-center"
        >
          {currentSong.title || 'Loading...'}
        </motion.h2>
        <motion.p
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="text-purple-200 mb-6 text-center"
        >
          {currentSong.artist || 'Loading...'}
        </motion.p>
        <div className="flex items-center justify-between mb-4">
          <span className="text-purple-200 text-sm">{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration}
            value={currentTime}
            onChange={handleSeek}
            className="w-full mx-2 accent-purple-500"
            disabled={loading} // Deshabilitar durante la carga
          />
          <span className="text-purple-200 text-sm">{formatTime(duration || 0)}</span>
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
              loading ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-500'
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