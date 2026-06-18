const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const cron = require('node-cron');
const axios = require('axios');
const express = require('express');
const fs = require('fs');
const path = require('path');

const API_URL = 'http://localhost:8000';
const API_KEY = 'menabot-internal-key-2024';
const BOT_PORT = 3001;
const AUTH_DIR = './auth_info';

const app = express();
app.use(express.json());

// ─── ESTADO GLOBAL ───────────────────────────────────────────────────────────

let sock = null;
let botConectado = false;
let qrActual = null;
let numeroConectado = null;
let cronJob = null;

// ─── FUNCIÓN PRINCIPAL DEL BOT ───────────────────────────────────────────────

async function conectarBot() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        auth: state,
        printQRInTerminal: true,
        getMessage: async () => ({ conversation: '' })
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
        if (qr) {
            qrActual = qr;
            botConectado = false;
            console.log('📱 Escanea el QR desde el panel web');
        }

        if (connection === 'close') {
            botConectado = false;
            qrActual = null;
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('❌ Bot desconectado. Reconectando:', shouldReconnect);
            if (shouldReconnect) {
                setTimeout(conectarBot, 5000);
            }
        }

        if (connection === 'open') {
            botConectado = true;
            qrActual = null;
            numeroConectado = sock.user?.id?.split(':')[0] || null;
            console.log(`✅ Bot conectado: ${numeroConectado}`);
            iniciarCron();
        }
    });

    // ─── MANEJO DE MENSAJES ENTRANTES ─────────────────────────────────────────

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;
        for (const msg of messages) {
            if (msg.key.fromMe) continue;
            const texto = msg.message?.conversation || msg.message?.extendedTextMessage?.text || '';
            const numero = msg.key.remoteJid.replace('@s.whatsapp.net', '');

            if (texto.trim().toUpperCase() === 'RENOVAR') {
                try {
                    const res = await axios.get(`${API_URL}/api/interno/clientes-por-notificar?api_key=${API_KEY}`);
                    const mensajeRenovar = res.data.mensaje_renovar || '✅ Gracias por tu interés. Te contactamos pronto.';
                    await enviarMensaje(msg.key.remoteJid, mensajeRenovar);
                    console.log(`✅ Respuesta RENOVAR enviada a ${numero}`);
                } catch (e) {
                    console.error('Error respondiendo RENOVAR:', e.message);
                }
            }
        }
    });
}

// ─── ENVIAR MENSAJE ───────────────────────────────────────────────────────────

async function enviarMensaje(jid, texto, archivoPath = null, tipoArchivo = null) {
    if (!sock || !botConectado) throw new Error('Bot no conectado');

    if (archivoPath && tipoArchivo) {
        const archivoCompleto = path.join(__dirname, '..', 'backend', archivoPath);
        if (fs.existsSync(archivoCompleto)) {
            const buffer = fs.readFileSync(archivoCompleto);
            const mimeTypes = {
                image: 'image/jpeg',
                document: 'application/pdf',
                video: 'video/mp4'
            };
            const mime = mimeTypes[tipoArchivo] || 'application/octet-stream';

            if (tipoArchivo === 'image') {
                await sock.sendMessage(jid, {
                    image: buffer,
                    caption: texto
                });
                return;
            } else if (tipoArchivo === 'video') {
                await sock.sendMessage(jid, {
                    video: buffer,
                    caption: texto
                });
                return;
            } else {
                await sock.sendMessage(jid, {
                    document: buffer,
                    mimetype: mime,
                    fileName: path.basename(archivoCompleto),
                    caption: texto
                });
                return;
            }
        }
    }

    await sock.sendMessage(jid, { text: texto });
}

// ─── CRON DE NOTIFICACIONES ───────────────────────────────────────────────────

function iniciarCron() {
    if (cronJob) {
        cronJob.stop();
    }

    // Correr cada hora y verificar hora configurada
    cronJob = cron.schedule('0 * * * *', async () => {
        await ejecutarNotificaciones();
    });

    // También ejecutar al conectar para verificar si hay algo pendiente
    console.log('⏰ Cron de notificaciones iniciado');
}

async function ejecutarNotificaciones() {
    if (!botConectado) {
        console.log('⚠️ Bot no conectado, saltando notificaciones');
        return;
    }

    console.log('🔔 Verificando notificaciones pendientes...');
    try {
        const res = await axios.get(`${API_URL}/api/interno/clientes-por-notificar?api_key=${API_KEY}`);
        const { notificaciones } = res.data;

        if (notificaciones.length === 0) {
            console.log('✅ Sin notificaciones pendientes');
            return;
        }

        console.log(`📨 Enviando ${notificaciones.length} notificaciones...`);

        for (const notif of notificaciones) {
            const jid = `${notif.numero}@s.whatsapp.net`;
            let exitoso = true;
            let errorMsg = null;

            try {
                await enviarMensaje(jid, notif.mensaje, notif.archivo, notif.tipo_archivo);
                console.log(`✅ Notificación ${notif.tipo} enviada a ${notif.numero} (${notif.nombre})`);
                // Pausa entre mensajes para no ser bloqueado
                await new Promise(r => setTimeout(r, 2000));
            } catch (e) {
                exitoso = false;
                errorMsg = e.message;
                console.error(`❌ Error enviando a ${notif.numero}:`, e.message);
            }

            // Registrar en el log
            try {
                await axios.post(`${API_URL}/api/interno/log-notificacion`, null, {
                    params: {
                        cliente_id: notif.cliente_id,
                        numero: notif.numero,
                        tipo: notif.tipo,
                        exitoso,
                        api_key: API_KEY,
                        error: errorMsg
                    }
                });
            } catch (e) {
                console.error('Error registrando log:', e.message);
            }
        }
    } catch (e) {
        console.error('Error obteniendo notificaciones:', e.message);
    }
}

// ─── API INTERNA DEL BOT ──────────────────────────────────────────────────────

app.get('/status', (req, res) => {
    res.json({
        conectado: botConectado,
        qr: qrActual,
        numero_conectado: numeroConectado
    });
});

app.post('/reiniciar', async (req, res) => {
    botConectado = false;
    qrActual = null;
    if (sock) {
        try { sock.end(); } catch (e) {}
    }
    // Eliminar sesión para forzar nuevo QR
    if (fs.existsSync(AUTH_DIR)) {
        fs.rmSync(AUTH_DIR, { recursive: true });
    }
    setTimeout(conectarBot, 1000);
    res.json({ message: 'Bot reiniciando...' });
});

app.post('/enviar', async (req, res) => {
    const { numero, mensaje, archivo, tipo } = req.body;
    try {
        const jid = `${numero}@s.whatsapp.net`;
        await enviarMensaje(jid, mensaje, archivo, tipo);
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/notificar-ahora', async (req, res) => {
    ejecutarNotificaciones();
    res.json({ message: 'Notificaciones ejecutándose...' });
});

// ─── INICIO ───────────────────────────────────────────────────────────────────

app.listen(BOT_PORT, () => {
    console.log(`🤖 MenaBot Panel - Bot API escuchando en puerto ${BOT_PORT}`);
});

conectarBot().catch(console.error);
