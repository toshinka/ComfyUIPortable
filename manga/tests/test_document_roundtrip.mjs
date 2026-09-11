import assert from 'node:assert/strict';
import { AuthoringStore } from '../app/src/state/authoring_store.js';
import { validateAuthoringDocument, FORBIDDEN_SESSION_KEYS } from '../app/src/domain/authoring_document.js';

console.log('--- Running test_document_roundtrip.mjs (M1B Durable Parity) ---');

// 1. Initial store
const store1 = new AuthoringStore();

// 2. Perform operations through store
// Add Scene
const sc3 = store1.addScene({
  name: 'Scene 3 New',
  prompt: 'busy market street with colorful stalls',
  negative_prompt: 'dark alley'
});

// Update Scene top
store1.updateScene('scene_top', {
  name: 'Updated Scene Top',
  prompt: 'sunset classroom with golden light',
  negative_prompt: 'rain outside'
});
store1.moveScene('scene_top', 0.02, 0.01);
const currTop = store1.getPage().scenes.find(s => s.scene_id === 'scene_top');
store1.resizeScene('scene_top', {
  x: currTop.area.x,
  y: currTop.area.y,
  w: currTop.area.w + 0.05,
  h: currTop.area.h - 0.02
});

// Add CAST entries
const castHero = store1.addCast({
  display_name: 'Hero Protagonist',
  identity_prompt: 'young male anime hero with spiky hair',
  negative_prompt: 'armor broken'
});

const castRival = store1.addCast({
  display_name: 'Dark Rival',
  identity_prompt: 'tall swordsman with dark cloak',
  negative_prompt: 'unarmed'
});

// Update CAST
store1.updateCast(castHero.cast_id, {
  display_name: 'Hero (Awakened)',
  identity_prompt: 'young male anime hero with glowing aura'
});

// Place Characters
const inst1 = store1.placeCharacter(sc3.scene_id, castHero.cast_id);
const inst2 = store1.placeCharacter('scene_top', castRival.cast_id);

// Update Character
store1.updateCharacter(inst1.instance_id, {
  acting_prompt: 'standing determined with clenched fists'
});
store1.moveCharacter(inst1.instance_id, 0.01, 0.02);
store1.resizeCharacter(inst1.instance_id, inst1.area.w + 0.02, inst1.area.h + 0.03);

// Update Global Seed & Style
store1.setSeed(987654);
store1.setStyleMetadata({
  styleTemplate: 'Manga Color',
  stylePrompt: 'vibrant colors, dramatic watercolor shading',
  styleNegativePrompt: 'greyscale, muddy'
});

// 3. Export JSON
const jsonExport1 = store1.exportJson();
const parsed1 = JSON.parse(jsonExport1);

// Verify valid schema
const val1 = validateAuthoringDocument(parsed1);
assert.equal(val1.valid, true, `Exported doc must be valid: ${JSON.stringify(val1.errors)}`);

// Verify session states are excluded
for (const forbidden of FORBIDDEN_SESSION_KEYS) {
  assert.equal(forbidden in parsed1, false, `Key ${forbidden} must not be in exported JSON`);
  if (parsed1.pages && parsed1.pages[0]) {
    assert.equal(forbidden in parsed1.pages[0], false, `Key ${forbidden} must not be in page JSON`);
  }
}
assert.equal('selection' in parsed1, false, 'selection must not be exported');
assert.equal('selectedSceneId' in parsed1, false, 'selectedSceneId must not be exported');
assert.equal('selectedCharacterId' in parsed1, false, 'selectedCharacterId must not be exported');
assert.equal('selectedCastId' in parsed1, false, 'selectedCastId must not be exported');
assert.equal('hover' in parsed1, false, 'hover state must not be exported');
assert.equal('runtime_mode' in parsed1, false, 'runtime_mode must not be exported');

// 4. Re-import into a fresh store
const store2 = new AuthoringStore();
const importRes = store2.importJson(jsonExport1);
assert.equal(importRes.ok, true, `Import must succeed: ${importRes.error}`);

const jsonExport2 = store2.exportJson();
const parsed2 = JSON.parse(jsonExport2);

// 5. Deep equality between exported documents
assert.deepEqual(parsed2, parsed1, 'Re-imported document exported JSON must match parsed1');

// Verify specific durable fields
const p2 = parsed2.pages[0];
assert.equal(p2.generation.seed, 987654);
assert.equal(p2.metadata.style_template, 'Manga Color');
assert.equal(p2.style_prompt, 'vibrant colors, dramatic watercolor shading');

assert.equal(p2.cast.length, 2);
const expHero = p2.cast.find(c => c.cast_id === castHero.cast_id);
assert.equal(expHero.display_name, 'Hero (Awakened)');
assert.equal(expHero.identity_prompt, 'young male anime hero with glowing aura');

assert.equal(p2.scenes.length, 3);
const expSceneTop = p2.scenes.find(s => s.scene_id === 'scene_top');
assert.equal(expSceneTop.name, 'Updated Scene Top');
assert.equal(expSceneTop.prompt, 'sunset classroom with golden light');
assert.equal(expSceneTop.input_mode, 'cast');

const expScene3 = p2.scenes.find(s => s.scene_id === sc3.scene_id);
assert.equal(expScene3.name, 'Scene 3 New');
assert.equal(expScene3.prompt, 'busy market street with colorful stalls');

assert.equal(p2.character_instances.length, 2);
const expInst1 = p2.character_instances.find(ci => ci.instance_id === inst1.instance_id);
assert.equal(expInst1.acting_prompt, 'standing determined with clenched fists');
assert.equal(expInst1.cast_id, castHero.cast_id);
assert.equal(expInst1.scene_id, sc3.scene_id);

console.log('✓ Check Passed: export -> re-import durable parity verified');
console.log('✓ Check Passed: session state completely excluded');
console.log('✓ Check Passed: schema valid before and after');
console.log('==================================================');
console.log('ALL ROUNDTRIP TESTS PASSED (M1B)');
console.log('==================================================');
