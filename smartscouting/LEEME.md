# SmartScouting · Instalación y publicación

## Contenido del proyecto

```
smartscouting/
├── index.html      Acceso con correo y contraseña
├── panel.html      Panel del administrador (dos módulos)
├── usuarios.html   Alta y administración de cuentas
├── app.html        Calculadora (estructura y estilos)
├── app.js          Lógica de la calculadora
├── db.js           Acceso a la base de datos
├── config.js       Datos de conexión (hay que llenarlo)
├── estilos.css     Estilos de acceso, panel y usuarios
├── apps_script.gs  Código que va en Google Apps Script
├── config.js       Conexión con Google Sheets (hay que llenarlo)
└── vendor/         Bibliotecas incluidas en el proyecto
```

Siguen siendo archivos estáticos: no necesitas servidor propio.

---

## Dos modos, un solo paquete

La aplicación revisa `config.js` al arrancar y decide sola cómo trabajar:

| | **Modo local** | **Modo nube** |
|---|---|---|
| Cuándo se activa | Mientras `config.js` conserve los valores de ejemplo | En cuanto pegues la URL y el token de Google Sheets |
| Dónde viven los datos | En el navegador de cada equipo | En la base de datos compartida |
| Qué se necesita | Nada | Una hoja de Google con Apps Script |
| Se ve | Una etiqueta ámbar "Modo local" abajo a la derecha | Sin etiqueta |

No hay que cambiar ningún otro archivo: las dos formas ofrecen exactamente las mismas funciones y las pantallas no se enteran de cuál está activa.

---

## Modo local: empezar ahora mismo

Abre `index.html` y entra con la cuenta que viene creada:

| Correo | Contraseña |
|---|---|
| `juan.manuel@gmail.com` | `shopx2026` |

Desde ahí ya puedes dar de alta al equipo, capturar productos y guardar cotizaciones. Todo funciona igual que en la nube: los roles, la ventana de comisiones en solo lectura para el equipo de scouting, y la separación de cotizaciones por persona.

**Lo que sí conviene tener claro.** Los datos viven en el navegador de cada equipo, así que no se comparten entre computadoras ni entre navegadores distintos, y se pierden si alguien borra los datos de navegación. Además, en este modo los permisos se aplican del lado del navegador: alguien con conocimientos técnicos podría saltárselos desde la consola. Sirve muy bien para trabajar y para presentar el sistema, pero no para información delicada ni para varias personas a la vez.

Para no perder lo capturado, el panel del administrador tiene un botón **Respaldo** que descarga un archivo con usuarios, configuración y cotizaciones.

---

## Modo nube: cuando tengas el dominio (Google Sheets)

En este modo los datos viven en una hoja de cálculo de Google, que hace de base de datos. La ventaja es que puedes abrir la hoja y ver o corregir todo como cualquier planilla. Un intermediario llamado Apps Script se encarga de leer y escribir en ella; la aplicación nunca toca la hoja directamente.

### 1. Crear la hoja y el intermediario

1. Entra a `sheets.google.com` y crea una hoja en blanco. Ponle el nombre que quieras, por ejemplo "SmartScouting datos".
2. En el menú, abre **Extensiones → Apps Script**. Se abre un editor de código en otra pestaña.
3. Borra el contenido que traiga y pega **todo** el archivo `apps_script.gs`.
4. Cerca del inicio verás una línea con `const TOKEN = '...'`. Cámbiala por una frase larga y única, inventada por ti. Anótala: la vas a necesitar en el paso 3.
5. Guarda con el icono del disquete.

### 2. Preparar la base y publicar

1. En el editor de Apps Script, arriba hay un menú que dice "Seleccionar función". Elige **instalar** y presiona **Ejecutar**. La primera vez Google te pedirá autorizar el permiso para editar tu hoja: acéptalo. Esto crea las tres pestañas (`usuarios`, `configuracion`, `cotizaciones`) y deja creada tu cuenta de administrador.
2. Ahora publica el intermediario: **Implementar → Nueva implementación**. En el engrane elige **Aplicación web** y configura:

   | Campo | Valor |
   |---|---|
   | Ejecutar como | Yo (tu cuenta) |
   | Quién tiene acceso | Cualquier persona |

3. Presiona **Implementar**, autoriza si lo pide, y copia la **URL de la aplicación web**. Termina en `/exec`.

### 3. Conectar la aplicación

Abre `config.js` y pega las dos cosas:

```js
const SHEETS_URL   = 'https://script.google.com/macros/s/AKfyc.../exec';
const SHEETS_TOKEN = 'la-misma-frase-larga-que-pusiste-en-el-script';
```

