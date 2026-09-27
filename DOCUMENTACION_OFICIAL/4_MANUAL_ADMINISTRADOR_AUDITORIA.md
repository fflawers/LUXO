# 📕 MANUAL DE ADMINISTRADOR, AUDITORÍA Y CONTROL DE SISTEMA
## LUXO AI SYSTEM v7.7 - Guía Técnica y de Gestión Corporativa

---

## 📑 ÍNDICE AUTOMATIZADO
1. [Perfil de Administrador y Jerarquía Corporativa](#1-perfil-de-administrador-y-jerarquía-corporativa)
2. [Gestión de Zonas Nacionales, Regiones y Tiendas](#2-gestión-de-zonas-nacionales-regiones-y-tiendas)
3. [Módulo de Auditoría DiSA para Contabilidad y Auditoría Interna](#3-módulo-de-auditoría-disa)
   - [3.1 Monitoreo del Calendario Semáforo a Nivel Nacional](#31-monitoreo-del-calendario-semáforo)
   - [3.2 Revisión de Cortes Panorámicos y Comprobantes](#32-revisión-de-cortes-panorámicos)
   - [3.3 Levantamiento de Observaciones y Faltantes](#33-levantamiento-de-observaciones-y-faltantes)
   - [3.4 Auditoría de Aclaraciones y Validación Final](#34-auditoría-de-aclaraciones-y-validación-final)
4. [Dashboard Ejecutivo y Métricas BI](#4-dashboard-ejecutivo-y-métricas-bi)
5. [Gestión de Manuales y Mantenimiento del Motor RAG](#5-gestión-de-manuales-y-mantenimiento-del-motor-rag)
6. [Administración de Checklists, Tareas y Campañas POP](#6-administración-de-checklists-tareas-y-campañas-pop)
7. [Administración de Trivias y Gamificación](#7-administración-de-trivias-y-gamificación)
8. [Configuración de APIs (Groq, Edge-TTS, SAPI, FedEx)](#8-configuración-de-apis)
9. [Operación del Servidor, Despliegue y Red (Cloudflare / FastAPI)](#9-operación-del-servidor-despliegue-y-red)
10. [Políticas de Respaldo de Datos y Bitácora de Auditoría](#10-políticas-de-respaldo-de-datos-y-bitácora)

---

## 1. PERFIL DE ADMINISTRADOR Y JERARQUÍA CORPORATIVA
El rol **Admin** (`rol_id = 1`) cuenta con privilegios globales para:
* Visualizar y auditar cualquier tienda del país.
* Filtrar tableros por Zona Nacional y Región Operativa.
* Modificar catálogos, cargar manuales RAG y gestionar configuraciones maestras.
* Acceder a la Bitácora inmutable de auditoría del sistema.

---

## 2. GESTIÓN DE ZONAS NACIONALES, REGIONES Y TIENDAS

La estructura corporativa está configurada en base de datos con 4 Zonas Maestras:
1. **ZONA CENTRO (Zona 1):** Regiones AICM, DF Centro, DF Norte, Valle.
2. **ZONA NORTE (Zona 2):** Regiones MTY, Noreste, Norte, Pacífico.
3. **ZONA OCCIDENTE (Zona 3):** Regiones Bajío, GDL, Occidente.
4. **ZONA SUR (Zona 4):** Regiones ACUN, CUN, Playa, Golfo, Península.

### Selector Global de Zona y Región:
En la barra superior de la aplicación, el Administrador puede alternar entre zonas y regiones mediante los menús desplegables `📍 Zona Activa` y `🗺️ Región Activa`. Los cambios se reflejan al instante en todos los tableros.

---

## 3. MÓDULO DE AUDITORÍA DiSA PARA CONTABILIDAD Y AUDITORÍA

### 3.1 Monitoreo del Calendario Semáforo
El área de Contabilidad puede auditar el cumplimiento diario de cualquier sucursal abriendo `Menú > DiSA > Ver Calendario de Cortes`:
* 🔴 **Rojo:** Exige llamada inmediata a la sucursal para requerir el corte vencido.
* 🟡 **Amarillo:** Sucursales con discrepancias o pendientes de aclarar.
* 🟢 **Verde:** Tiendas al corriente y comprobadas.

### 3.2 Revisión de Cortes Panorámicos y Comprobantes
1. Selecciona la sucursal y la fecha en el panel superior.
2. Revisa el **Corte Z (Casilla 1)** y corrobora el desglose de importes.
3. Verifica que la suma de tickets y vouchers de terminal coincidan con el importe total.
4. Comprueba que los tickets contengan la firma del cliente y sello de tienda.

### 3.3 Levantamiento de Observaciones y Faltantes
Si se detecta una discrepancia (ej. venta en efectivo sin ficha de depósito Panamericano):
* El sistema o el auditor registra la incidencia en el archivo central de estatus `disa_status.json`.
* El día cambia a color 🟡 **Amarillo** automáticamente.

### 3.4 Auditoría de Aclaraciones y Validación Final
* En la pestaña **`💬 OBSERVACIONES Y AUDITORÍA`**, el auditor revisa la respuesta enviada por la tienda.
* Si la justificación es válida (ej. comprobante anexo o nota de crédito justificada), el auditor valida el corte para cambiarlo a 🟢 **Verde**.

---

## 4. DASHBOARD EJECUTIVO Y MÉTRICAS BI
En `Menú > Dashboard`:
* **Estadísticas de Apertura en Vivo:** Gráfico de porcentaje de sucursales abiertas en tiempo y forma.
* **Cumplimiento de Checklists:** Tasa de finalización de rutinas matutinas y nocturnas.
* **Ventas vs Presupuesto:** Indicadores consolidados por región y comparación interanual.

---

## 5. GESTIÓN DE MANUALES Y MANTENIMIENTO DEL MOTOR RAG

En `Menú > Manuales`:
1. **Carga de Nuevos Documentos:** Sube archivos PDF corporativos actualizados.
2. **Buenas Prácticas para Evitar Mezclas de Información (Chunking):**
   * Asegúrate de que los PDFs contengan títulos y subtítulos claros para cada política.
   * Separa documentos históricos/inducción de documentos de procedimientos operativos de caja.
3. **Reindexación:** Al subir un manual, el sistema regenera los vectores de búsqueda para el Asistente Virtual.

---

## 6. ADMINISTRACIÓN DE CHECKLISTS, TAREAS Y CAMPAÑAS POP

* **Checklists (`build_admin_checklist_tab`):** Modifica o añade reactivos para apertura, cierre y venta.
* **Módulo de Tareas (`build_modulo_tareas_admin_tab`):** Asigna tareas con fecha límite a sucursales específicas o a nivel regional.
* **Campañas POP (`build_campanas_admin_view`):**
  * Define lineamientos visuales y planogramas oficiales.
  * Revisa las fotografías subidas por las sucursales y aprueba/rechaza el montaje.

---

## 7. ADMINISTRACIÓN DE TRIVIAS Y GAMIFICACIÓN
En `Menú > Admin Trivia`:
* Crea preguntas de opción múltiple para el Reto del Día.
* Establece la respuesta correcta, explicación técnica y fecha de publicación.
* Monitorea el ranking nacional de colaboradores con mayor puntaje.

---

## 8. CONFIGURACIÓN DE APIS Y LLAVES DE SERVICIO

Las configuraciones centrales residen en `main.py` y variables de entorno:
* **Groq API:** Lista de claves en `GROQ_API_KEYS` con balanceo y rotación automática.
* **FedEx API:** Credenciales en `fedex_service.py` (Client ID, Secret, Account Number).
* **Edge-TTS / SAPI:** Parámetros de velocidad, tono y voz predeterminada (`jarvis` / `es-MX`).

---

## 9. OPERACIÓN DEL SERVIDOR, DESPLIEGUE Y RED

### Comandos de Ejecución:
* **Servidor Web Principal (FastAPI + Flet):**
  ```powershell
  python run_web.py
  ```
* **Acceso Local:** `http://localhost:8550`
* **Túnel Seguro de Producción (Cloudflare):**
  ```powershell
  .\cloudflared.exe tunnel --url http://localhost:8550
  ```

---

## 10. POLÍTICAS DE RESPALDO DE DATOS Y BITÁCORA

### Archivos Críticos a Respaldar:
* `uploads/disa_cortes/`: Carpeta con todas las imágenes de cortes de tienda.
* `uploads/disa_cortes/disa_status.json`: Registro maestro de semáforos, aclaraciones y auditorías.
* `enfoque_diario_state_*.json`: Hojas de trabajo de planeación de tiendas.
* Base de Datos MySQL: Ejecutar respaldos periódicos con `mysqldump`.

### Bitácora de Auditoría:
Accesible desde `Menú > Bitácora`, registra con marca de tiempo inmutable cada inicio de sesión, cambio de estatus de corte, aclaraciones guardadas y movimientos administrativos.

---
