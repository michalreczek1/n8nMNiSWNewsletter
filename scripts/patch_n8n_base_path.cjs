const fs = require('node:fs');
const path = require('node:path');

const file = '/usr/local/lib/node_modules/n8n/dist/commands/start.js';
const before = 'const n8nPath = this.globalConfig.path;';
const after = "const n8nPath = this.globalConfig.path || '/';";
const source = fs.readFileSync(file, 'utf8');
if (source.split(before).length !== 2) {
  throw new Error('Unexpected n8n static asset generator; review patch before upgrading');
}
fs.writeFileSync(file, source.replace(before, after));

const packagesDir = '/usr/local/lib/node_modules/n8n/node_modules/.pnpm';
const editorPackage = fs.readdirSync(packagesDir).find((name) => name.startsWith('n8n-editor-ui@'));
if (!editorPackage) throw new Error('n8n editor UI package not found');
const indexFile = path.join(packagesDir, editorPackage, 'node_modules/n8n-editor-ui/dist/index.html');
const oldScript = '/{{BASE_PATH}}/static/base-path.js';
const newScript = `${oldScript}?v=2.40.5-basepath2`;
const index = fs.readFileSync(indexFile, 'utf8');
if (index.split(oldScript).length !== 2) {
  throw new Error('Unexpected n8n editor index; review patch before upgrading');
}
fs.writeFileSync(indexFile, index.replace(oldScript, newScript));