El token tiene que ser **idéntico** al del script. En cuanto guardes este archivo con datos reales, la etiqueta "Modo local" desaparece y la aplicación empieza a trabajar contra la hoja.

### Tu cuenta de administrador

Queda creada por el paso `instalar`, con los mismos datos de siempre:

| Correo | Contraseña |
|---|---|
| `juan.manuel@gmail.com` | `shopx2026` |

Desde el módulo de usuarios das de alta al resto. Todo, incluidos correos y contraseñas, se puede corregir después con el icono de editar.

### Sobre la seguridad de este modo

Es importante que lo tengas claro para la tesina. Este esquema es más sencillo que una base de datos profesional, y esa sencillez tiene un costo:

- Las contraseñas se guardan como huella cifrada (SHA-256), nunca en texto legible dentro de la hoja. Eso está bien.
- El token evita que alguien que encuentre la URL por casualidad escriba en tu hoja, pero viaja dentro del navegador, así que alguien con conocimientos técnicos podría leerlo. No es una barrera infranqueable.
- La separación "cada quien ve lo suyo" la decide el intermediario, no la hoja. Funciona para el uso normal del equipo, pero no tiene la solidez de las reglas a nivel de base de datos.

En resumen: es una solución muy práctica para un proyecto de equipo pequeño y para presentar el sistema, pero no la recomendaría para datos verdaderamente sensibles. Si algún día necesitas esa solidez, la aplicación está escrita de forma que solo habría que reescribir el modo nube de `db.js`, sin tocar las pantallas.

---

## Cómo ver o corregir datos a mano

Como la base es una hoja de cálculo, puedes abrirla cuando quieras:

- La pestaña **usuarios** lista las cuentas. Puedes cambiar un rol o desactivar a alguien editando la celda, aunque es más cómodo hacerlo desde el módulo. La columna `clave` es la huella de la contraseña: no la edites a mano.
- La pestaña **configuracion** guarda las comisiones y variables en una sola celda.
- La pestaña **cotizaciones** tiene el historial completo. Sirve para sacar reportes o gráficas con las herramientas de Google Sheets.

Para un respaldo, el panel del administrador tiene un botón **Respaldo** que descarga todo en un archivo, y además Google guarda el historial de versiones de la hoja automáticamente.

---

## Publicar en un dominio

Los archivos son estáticos, así que sirve cualquiera de estas opciones:

**Netlify** — comprime la carpeta en un `.zip`, entra a `app.netlify.com/drop` y arrástralo. En *Site settings → Domain management* conectas tu dominio.

**Vercel** — sube la carpeta a GitHub, importa el repositorio y en "Framework Preset" elige **Other**, dejando vacíos los campos de compilación.

**GitHub Pages** — sube los archivos a la rama `main` y actívalo en *Settings → Pages*.

**Hosting con cPanel** — sube el `.zip` a `public_html` y usa "Extract". Verifica que `index.html` quede directamente ahí, no dentro de una subcarpeta. Activa el certificado SSL en *SSL/TLS Status*.

En todos los casos el sitio debe abrir con `https`, porque tanto Google Apps Script como el servicio de tipo de cambio lo exigen.

---

## Notas de operación

**Contraseñas.** Cuando das de alta a alguien, la contraseña se muestra en pantalla una sola vez para que puedas copiarla y entregarla. Después ya no se puede consultar: la hoja guarda solo una huella cifrada. Si alguien la pierde, entra al módulo de usuarios, abre su ficha con el icono de editar y asígnale una nueva.

**Bajas.** No borres cuentas: usa el botón "Desactivar". La persona deja de poder entrar, pero sus cotizaciones se conservan para el historial y los reportes.

**Comisiones.** Las cambia solo el administrador desde el botón Config, y el cambio aplica de inmediato para todo el equipo, porque viven en una sola fila compartida de la base de datos.

**Respaldos.** Google guarda el historial de versiones de la hoja automáticamente. Para un respaldo aparte, usa el botón **Respaldo** del panel del administrador, que descarga usuarios, configuración y cotizaciones en un archivo.

**Límites.** Google Apps Script permite una buena cantidad de peticiones al día en una cuenta normal, de sobra para un equipo pequeño. Si en algún momento la app se siente lenta, suele ser porque Apps Script tarda un poco en responder la primera petición tras un rato de inactividad; a partir de la segunda va fluido.

---

## Volver a compilar tras un cambio

`app.js` es código ya compilado, pero está en JavaScript legible, sin minificar. Si necesitas modificar algo, edítalo directamente y súbelo otra vez. No hay paso de compilación.
