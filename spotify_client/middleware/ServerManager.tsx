class ServerManager {
  private servers: string[];
  private currentServerIndex: number;

  constructor(servers: string[]) {
    this.servers = servers; // Lista de servidores disponibles
    this.currentServerIndex = 0; // Iniciar con el primer servidor
  }

  get currentServer(): string {
    return this.servers[this.currentServerIndex];
  }

  private async isServerAvailable(server: string): Promise<boolean> {
    const controller = new AbortController(); // Crea una instancia de AbortController
    const timeoutId = setTimeout(() => controller.abort(), 3000); // Establece un timeout de 3 segundos

    try {
      const response = await fetch(`${server}/api/songs`, {
        method: "HEAD",
        signal: controller.signal, // Asigna el signal del AbortController
      });
      return response.ok; // Retorna true si la respuesta es correcta
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          console.error(`Timeout: ${server} no respondió a tiempo.`);
        } else {
          console.error(`Error en el servidor ${server}: ${error.message}`);
        }
      } else {
        console.error(`Error desconocido en el servidor ${server}:`, error);
      }
      return false;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Devuelve el primer servidor disponible en tiempo real
  async getAvailableServer(
    songName: string,
    artistName: string
  ): Promise<string | null> {
    for (let i = 0; i < this.servers.length; i++) {
      const server = this.servers[i];
      if (await this.isServerAvailable(server)) {
        const servers = await fetch(
          `${server}/api/findStreamers/?song_id=${songName}-${artistName}`
        );
        console.log("servers");
        console.log(servers);
        console.log("song Name y artist name");
        console.log(songName);
        console.log(artistName);

        this.currentServerIndex = i; // Actualizamos el índice del servidor actual
        console.log(`Servidor disponible: ${server}`);
        return server;
      }
    }

    console.warn("No hay servidores disponibles.");
    return null;
  }

  async fetchStream(
    songName: string,
    artistName: string,
    rangeStart: number,
    rangeEnd: number
  ): Promise<ArrayBuffer | null> {
    const server = await this.getAvailableServer(songName, artistName);
    if (server) {
      const url = `${server}/api/stream/?song_id=${songName}-${artistName}`;
      console.log(`downloading: bytes=${rangeStart}-${rangeEnd}`);
      try {
        const response = await fetch(url, {
          headers: {
            Range: `bytes=${rangeStart}-${rangeEnd}`,
          },
        });

        if (response.ok) {
          return await response.arrayBuffer(); // Devuelve el chunk de datos
        } else {
          console.error(`Error ${response.status} al cargar desde ${url}`);
          return null;
        }
      } catch (error) {
        console.error(`Error al conectar con ${url}:`, error);
        return null;
      }
    }
    return null;
  }
}

export default new ServerManager(["http://127.0.0.1:8000"]);
