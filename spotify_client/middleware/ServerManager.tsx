import axios from "axios";
class ServerManager {
  private servers: string[];
  private streamersServers: string[];
  private currentServerIndex: number;

  constructor(servers: string[]) {
    this.servers = servers; // Lista de servidores disponibles
    this.streamersServers = [];
    this.currentServerIndex = 0; // Iniciar con el primer servidor
  }

  get currentServer(): string {
    return this.servers[this.currentServerIndex];
  }

  private async isServerAvailable(server: string): Promise<boolean> {
    const controller = new AbortController(); // Crea una instancia de AbortController
    const timeoutId = setTimeout(() => controller.abort(), 1000); // Establece un timeout de 1 segundos

    try {
      const response = await axios.get(`${server}/api/songs/`);
      return response.data != null; // Retorna true si la respuesta es correcta
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
  async getAvailableServer(): Promise<string | null> {
    for (let i = 0; i < this.servers.length; i++) {
      const server = this.servers[i];
      if (await this.isServerAvailable(server)) {
        this.currentServerIndex = i; // Actualizamos el índice del servidor actual
        console.log(`Servidor disponible: ${server}`);
        return server;
      }
    }

    console.warn("No hay servidores disponibles.");
    return null;
  }

  async findStreamersServers(
    songName: string,
    artistName: string
  ): Promise<boolean> {
    const server = await this.getAvailableServer();
    console.log(server);
    const servers = (
      await axios.get(
        `${server}/api/findStreamers/?song_id=${songName}-${artistName}`
      )
    ).data.data.streamers;
    console.log(servers);
    for (let index = 0; index < servers.length; index++) {
      this.streamersServers.push(
        `http://localhost:4000/${servers[index]["ip"]}`
      );
      console.log(servers[index]["ip"] + " agregado");
    }
    return servers.length > 0;
  }

  async fetchStream(
    songName: string,
    artistName: string,
    rangeStart: number,
    rangeEnd: number
  ): Promise<ArrayBuffer | null> {
    if (!(await this.findStreamersServers(songName, artistName))) {
      console.log("No se encontraron servidores con la canción");
      return null;
    }
    for (const server of this.streamersServers) {
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
        }
      } catch (error) {
        console.error(`Error al conectar con ${url}:`, error);
      }
    }
    return null;
  }
}

export default new ServerManager([
  "http://loaclhost:4000/172.0.13.2",
  "http://loaclhost:4000/172.0.13.3",
  "http://loaclhost:4000/172.0.13.4",
  "http://loaclhost:4000/172.0.13.5",
]);
