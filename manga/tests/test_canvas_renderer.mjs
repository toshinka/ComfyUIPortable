/**
 * test_canvas_renderer.mjs — Canvas Renderer & Host Glue Exclusion Tests
 * =======================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Verifies:
 * 1. Scene geometry renderer accepts current document.
 * 2. CAST/Instance/Frame/Guide fixture accepted and rendered.
 * 3. Strict verification of ZERO ComfyUI host imports / LiteGraph references.
 */

import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert';
import { fileURLToPath } from 'node:url';
import { createDefaultAuthoringDocument, createRichAuthoringFixture } from '../app/src/domain/authoring_document.js';
import { SessionState } from '../app/src/state/session_state.js';
import { renderMangaCanvas } from '../app/src/view/canvas_renderer.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('--- Running test_canvas_renderer.mjs ---');

function createMockCanvas(w = 416, h = 608) {
    const operations = [];
    const ctx = {
        clearRect: (...args) => operations.push({ op: 'clearRect', args }),
        fillRect: (...args) => operations.push({ op: 'fillRect', args }),
        strokeRect: (...args) => operations.push({ op: 'strokeRect', args }),
        fillText: (...args) => operations.push({ op: 'fillText', args }),
        drawImage: (...args) => operations.push({ op: 'drawImage', args }),
        measureText: (txt) => ({ width: (txt || '').length * 6 }),
        save: () => operations.push({ op: 'save' }),
        restore: () => operations.push({ op: 'restore' }),
        setLineDash: (d) => operations.push({ op: 'setLineDash', d })
    };
    return {
        width: w,
        height: h,
        getContext: (type) => ctx,
        _getOperations: () => operations
    };
}

// Check 1: Default document renders scenes
const defaultDoc = createDefaultAuthoringDocument();
const session = new SessionState();
const canvas1 = createMockCanvas();
renderMangaCanvas(canvas1, defaultDoc, session);
const ops1 = canvas1._getOperations();
assert.ok(ops1.some(o => o.op === 'strokeRect'), 'Canvas must draw strokeRects for scenes');
assert.ok(ops1.some(o => o.op === 'fillText' && o.args[0].includes('Scene 1')), 'Must label Scene 1');
console.log('✓ Check 5 Passed: Scene geometry renderer accepts current document');

// Check 2: Rich fixture renders all layers
const richDoc = createRichAuthoringFixture();
const canvas2 = createMockCanvas();
const mockImage = { complete: true, naturalWidth: 800, naturalHeight: 600 };
const imageCache = { [richDoc.pages[0].guides[0].asset_reference]: mockImage };
canvas2.getContext('2d').drawImage = (...args) => canvas2._getOperations().push({ op: 'drawImage', args });

renderMangaCanvas(canvas2, richDoc, session, 0, imageCache);
const ops2 = canvas2._getOperations();
assert.ok(ops2.some(o => o.op === 'fillText' && (o.args[0].includes('frame_1') || o.args[0].includes('Frame 1'))), 'Must render Frame 1');
assert.ok(ops2.some(o => o.op === 'fillText' && o.args[0].includes('Ren')), 'Must render Cast/Instance Ren');
assert.ok(ops2.some(o => o.op === 'fillText' && o.args[0].toLowerCase().includes('guide')), 'Must render Guide');
assert.ok(ops2.some(o => o.op === 'fillText' && o.args[0].includes('fig_ren')), 'Must render Figure fig_ren');
assert.ok(ops2.some(o => o.op === 'drawImage'), 'Must invoke drawImage when imageCache has loaded image');
console.log('✓ Check 6 Passed: CAST/Instance/Frame/Guide fixture accepted and rendered with image preview');

// Check 3: Verify Zero ComfyUI host imports in ComfyUIPortable/manga/app/
const appDir = path.resolve(__dirname, '..', 'app');
const forbiddenPatterns = [
    'scripts/app.js',
    'scripts/api.js',
    'app.registerExtension',
    'LiteGraph',
    'node.addDOMWidget',
    'node.widgets',
    'app.graph'
];

function scanFiles(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const ent of entries) {
        const full = path.join(dir, ent.name);
        if (ent.isDirectory()) {
            scanFiles(full);
        } else if (ent.name.endsWith('.js') || ent.name.endsWith('.html')) {
            const content = fs.readFileSync(full, 'utf8');
            for (const pat of forbiddenPatterns) {
                assert.strictEqual(
                    content.includes(pat),
                    false,
                    'Forbidden ComfyUI host pattern ' + pat + ' found in ' + full
                );
            }
        }
    }
}
scanFiles(appDir);
console.log('✓ Check 7 Passed: Zero ComfyUI host imports or LiteGraph dependencies in standalone app');
console.log('All canvas and host isolation checks PASSED.');
