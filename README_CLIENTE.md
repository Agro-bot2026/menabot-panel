# 🤖 MenaBot Panel — Guía de uso

## ¿Qué es MenaBot Panel?

MenaBot Panel es un sistema de notificaciones automáticas por WhatsApp.
Te permite cargar tus clientes con la fecha en que vence su servicio,
y el bot les enviará un mensaje automático avisándoles que están por vencer,
sin que tengas que hacer nada manualmente.

---

## 📱 Cómo acceder al panel

Abrí el navegador y escribí la dirección que te dio tu técnico.
Ingresá con tu usuario y contraseña.

---

## 🤖 Sección: Bot WhatsApp

Esta es la primera sección que tenés que configurar antes de usar el sistema.

### ¿Qué hace?
Conecta el bot a tu cuenta de WhatsApp para que pueda enviar mensajes.

### ¿Cómo conectarlo?
1. Tocá el botón **"Reconectar / Nuevo QR"**
2. Abrí WhatsApp en tu celular
3. Tocá los tres puntos (⋮) arriba a la derecha
4. Entrá a **Dispositivos vinculados**
5. Tocá **Vincular dispositivo**
6. Escaneá el código QR que aparece en el panel
7. Listo — el punto verde indica que el bot está conectado

### ⚠️ Importante
- Usá un número de WhatsApp exclusivo para el bot, no el tuyo personal
- Si cerrás sesión en WhatsApp desde ese celular, el bot se desconecta
- Si el bot se desconecta, repetí los pasos anteriores para reconectarlo

### Mensaje de prueba
Podés ingresar un número y tocar **"Enviar test"** para verificar
que el bot está enviando mensajes correctamente antes de usarlo.

---

## 👥 Sección: Clientes

Acá cargás todos tus clientes y la fecha en que vence su servicio.

### ¿Cómo agregar un cliente?
1. Tocá **+ Nuevo cliente**
2. Completá los campos:
   - **Nombre completo** — nombre de tu cliente
   - **Número WhatsApp** — sin el + y sin espacios. Ejemplo: 5491112345678
     (549 = Argentina, 11 = código de área, 12345678 = número)
   - **Producto / Servicio** — qué compró. Ejemplo: VPS 2GB, SSH Premium, etc.
   - **Descripción** — opcional, para tus notas internas
   - **Fecha de vencimiento** — el día que vence su servicio
3. Tocá **Guardar**

### Estados de los clientes
- 🟢 **Activo** — vence en más días de los configurados como aviso
- 🟡 **Por vencer** — está dentro del período de aviso
- 🔴 **Vencido** — ya venció la fecha

### ¿Cómo editar o eliminar?
En la tabla de clientes tocá ✏️ para editar o 🗑️ para eliminar.

---

## ⚙️ Sección: Configuración

Acá personalizás cómo y cuándo el bot avisa a tus clientes.

### Días de notificación
Definís con cuántos días de anticipación el bot avisa.
Por defecto avisa 7, 3 y 1 día antes del vencimiento.

**Ejemplo:** si un cliente vence el 30 de junio:
- El 23 de junio recibe el aviso de 7 días
- El 27 de junio recibe el aviso de 3 días
- El 29 de junio recibe el aviso de 1 día
- El 30 de junio recibe el mensaje de vencido

Para agregar un día escribí el número y tocá **+ Agregar**.
Para quitar un día tocá la **×** al lado del chip.

### Hora de envío
La hora del día en que el bot revisa y envía las notificaciones.
Por defecto son las 09:00. Podés cambiarla a tu gusto.

### Mensaje de aviso de vencimiento
El texto que recibe el cliente cuando está por vencer.
Podés personalizarlo usando estas variables que se reemplazan automáticamente:

- **{nombre}** — se reemplaza por el nombre del cliente
- **{producto}** — se reemplaza por el producto que compró
- **{dias}** — se reemplaza por los días que faltan
- **{fecha}** — se reemplaza por la fecha de vencimiento

**Ejemplo de mensaje:**
⚠️ Hola {nombre}, tu {producto} vence en {dias} día(s) el {fecha}.
Para renovar respondé RENOVAR o contactate con nosotros.

### Mensaje al vencer
El texto que recibe el cliente el día que vence su servicio.
Usa las mismas variables excepto {dias}.

### Respuesta a RENOVAR
Cuando un cliente responde **RENOVAR** al mensaje del bot,
este texto es lo que el bot le contesta automáticamente.

### Archivo adjunto
Podés subir una imagen, PDF o video que se enviará junto
con cada notificación. Por ejemplo un flyer de renovación.
Para subir: arrastrá el archivo o tocá el área punteada.
Para quitar: tocá la ✕ al lado del nombre del archivo.

### Guardar
Siempre tocá **💾 Guardar configuración** después de hacer cambios.

---

## 📊 Sección: Dashboard (Inicio)

Pantalla principal con el resumen general del sistema.

- **Total clientes** — cuántos clientes tenés cargados
- **Activos** — clientes con servicio vigente
- **Por vencer** — clientes que están por vencer próximamente
- **Vencidos** — clientes con servicio vencido
- **Notif. hoy** — cuántas notificaciones envió el bot hoy

En **Atención urgente** ves las tarjetas de los clientes
que necesitan atención inmediata (por vencer o vencidos).

---

## 📋 Sección: Historial

Registro de todas las notificaciones que envió el bot.

- 🟢 Punto verde = mensaje enviado correctamente
- 🔴 Punto rojo = hubo un error al enviar

Podés ver el número, el tipo de aviso y la fecha/hora de cada envío.

---

## 👤 Sección: Perfil

Acá podés cambiar tu usuario y contraseña de acceso al panel.

### Cambiar contraseña
1. Ingresá tu contraseña actual
2. Ingresá la nueva contraseña (mínimo 6 caracteres)
3. Repetí la nueva contraseña
4. Tocá **Guardar contraseña**

### Cambiar usuario
1. Ingresá el nuevo nombre de usuario
2. Tocá **Guardar usuario**
3. El sistema te va a pedir que inicies sesión nuevamente

---

## ❓ Preguntas frecuentes

**¿El bot envía mensajes solo o tengo que hacer algo?**
Solo. Una vez configurado y conectado, el bot revisa todos los días
a la hora configurada y envía los mensajes automáticamente.

**¿Qué pasa si el VPS se reinicia?**
El sistema arranca solo automáticamente. No necesitás hacer nada,
solo volver a escanear el QR si el bot se desconecta de WhatsApp.

**¿Puedo tener varios productos por cliente?**
Por ahora cada cliente tiene un producto. Si el mismo cliente
compra otro servicio, cargalo como un cliente nuevo con otro vencimiento.

**¿El cliente sabe que es un bot?**
Los mensajes llegan como cualquier WhatsApp normal desde tu número.
No hay indicación de que es automático a menos que vos lo aclares en el mensaje.

**¿Qué pasa si un cliente no tiene WhatsApp?**
El mensaje no llega. Verificá siempre que el número tenga WhatsApp activo.

**¿Puedo cambiar los mensajes después?**
Sí, en cualquier momento desde Configuración. Los cambios aplican
a partir de la próxima notificación.

---

## 📞 Soporte técnico

Para cualquier problema técnico contactate con tu proveedor del sistema.
