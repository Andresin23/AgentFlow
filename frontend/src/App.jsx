
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [tareas, setTareas] = useState([]);
  const [titulo, setTitulo] = useState("");
  const [prioridad, setPrioridad] = useState("media");
  const [duracion, setDuracion] = useState(60);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [estimando, setEstimando] = useState(false);
  const [mensajeEstimacion, setMensajeEstimacion] = useState("");
  async function cargarTareas() {
    try {
      setError("");
      const respuesta = await fetch(`${API}/api/tareas`);

      if (!respuesta.ok) {
        throw new Error("No se pudieron cargar las tareas");
      }

      const datos = await respuesta.json();
      setTareas(datos);
    } catch {
      setError("No se pudo conectar con AgentFlow. Verifica que FastAPI esté activo.");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargarTareas();
  }, []);

async function estimarDuracion() {
  if (!titulo.trim()) {
    setError("Escribe el título de la tarea primero.");
    return;
  }

  try {
    setError("");
    setMensajeEstimacion("");
    setEstimando(true);

    const respuesta = await fetch(
      `${API}/api/tareas/estimar-duracion`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          titulo,
          descripcion: "",
          prioridad,
        }),
      }
    );

    if (!respuesta.ok) {
      throw new Error("No se pudo estimar la duración.");
    }

    const resultado = await respuesta.json();

    setDuracion(resultado.duracion_estimada_minutos);
    setMensajeEstimacion(
      `Estimación del modelo: ${resultado.duracion_estimada_minutos} minutos`
    );
    
<button
  type="button"
  className="secundario"
  onClick={estimarDuracion}
  disabled={estimando}
>
  {estimando ? "Estimando..." : "Estimar con IA"}
</button>

{mensajeEstimacion && (
  <p className="mensaje-estimacion">{mensajeEstimacion}</p>
)}

  } catch (err) {
    setError(err.message);
  } finally {
    setEstimando(false);
  }
}


  async function crearTarea(e) {
    e.preventDefault();

    try {
      setError("");

      const respuesta = await fetch(`${API}/api/tareas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          titulo,
          prioridad,
          duracion_estimada: Number(duracion),
        }),
      });

      if (!respuesta.ok) {
        throw new Error("No se pudo crear la tarea");
      }

      setTitulo("");
      setPrioridad("media");
      setDuracion(60);

      await cargarTareas();
    } catch (err) {
      setError(err.message);
    }
  }

  async function completarTarea(id) {
    try {
      setError("");

      const respuesta = await fetch(
        `${API}/api/tareas/${id}/completar`,
        { method: "PATCH" }
      );

      if (!respuesta.ok) {
        throw new Error("No se pudo completar la tarea");
      }

      await cargarTareas();
    } catch (err) {
      setError(err.message);
    }
  }

  async function eliminarTarea(id) {
    if (!window.confirm("¿Quieres eliminar esta tarea?")) return;

    try {
      setError("");

      const respuesta = await fetch(`${API}/api/tareas/${id}`, {
        method: "DELETE",
      });

      if (!respuesta.ok) {
        throw new Error("No se pudo eliminar la tarea");
      }

      await cargarTareas();
    } catch (err) {
      setError(err.message);
    }
  }

  const pendientes = tareas.filter(
    (tarea) => tarea.estado !== "completada"
  ).length;

  return (
    <main className="app">
      <header className="encabezado">
        <div>
          <p className="marca">AGENTFLOW / PRODUCTIVIDAD INTELIGENTE</p>
          <h1>Organiza tu día.</h1>
          <p className="subtitulo">
            Tus tareas, tu tiempo y tu progreso en un solo lugar.
          </p>
        </div>

        <div className="resumen">
          <span>Tareas pendientes</span>
          <strong>{pendientes}</strong>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      <section className="panel">
        <h2>Nueva tarea</h2>

        <form onSubmit={crearTarea} className="formulario">
          <label>
            Nombre de la tarea
            <input
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              placeholder="Ej. Estudiar Machine Learning"
              maxLength={150}
              required
            />
          </label>

          <div className="campos">
            <label>
              Prioridad
              <select
                value={prioridad}
                onChange={(e) => setPrioridad(e.target.value)}
              >
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
              </select>
            </label>

            <label>
              Duración estimada (minutos)
              <input
                type="number"
                min="1"
                value={duracion}
                onChange={(e) => setDuracion(e.target.value)}
                required
              />
            </label>
          </div>

          <button type="submit">+ Crear tarea</button>
        </form>
      </section>

      <section className="panel">
        <div className="titulo-lista">
          <h2>Mis tareas</h2>
          <span>{tareas.length} en total</span>
        </div>

        {cargando ? (
          <p>Cargando tareas...</p>
        ) : tareas.length === 0 ? (
          <p>Aún no tienes tareas. ¡Crea la primera!</p>
        ) : (
          <div className="lista">
            {tareas.map((tarea) => (
              <article className="tarea" key={tarea.id}>
                <div className="tarea-info">
                  <h3>{tarea.titulo}</h3>
                  <p>
                    {tarea.duracion_estimada} min · Prioridad{" "}
                    {tarea.prioridad}
                  </p>
                  <span
                    className={`estado ${
                      tarea.estado === "completada" ? "completada" : ""
                    }`}
                  >
                    {tarea.estado}
                  </span>
                </div>

                <div className="acciones">
                  {tarea.estado !== "completada" && (
                    <button
                      className="secundario"
                      onClick={() => completarTarea(tarea.id)}
                    >
                      Completar
                    </button>
                  )}

                  <button
                    className="eliminar"
                    onClick={() => eliminarTarea(tarea.id)}
                  >
                    Eliminar
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer>AgentFlow · Construido para trabajar mejor</footer>
    </main>
  );
}

export default App;
