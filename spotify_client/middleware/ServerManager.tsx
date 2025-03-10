import axios from "axios";
import { sign } from "crypto";
class ServerManager {
  private servers: string[];
  private streamersServers: string[];
  private currentServerIndex: number;
  private currentStreamServer: string;


  constructor(servers: string[]) {
    this.servers = servers; // Lista de servidores disponibles
    this.streamersServers = [];
    this.currentServerIndex = 0; // Iniciar con el primer servidor
    this.currentStreamServer = "";
  }

  get currentServer(): string {
    return this.servers[this.currentServerIndex];
  }

  private async isServerAvailable(server: string): Promise<boolean> {
    const controller = new AbortController(); // Crea una instancia de AbortController
    const timeoutId = setTimeout(() => controller.abort(), 3000); // Establece un timeout de 1 segundos

    try {
      console.log(`Verificando disponibilidad de ${server}...`);
      const response = await axios.get(`${server}/api/alive/`, { signal: controller.signal });
      console.log(`Servidor ${server} disponible.`);
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
    if (await this.isServerAvailable(this.servers[this.currentServerIndex])) {
      return this.servers[this.currentServerIndex];
    }
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
    const url = `${this.currentStreamServer}/api/stream/?song_id=${songName}-${artistName}`;
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
    if (this.streamersServers.length == 0 && !(await this.findStreamersServers(songName, artistName))) {
      console.log("No se encontraron servidores con la canción");
      return null;
    }
    for (const server of this.streamersServers) {
      if (server !== this.currentStreamServer) {
        const url = `${server}/api/stream/?song_id=${songName}-${artistName}`;
        console.log(`downloading: bytes=${rangeStart}-${rangeEnd}`);
        try {
          const response = await fetch(url, {
            headers: {
              Range: `bytes=${rangeStart}-${rangeEnd}`,
            },
          });

          if (response.ok) {
            this.currentStreamServer = server;
            return await response.arrayBuffer(); // Devuelve el chunk de datos
          } else {
            console.error(`Error ${response.status} al cargar desde ${url}`);
          }
        } catch (error) {
          console.error(`Error al conectar con ${url}:`, error);
        }
      }
    }
    return null;
  }
}

export default new ServerManager([
  "http://localhost:4000/172.0.13.2",
  "http://localhost:4000/172.0.13.3",
  "http://localhost:4000/172.0.13.4",
  "http://localhost:4000/172.0.13.5",
]);
