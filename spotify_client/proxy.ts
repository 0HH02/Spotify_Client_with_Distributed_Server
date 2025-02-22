const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();

const cors = require("cors");

app.use(cors({ origin: "*" })); // Permitir todos los orígenes (para pruebas)
app.use(
  (
    req: import("express").Request,
    res: import("express").Response,
    next: import("express").NextFunction
  ) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header(
      "Access-Control-Allow-Methods",
      "GET, POST, PUT, DELETE, OPTIONS"
    );
    res.header(
      "Access-Control-Allow-Headers",
      "Origin, X-Requested-With, Content-Type, Accept, Authorization"
    );

    // Manejo de preflight (CORS OPTIONS request)
    if (req.method === "OPTIONS") {
      return res.sendStatus(200);
    }

    next();
  }
);

app.use(
  (
    req: import("express").Request,
    res: import("express").Response,
    next: import("express").NextFunction
  ) => {
    console.log(`[LOG] Solicitud entrante: ${req.method} ${req.url}`);

    // Convertimos la respuesta a ServerResponse de 'http' para usar el método "on"
    const nodeRes = res as import("http").ServerResponse;
    nodeRes.on("finish", () => {
      console.log(
        `[LOG] Respuesta enviada para ${req.method} ${req.url} con status ${res.statusCode}`
      );
    });
    next();
  }
);

// Proxy para redirigir solicitudes de API al backend (rutas que comienzan con /api)
app.use(
  "/172.0.13.2",
  createProxyMiddleware({
    target: "http://172.0.13.2:8000", // Dirección del backend
    changeOrigin: true,
  })
);

app.use(
  "/172.0.13.3",
  createProxyMiddleware({
    target: "http://172.0.13.3:8000", // Dirección del backend
    changeOrigin: true,
  })
);

app.use(
  "/172.0.13.4",
  createProxyMiddleware({
    target: "http://172.0.13.4:8000", // Dirección del backend
    changeOrigin: true,
  })
);
// Proxy para redirigir todo lo demás al frontend
// app.use(
//   "/",
//   createProxyMiddleware({
//     target: "http://localhost:3000", // Dirección del frontend
//     changeOrigin: true,
//   })
// );

const PORT = 4000;
app.listen(PORT, () => {
  console.log(`🔄 Proxy corriendo en http://localhost:${PORT}`);
});
