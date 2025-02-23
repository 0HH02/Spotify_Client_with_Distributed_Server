// cacheManager.ts
const songChunksCache: {
  [songId: string]: { [chunkIndex: number]: Uint8Array };
} = {};

export const getSongChunk = (
  songId: string,
  chunkIndex: number
): Uint8Array | undefined => {
  return songChunksCache[songId]?.[chunkIndex];
};

export const cacheSongChunk = (
  songId: string,
  chunkIndex: number,
  chunk: Uint8Array
) => {
  if (!songChunksCache[songId]) {
    songChunksCache[songId] = {};
  }
  songChunksCache[songId][chunkIndex] = chunk;
};
