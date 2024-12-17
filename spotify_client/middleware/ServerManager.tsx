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

  // Método para comprobar si un servidor está disponible
  private async isServerAvailable(server: string): Promise<boolean> {
    try {
      const response = await fetch(`${server}/api/songs`, { method: 'HEAD', timeout: 3000 });
      return response.ok;
    } catch {
      return false;
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
    console.warn('No hay servidores disponibles.');
    return null;
  }

  async fetchStream(songId: string, rangeStart: number, rangeEnd: number): Promise<ArrayBuffer | null> {
    const server = await this.getAvailableServer();
    if (server){
      const url = `${server}/api/stream/${songId}/`;
  
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
    return null
  }
}

export default new ServerManager([
  'http://192.168.93.221:8000',
  'http://192.168.93.221:8080',
]);;
