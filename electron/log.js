const fs = require('fs');
const path = require('path');

const logDir = path.join(process.resourcesPath, 'logs');
if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
const allLogPath = path.join(logDir, 'all.log');
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_LOG_FILES = 5;

function pad(n) { return n.toString().padStart(2, '0'); }
function getLocalTimeString() {
    const d = new Date();
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${d.getMilliseconds().toString().padStart(3, '0')}`;
}

function rotateLogIfNeeded() {
    if (fs.existsSync(allLogPath)) {
        const stats = fs.statSync(allLogPath);
        if (stats.size > MAX_LOG_SIZE) {
            const ts = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
            const rotated = allLogPath.replace(/\.log$/, `_${ts}.log`);
            fs.renameSync(allLogPath, rotated);
            // 清理多余的历史日志
            const files = fs.readdirSync(logDir)
                .filter(f => f.startsWith('all_') && f.endsWith('.log'))
                .sort((a, b) => fs.statSync(path.join(logDir, b)).mtimeMs - fs.statSync(path.join(logDir, a)).mtimeMs);
            files.slice(MAX_LOG_FILES).forEach(f => fs.unlinkSync(path.join(logDir, f)));
        }
    }
}

function logToAll(msg, level = 'INFO', module = 'electron') {
    rotateLogIfNeeded();
    const line = `[${getLocalTimeString()}] [${module}] [${level}] ${msg}\n`;
    fs.appendFileSync(allLogPath, line, 'utf8');
}

module.exports = { logToAll, logDir, allLogPath };
