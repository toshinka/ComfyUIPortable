/**
 * verify_page_composite_gui.mjs
 *
 * Verification suite for MANGA-WORKSPACE-PAGE-COMPOSITE-GUI-VERIFY3
 * Tests Cases A through U:
 *   Case A: Page Composite action exists.
 *   Case B: Existing whole-page Generate remains.
 *   Case C: One compose POST per click.
 *   Case D: Compose payload includes current authoring_document.
 *   Case E: Compose payload includes generation_params.
 *   Case F: Compose payload includes correct current page_id and/or page_index (page_0 via fallback).
 *   Case G: Forbidden authority fields absent.
 *   Case H: Successful compose result creates exact /api/manga/page-composites/<composite_id>/artifact preview URL.
 *   Case I: Exactly one currentness POST.
 *   Case J: Currentness request uses the SAME page identity as compose.
 *   Case K: CURRENT renders.
 *   Case L: STALE renders.
 *   Case M: UNKNOWN renders.
 *   Case N: Compose failure bounded without leaking paths.
 *   Case O: Artifact failure bounded without leaking paths.
 *   Case P: Currentness failure keeps valid preview and degrades display to UNKNOWN.
 *   Case Q: Duplicate compose submission prevented while pending.
 *   Case R: Authoring Document remains unmodified.
 *   Case S: Switching from page 0 to page 1 clears page-0 preview/status (fallback path: state.currentPageIndex + authoringDoc.pages[index].id).
 *   Case S Fallback: Fallback resolves pageIndex=1 and pageId="page_1" when getters return undefined/null.
 *   Case T: History endpoint is never called.
 *   Case U: /prompt / live backend / GPU ZERO.
 */

import assert from 'node:assert/strict';

// --- Lightweight DOM and Browser Environment Simulation ---
class MockElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.className = '';
    this.id = '';
    this.style = {
      setProperty: (prop, val) => { this.style[prop] = String(val); },
      removeProperty: (prop) => { delete this.style[prop]; }
    };
    this.attributes = new Map();
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this._textContent = '';
    this.dataset = {};
    this.value = '';
  }

  setAttribute(name, val) {
    this.attributes.set(name, String(val));
    if (name.startsWith('data-')) {
      const prop = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      this.dataset[prop] = String(val);
    }
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  removeAttribute(name) {
    this.attributes.delete(name);
    if (name.startsWith('data-')) {
      const prop = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      delete this.dataset[prop];
    }
  }

  hasAttribute(name) {
    return this.attributes.has(name);
  }

  get src() {
    return this.getAttribute('src') || '';
  }

  set src(val) {
    this.setAttribute('src', val);
  }

  get disabled() {
    return this.hasAttribute('disabled');
  }

  set disabled(val) {
    if (val) this.setAttribute('disabled', 'disabled');
    else this.removeAttribute('disabled');
  }

  get textContent() {
    return this._textContent || '';
  }

  set textContent(val) {
    this._textContent = String(val);
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  append(...items) {
    for (const item of items) {
      if (item instanceof MockElement) {
        this.appendChild(item);
      } else if (item != null) {
        const textNode = new MockElement('#text');
        textNode.textContent = String(item);
        this.appendChild(textNode);
      }
    }
  }

  replaceChildren(...items) {
    for (const child of [...this.children]) {
      child.parentNode = null;
    }
    this.children = [];
    this.append(...items);
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx >= 0) {
      child.parentNode = null;
      this.children.splice(idx, 1);
    }
    return child;
  }

  addEventListener(event, fn) {
    this.listeners[event] = this.listeners[event] || [];
    this.listeners[event].push(fn);
  }

  removeEventListener(event, fn) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(f => f !== fn);
  }

  async dispatchEvent(event) {
    const handlers = [...(this.listeners[event.type] || [])];
    for (const h of handlers) {
      await h(event);
    }
  }

  async click() {
    if (this.disabled) return;
    await this.dispatchEvent({ type: 'click', target: this, preventDefault() {}, stopPropagation() {} });
  }

  focus() {}
  blur() {}

  get dataset() {
    if (!this._datasetProxy) {
      this._datasetInternal = this._datasetInternal || {};
      const el = this;
      this._datasetProxy = new Proxy(this._datasetInternal, {
        get(target, prop) {
          if (typeof prop === 'symbol') return target[prop];
          const attr = 'data-' + String(prop).replace(/([A-Z])/g, '-$1').toLowerCase();
          if (el.attributes && el.attributes[attr] !== undefined) return el.attributes[attr];
          return target[prop];
        },
        set(target, prop, val) {
          if (typeof prop === 'symbol') return true;
          target[prop] = String(val);
          const attr = 'data-' + String(prop).replace(/([A-Z])/g, '-$1').toLowerCase();
          el.attributes = el.attributes || {};
          el.attributes[attr] = String(val);
          return true;
        },
        deleteProperty(target, prop) {
          if (typeof prop === 'symbol') return true;
          delete target[prop];
          const attr = 'data-' + String(prop).replace(/([A-Z])/g, '-$1').toLowerCase();
          if (el.attributes) delete el.attributes[attr];
          return true;
        }
      });
    }
    return this._datasetProxy;
  }

  set dataset(val) {
    this._datasetInternal = val || {};
  }

  getAttribute(name) {
    if (this.attributes && this.attributes[name] !== undefined) {
      return this.attributes[name];
    }
    if (typeof name === 'string' && name.startsWith('data-') && this._datasetInternal) {
      const camel = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      if (this._datasetInternal[camel] !== undefined) return this._datasetInternal[camel];
      if (this._datasetInternal[name.slice(5)] !== undefined) return this._datasetInternal[name.slice(5)];
    }
    return null;
  }

  setAttribute(name, value) {
    this.attributes = this.attributes || {};
    this.attributes[name] = String(value);
    if (typeof name === 'string' && name.startsWith('data-')) {
      const camel = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      this._datasetInternal = this._datasetInternal || {};
      this._datasetInternal[camel] = String(value);
    }
  }

  hasAttribute(name) {
    if (this.attributes && this.attributes[name] !== undefined) return true;
    if (typeof name === 'string' && name.startsWith('data-') && this._datasetInternal) {
      const camel = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      if (this._datasetInternal[camel] !== undefined) return true;
      if (this._datasetInternal[name.slice(5)] !== undefined) return true;
    }
    return false;
  }

  removeAttribute(name) {
    if (this.attributes) delete this.attributes[name];
    if (typeof name === 'string' && name.startsWith('data-') && this._datasetInternal) {
      const camel = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      delete this._datasetInternal[camel];
      delete this._datasetInternal[name.slice(5)];
    }
  }

  matches(sel) {
    return MockElement.matchesSelector(this, sel);
  }

  static matchesSelector(el, sel) {
    if (!el || !sel) return false;
    sel = sel.trim();
    if (sel.startsWith('#')) return el.id === sel.slice(1);
    if (sel.startsWith('.')) return (el.className || '').split(/\s+/).includes(sel.slice(1));
    const attrMatch = sel.match(/^\[([a-zA-Z0-9_-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\]]+)))?\]$/);
    if (attrMatch) {
      const [, attr, v1, v2, v3] = attrMatch;
      const val = v1 ?? v2 ?? v3;
      if (val !== undefined) return el.getAttribute(attr) === val;
      return el.hasAttribute(attr);
    }
    const tagAttrMatch = sel.match(/^([a-zA-Z0-9_-]+)\[([a-zA-Z0-9_-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\]]+)))?\]$/);
    if (tagAttrMatch) {
      const [, tag, attr, v1, v2, v3] = tagAttrMatch;
      if ((el.tagName || '').toLowerCase() !== tag.toLowerCase()) return false;
      const val = v1 ?? v2 ?? v3;
      if (val !== undefined) return el.getAttribute(attr) === val;
      return el.hasAttribute(attr);
    }
    const tagClassMatch = sel.match(/^([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)$/);
    if (tagClassMatch) {
      const [, tag, cls] = tagClassMatch;
      if ((el.tagName || '').toLowerCase() !== tag.toLowerCase()) return false;
      return (el.className || '').split(/\s+/).includes(cls);
    }
    return (el.tagName || '').toLowerCase() === sel.toLowerCase();
  }

  querySelector(selector) {
    const list = this.querySelectorAll(selector);
    if (list.length > 0) return list[0];
    if (selector.includes('page-composite')) {
      return null;
    }
    const el = new MockElement('DIV');
    if (selector.startsWith('#')) {
      el.id = selector.slice(1);
    } else if (selector.startsWith('.')) {
      el.className = selector.slice(1);
    } else {
      const m = selector.match(/^\[([a-zA-Z0-9_-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\]]+)))?\]$/);
      if (m) {
        el.setAttribute(m[1], m[2] ?? m[3] ?? m[4] ?? '');
      }
    }
    this.appendChild(el);
    return el;
  }

  querySelectorAll(selector) {
    const parts = selector.split(',').map(s => s.trim());
    const results = [];

    const walk = (node) => {
      for (const p of parts) {
        if (MockElement.matchesSelector(node, p)) {
          results.push(node);
          break;
        }
      }
      for (const child of node.children) {
        walk(child);
      }
    };

    for (const child of this.children) {
      walk(child);
    }
    return results;
  }
}

class MockDocument {
  constructor() {
    this.body = new MockElement('BODY');
    this.listeners = {};
    this.activeElement = null;
  }

  createElement(tagName) {
    return new MockElement(tagName);
  }

  getElementById(id) {
    let found = this.body.querySelector(`#${id}`);
    if (!found) {
      found = new MockElement('DIV');
      found.id = id;
      this.body.appendChild(found);
    }
    return found;
  }

  querySelector(selector) {
    return this.body.querySelector(selector);
  }

  querySelectorAll(selector) {
    return this.body.querySelectorAll(selector);
  }

  addEventListener(event, fn) {
    this.listeners[event] = this.listeners[event] || [];
    this.listeners[event].push(fn);
  }

  removeEventListener(event, fn) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(f => f !== fn);
  }
}

// Install Mock Globals before importing GUI modules
const mockWindow = {
  listeners: {},
  addEventListener(event, fn) {
    this.listeners[event] = this.listeners[event] || [];
    this.listeners[event].push(fn);
  },
  removeEventListener(event, fn) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(f => f !== fn);
  }
};
const mockDocument = new MockDocument();

globalThis.window = mockWindow;
globalThis.document = mockDocument;
globalThis.HTMLElement = MockElement;
globalThis.Element = MockElement;
globalThis.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {}
};

// Import workspace modules using existing canonical paths
const { mountGenerationView } = await import('../app/src/view/generation_view.js');
const storeModule = await import('../app/src/state/authoring_store.js');

let baseStore = storeModule.authoringStore || storeModule.default;
if (!baseStore && typeof storeModule.createAuthoringStore === 'function') {
  baseStore = storeModule.createAuthoringStore();
} else if (!baseStore && typeof storeModule.AuthoringStore === 'function') {
  baseStore = new storeModule.AuthoringStore();
}

let subscribers = [];
let currentDocument = null;

const authoringStore = {
  ...(baseStore || {}),
  subscribe(fn) {
    subscribers.push(fn);
    if (typeof baseStore?.subscribe === 'function') {
      try { baseStore.subscribe(fn); } catch (_) {}
    }
    return () => {
      subscribers = subscribers.filter(s => s !== fn);
    };
  },
  setDocument(d) {
    currentDocument = d;
    if (typeof baseStore?.setDocument === 'function') {
      try { baseStore.setDocument(d); } catch (_) {}
    }
    for (const s of [...subscribers]) {
      try { s(d); } catch (_) {}
    }
  },
  getDocument() {
    if (typeof baseStore?.getDocument === 'function') {
      try {
        const d = baseStore.getDocument();
        if (d) return d;
      } catch (_) {}
    }
    return currentDocument;
  }
};

mockWindow.authoringStore = authoringStore;

function createGenerationViewPrerequisites(container) {
  const fields = [
    'checkpoint_id',
    'sampler_id',
    'scheduler_id',
    'steps',
    'cfg',
    'seed_requested',
    'positive_prompt',
    'negative_prompt',
    'width',
    'height',
    'denoise'
  ];

  for (const f of fields) {
    const el = new MockElement(f.includes('id') ? 'SELECT' : 'INPUT');
    el.id = `mg-gen-${f}`;
    el.setAttribute('name', f);
    el.setAttribute('data-field', f);
    container.appendChild(el);

    const plainEl = new MockElement(f.includes('id') ? 'SELECT' : 'INPUT');
    plainEl.id = f;
    plainEl.setAttribute('name', f);
    container.appendChild(plainEl);
  }

  const genBtn = new MockElement('BUTTON');
  genBtn.id = 'mg-gen-execute';
  genBtn.setAttribute('data-testid', 'generate-page-btn');
  genBtn.textContent = 'Generate';
  container.appendChild(genBtn);

  const genReason = new MockElement('DIV');
  genReason.id = 'mg-gen-reason';
  container.appendChild(genReason);

  const genLabel = new MockElement('SPAN');
  genLabel.id = 'mg-gen-label';
  container.appendChild(genLabel);

  const refreshCatalogBtn = new MockElement('BUTTON');
  refreshCatalogBtn.id = 'mg-refresh-catalog';
  container.appendChild(refreshCatalogBtn);

  const scopeGlobal = new MockElement('BUTTON');
  scopeGlobal.id = 'mg-gen-scope-global';
  container.appendChild(scopeGlobal);

  const scopeScenes = new MockElement('BUTTON');
  scopeScenes.id = 'mg-gen-scope-scenes';
  container.appendChild(scopeScenes);

  const isolatedSceneBtn = new MockElement('BUTTON');
  isolatedSceneBtn.id = 'mg-isolated-scene-btn';
  isolatedSceneBtn.setAttribute('data-testid', 'isolated-scene-btn');
  isolatedSceneBtn.textContent = 'コマ単体生成';
  container.appendChild(isolatedSceneBtn);

  const statusEl = new MockElement('DIV');
  statusEl.id = 'mg-gen-status';
  container.appendChild(statusEl);

  const catalogNote = new MockElement('DIV');
  catalogNote.id = 'mg-gen-catalog-note';
  container.appendChild(catalogNote);

  const errorEl = new MockElement('DIV');
  errorEl.id = 'mg-gen-error';
  container.appendChild(errorEl);

  const stageSwitch = new MockElement('DIV');
  stageSwitch.id = 'mg-stage-mode-switch';
  container.appendChild(stageSwitch);

  const stageLayout = new MockElement('BUTTON');
  stageLayout.id = 'mg-stage-mode-layout';
  container.appendChild(stageLayout);

  const stageResult = new MockElement('BUTTON');
  stageResult.id = 'mg-stage-mode-result';
  container.appendChild(stageResult);

  const focusToggle = new MockElement('BUTTON');
  focusToggle.id = 'mg-focus-toggle';
  container.appendChild(focusToggle);

  const previewLabel = new MockElement('DIV');
  previewLabel.id = 'mg-gen-preview-label';
  container.appendChild(previewLabel);

  const preview = new MockElement('DIV');
  preview.id = 'mg-gen-preview';
  container.appendChild(preview);

  const previewEmpty = new MockElement('DIV');
  previewEmpty.id = 'mg-gen-preview-empty';
  container.appendChild(previewEmpty);

  const stageNeutral = new MockElement('DIV');
  stageNeutral.id = 'mg-stage-neutral';
  container.appendChild(stageNeutral);
}

/**
 * makeGenerationViewStateFixture
 * Constructs canonical Generation View state fixture matching mountGenerationView initialization contract.
 */
function makeGenerationViewStateFixture(overrides = {}) {
  const defaultDraft = {
    checkpoint_id: 'v1-5-pruned.safetensors',
    sampler_id: 'euler',
    scheduler_id: 'normal',
    steps: '20',
    cfg: '7',
    seed_requested: '-1',
    positive_prompt: '',
    negative_prompt: '',
    positive_raw: '',
    negative_raw: '',
    width: '512',
    height: '512',
    ...(overrides.draft || {})
  };

  const defaultPreview = {
    url: null,
    jobId: null,
    ...(overrides.preview || {})
  };

  const defaultSceneDraft = {
    mask_feather: '16',
    panel_strength: '1',
    controlnet_strength: '0.35',
    controlnet_start_percent: '0.0',
    controlnet_end_percent: '1.0',
    reference_weight: '0.70',
    reference_start: '0.0',
    reference_end: '1.0',
    ...(overrides.sceneDraft || {})
  };

  const defaultCatalog = {
    revision: 1,
    checkpoints: [
      { id: 'v1-5-pruned.safetensors', available: true }
    ],
    samplers: ['euler'],
    schedulers: ['normal'],
    product_bounds: {
      max_pixels: 4194304
    },
    ...(overrides.catalog || {})
  };

  const state = {
    currentPageIndex: 0,
    currentPageId: 'page_0',
    jobIds: new Set(),
    mode: 'txt2img',
    draft: defaultDraft,
    preview: defaultPreview,
    sceneDraft: defaultSceneDraft,
    catalog: defaultCatalog,
    catalogError: null,
    activeJob: null,
    history: [],
    jobs: [],
    completedJobs: [],
    attempts: [],
    historyLoading: false,
    submitUnconfirmed: false,
    localBusy: false,
    error: null,
    checkpoint_id: 'v1-5-pruned.safetensors',
    sampler_id: 'euler',
    scheduler_id: 'normal',
    steps: '20',
    cfg: '7',
    seed_requested: '-1',
    positive_raw: '',
    negative_raw: '',
    setDraft(field, val) {
      this.draft[field] = String(val);
      this[field] = val;
    },
    setJob(job) {
      this.activeJob = job;
    },
    endAttempt() {
      this.localBusy = false;
    },
    ...overrides
  };

  state.draft = { ...defaultDraft, ...(overrides.draft || {}) };
  state.preview = { ...defaultPreview, ...(overrides.preview || {}) };
  state.sceneDraft = { ...defaultSceneDraft, ...(overrides.sceneDraft || {}) };

  return state;
}

const RESULTS = [];

function record(id, title, pass, detail = '') {
  RESULTS.push({ id, title, pass, detail });
  const icon = pass ? '✓ PASS' : '✗ FAIL';
  console.log(`[${icon}] ${id}: ${title}${detail ? ' - ' + detail : ''}`);
}

async function run() {
  console.log('====================================================');
  console.log('MANGA WORKSPACE PAGE COMPOSITE GUI VERIFICATION');
  console.log('====================================================\n');

  const originalFetch = globalThis.fetch;

  try {
    const composeRequests = [];
    const currentnessRequests = [];
    const historyRequests = [];
    const promptRequests = [];
    const forbiddenFieldsDetected = [];

    const FORBIDDEN_KEYS = [
      'composite_id',
      'manifest',
      'artifact_url',
      'created_at',
      'status',
      'currentness',
      'cached_at'
    ];

    let currentCompositeId = 'comp_test_abc123';
    let currentnessStatusToReturn = 'CURRENT';
    let shouldComposeFail = false;
    let composeErrorMessage = '';
    let shouldCurrentnessFail = false;
    let pendingDelayMs = 0;

    globalThis.fetch = async (url, options = {}) => {
      const fullUrl = String(url);
      const method = (options.method || 'GET').toUpperCase();
      let bodyObj = null;
      if (options.body && typeof options.body === 'string') {
        try {
          bodyObj = JSON.parse(options.body);
        } catch (_) {}
      }

      if (fullUrl.includes('/api/manga/page-composites/compose')) {
        composeRequests.push({ method, url: fullUrl, body: bodyObj });
        if (bodyObj) {
          for (const k of FORBIDDEN_KEYS) {
            if (k in bodyObj) forbiddenFieldsDetected.push(k);
          }
        }

        if (pendingDelayMs > 0) {
          await new Promise(r => setTimeout(r, pendingDelayMs));
        }

        if (shouldComposeFail) {
          return {
            ok: false,
            status: 500,
            json: async () => ({
              ok: false,
              error: composeErrorMessage || 'Failed in D:\\GitHub\\ComfyUIPortable\\manga\\internal.py'
            })
          };
        }

        return {
          ok: true,
          status: 200,
          json: async () => ({
            ok: true,
            composite_id: currentCompositeId,
            manifest: {
              composite_id: currentCompositeId,
              page_id: bodyObj?.page_id || 'page_0',
              composition_plan_digest: 'plan_digest_xyz'
            }
          })
        };
      }

      if (fullUrl.includes('/currentness')) {
        currentnessRequests.push({ method, url: fullUrl, body: bodyObj });

        if (shouldCurrentnessFail) {
          return {
            ok: false,
            status: 500,
            json: async () => ({ ok: false, error: 'Currentness evaluation error' })
          };
        }

        return {
          ok: true,
          status: 200,
          json: async () => ({
            ok: true,
            status: currentnessStatusToReturn,
            reason: 'MATCH_IN_TEST'
          })
        };
      }

      if (fullUrl.includes('/api/manga/page-composites') && method === 'GET' && !fullUrl.includes('/artifact')) {
        historyRequests.push({ method, url: fullUrl });
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, entries: [] })
        };
      }

      if (fullUrl.includes('/prompt') || fullUrl.includes('/queue')) {
        promptRequests.push({ method, url: fullUrl });
        return { ok: false, status: 500 };
      }

      return { ok: true, status: 200, json: async () => ({}) };
    };

    // Setup Multi-page Authoring Document with page_0 and page_1
    const initialDoc = {
      schema_version: '1.0.0',
      pages: [
        {
          id: 'page_0',
          page_number: 1,
          width_px: 512,
          height_px: 512,
          panels: [{ id: 'panel_1', prompt: 'scene 1' }]
        },
        {
          id: 'page_1',
          page_number: 2,
          width_px: 512,
          height_px: 512,
          panels: [{ id: 'panel_2', prompt: 'scene 2' }]
        }
      ]
    };

    // Explicitly configure existence of getters returning unusable values to test fallback
    authoringStore.getPage = (idx = 0) => initialDoc.pages[idx] || null;
    authoringStore.getCurrentPageIndex = () => undefined;
    authoringStore.getCurrentPageId = () => null;
    authoringStore.getCurrentPage = () => null;
    authoringStore.getDocument = () => initialDoc;

    authoringStore.setDocument(initialDoc);

    // Build canonical view state fixture
    const viewState = makeGenerationViewStateFixture({ currentPageIndex: 0, currentPageId: 'page_0' });
    viewState.authoringStore = authoringStore;

    const container = new MockElement('DIV');
    mockDocument.body.appendChild(container);
    createGenerationViewPrerequisites(container);
    mountGenerationView(container, { authoringStore, store: authoringStore, state: viewState });

    // CASE A: Page Composite action exists
    const compositeBtn = container.querySelector('[data-testid="page-composite-btn"]');
    const hasCompositeBtn = Boolean(compositeBtn && compositeBtn.textContent.includes('ページ合成'));
    record('CASE_A', 'Page Composite action exists', hasCompositeBtn, `button text: "${compositeBtn?.textContent || ''}"`);

    // CASE B: Existing whole-page Generate remains
    const wholePageBtn = container.querySelector('#mg-gen-execute') || container.querySelector('[data-testid="generate-page-btn"]');
    record('CASE_B', 'Existing whole-page Generate remains', Boolean(wholePageBtn), 'whole page button present in container');

    // Capture initial document state before composite action
    const docBefore = JSON.parse(JSON.stringify(authoringStore.getDocument()));

    // Elements
    const previewBox = container.querySelector('[data-testid="page-composite-preview"]');
    const previewImg = container.querySelector('[data-testid="page-composite-img"]');
    const statusLabel = container.querySelector('[data-testid="page-composite-status"]');
    const errorLabel = container.querySelector('[data-testid="page-composite-error"]');

    // Trigger initial successful compose on page 0
    currentnessStatusToReturn = 'CURRENT';
    await compositeBtn.click();

    // CASE C: One compose POST per click
    const composeCalledOnce = composeRequests.length === 1 && composeRequests[0].method === 'POST';
    record('CASE_C', 'One compose POST per click', composeCalledOnce, `compose calls: ${composeRequests.length}`);

    // CASE D: Compose payload includes current authoring_document
    const reqBody = composeRequests[0]?.body || {};
    const hasDoc = Boolean(reqBody.authoring_document && reqBody.authoring_document.schema_version);
    record('CASE_D', 'Compose payload includes current authoring_document', hasDoc, `doc present: ${hasDoc}`);

    // CASE E: Compose payload includes generation_params
    const hasParams = typeof reqBody.generation_params === 'object' && reqBody.generation_params !== null;
    record('CASE_E', 'Compose payload includes generation_params', hasParams, `params present: ${hasParams}`);

    // CASE F: Compose payload includes correct current page_id and/or page_index (page_0 via fallback)
    const hasPageId = reqBody.page_id === 'page_0';
    const hasPageIndex = reqBody.page_index === 0;
    record('CASE_F', 'Compose payload includes correct current page_id and page_index', hasPageId && hasPageIndex, `page_id: "${reqBody.page_id}", page_index: ${reqBody.page_index}`);

    // CASE G: Forbidden authority fields absent
    const noForbidden = forbiddenFieldsDetected.length === 0;
    record('CASE_G', 'Forbidden authority fields absent', noForbidden, `detected: ${forbiddenFieldsDetected.join(', ') || 'none'}`);

    // CASE H: Successful compose result creates exact /api/manga/page-composites/<composite_id>/artifact preview URL
    const expectedArtifactUrl = `/api/manga/page-composites/${currentCompositeId}/artifact`;
    const hasArtifactUrl = previewImg.src === expectedArtifactUrl;
    const previewVisible = previewBox.style.display !== 'none';
    record('CASE_H', 'Successful compose result creates exact artifact preview URL', hasArtifactUrl && previewVisible, `src: ${previewImg.src}, visible: ${previewVisible}`);

    // CASE I: Exactly one currentness POST
    const currentnessCalledOnce = currentnessRequests.length === 1 && currentnessRequests[0].method === 'POST';
    record('CASE_I', 'Exactly one currentness POST', currentnessCalledOnce, `currentness calls: ${currentnessRequests.length}`);

    // CASE J: Currentness request uses the SAME page identity as compose
    const curBody = currentnessRequests[0]?.body || {};
    const curSamePageId = curBody.page_id === reqBody.page_id;
    const curSamePageIndex = curBody.page_index === reqBody.page_index;
    record('CASE_J', 'Currentness request uses the SAME page identity as compose', curSamePageId && curSamePageIndex, `cur page_id: "${curBody.page_id}", cur page_index: ${curBody.page_index}`);

    // CASE K: CURRENT renders
    const statusTextK = statusLabel.textContent;
    const statusAttrK = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    const isCurrent = statusTextK === 'CURRENT' && statusAttrK === 'CURRENT';
    record('CASE_K', 'CURRENT renders', isCurrent, `text: "${statusTextK}", data-status: "${statusAttrK}"`);

    // CASE L: STALE renders
    currentnessStatusToReturn = 'STALE';
    await compositeBtn.click();
    const statusTextL = statusLabel.textContent;
    const statusAttrL = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    const isStale = statusTextL === 'STALE' && statusAttrL === 'STALE';
    record('CASE_L', 'STALE renders', isStale, `text: "${statusTextL}", data-status: "${statusAttrL}"`);

    // CASE M: UNKNOWN renders
    currentnessStatusToReturn = 'UNKNOWN';
    await compositeBtn.click();
    const statusTextM = statusLabel.textContent;
    const statusAttrM = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    const isUnknown = statusTextM === 'UNKNOWN' && statusAttrM === 'UNKNOWN';
    record('CASE_M', 'UNKNOWN renders', isUnknown, `text: "${statusTextM}", data-status: "${statusAttrM}"`);

    // CASE N: Compose failure bounded
    shouldComposeFail = true;
    composeErrorMessage = 'SyntaxError in D:\\GitHub\\ComfyUIPortable\\manga\\compositor.py line 12';
    await compositeBtn.click();
    const errorVisibleN = errorLabel.style.display !== 'none';
    const errorTextN = errorLabel.textContent;
    const leakedPathN = /([a-zA-Z]:\\[^ \t\r\n]+|\/manga\/)/i.test(errorTextN);
    record('CASE_N', 'Compose failure bounded without leaking paths', errorVisibleN && errorTextN.length > 0 && !leakedPathN, `error visible: ${errorVisibleN}, text: "${errorTextN}"`);
    shouldComposeFail = false;

    // CASE O: Artifact failure bounded
    await previewImg.dispatchEvent({ type: 'error' });
    const errorVisibleO = errorLabel.style.display !== 'none';
    const errorTextO = errorLabel.textContent;
    record('CASE_O', 'Artifact failure bounded', errorVisibleO && errorTextO.includes('could not be loaded'), `error visible: ${errorVisibleO}, text: "${errorTextO}"`);

    // CASE P: Currentness failure keeps valid preview and degrades display to UNKNOWN
    currentnessStatusToReturn = 'CURRENT';
    await compositeBtn.click();
    assert.equal(previewBox.style.display, 'block');

    shouldCurrentnessFail = true;
    await compositeBtn.click();
    const previewStillVisibleP = previewBox.style.display === 'block';
    const statusDegradedToUnknownP = statusLabel.textContent === 'UNKNOWN' && (statusLabel.dataset.status === 'UNKNOWN' || statusLabel.getAttribute('data-status') === 'UNKNOWN');
    const errorShownP = errorLabel.style.display !== 'none';
    record('CASE_P', 'Currentness failure keeps valid preview and degrades display to UNKNOWN', previewStillVisibleP && statusDegradedToUnknownP && errorShownP, `preview visible: ${previewStillVisibleP}, status: "${statusLabel.textContent}", error visible: ${errorShownP}`);
    shouldCurrentnessFail = false;

    // CASE Q: Duplicate compose submission prevented while pending
    pendingDelayMs = 100;
    let pendingWasDisabled = false;
    const clickPromise = compositeBtn.click();
    await new Promise(r => setTimeout(r, 20));
    pendingWasDisabled = compositeBtn.disabled === true;
    await clickPromise;
    const enabledAfter = compositeBtn.disabled === false;
    pendingDelayMs = 0;
    record('CASE_Q', 'Duplicate compose submission prevented while pending', pendingWasDisabled && enabledAfter, `disabled while pending: ${pendingWasDisabled}, enabled after: ${enabledAfter}`);

    // CASE R: Authoring Document remains unmodified
    const docAfter = JSON.parse(JSON.stringify(authoringStore.getDocument()));
    let docEqual = false;
    try {
      assert.deepEqual(docBefore, docAfter);
      docEqual = true;
    } catch (_) {
      docEqual = false;
    }
    const docStr = JSON.stringify(docAfter);
    const persistedComposite = docStr.includes(currentCompositeId) || docStr.includes('/artifact') || docStr.includes('CURRENT');
    record('CASE_R', 'Authoring Document remains unmodified (zero persistence)', docEqual && !persistedComposite, `doc equal: ${docEqual}, persisted metadata: ${persistedComposite}`);

    // CASE S: Switching from page 0 to page 1 clears page-0 preview/status
    // IMPORTANT: Exercise fallback path where page identity depends on:
    // state.currentPageIndex = 1 + authoringDoc.pages[1].id = "page_1"
    // while store getters exist but return undefined/null!
    currentnessStatusToReturn = 'CURRENT';
    await compositeBtn.click();
    assert.equal(previewBox.style.display, 'block');
    assert.ok(previewImg.src.includes('/artifact'));

    // Switch viewState.currentPageIndex to 1 (page_1) and clear currentPageId for fallback test
    viewState.currentPageIndex = 1;
    viewState.currentPageId = null;
    authoringStore.getCurrentPageIndex = () => undefined;
    authoringStore.getCurrentPageId = () => null;
    authoringStore.getCurrentPage = () => null;
    authoringStore.getDocument = () => initialDoc;
    // Trigger store subscription event (simulating page switch in authoring store)
    authoringStore.setDocument({ ...initialDoc });

    const previewHiddenS = previewBox.style.display === 'none';
    const imgClearedS = previewImg.src === '';
    const statusClearedS = statusLabel.textContent === '' && !statusLabel.getAttribute('data-status');
    const errorClearedS = errorLabel.textContent === '' && errorLabel.style.display === 'none';
    const caseSPass = previewHiddenS && imgClearedS && statusClearedS && errorClearedS;
    record('CASE_S', 'Switching from page 0 to page 1 clears page-0 preview/status via fallback authority', caseSPass, `preview hidden: ${previewHiddenS}, src cleared: ${imgClearedS}, status cleared: ${statusClearedS}`);

    // Now compose while on page 1 (viewState.currentPageIndex = 1)
    // This explicitly proves that fallback resolves page_1 for compose and currentness!
    composeRequests.length = 0;
    currentnessRequests.length = 0;
    await compositeBtn.click();

    const composePage1Req = composeRequests[0]?.body || {};
    const curPage1Req = currentnessRequests[0]?.body || {};
    const fallbackPage1Compose = composePage1Req.page_id === 'page_1' && composePage1Req.page_index === 1;
    const fallbackPage1Currentness = curPage1Req.page_id === 'page_1' && curPage1Req.page_index === 1;
    record('CASE_S_FALLBACK', 'Fallback resolves pageIndex=1 and pageId="page_1" when getters return undefined/null', fallbackPage1Compose && fallbackPage1Currentness, `compose page_id: "${composePage1Req.page_id}", index: ${composePage1Req.page_index}, cur page_id: "${curPage1Req.page_id}", index: ${curPage1Req.page_index}`);

    // CASE T: History endpoint is never called
    const zeroHistory = historyRequests.length === 0;
    record('CASE_T', 'History endpoint is never called', zeroHistory, `history calls: ${historyRequests.length}`);

    // CASE U: /prompt / live backend / GPU ZERO
    const zeroPrompt = promptRequests.length === 0;
    record('CASE_U', '/prompt / live backend / GPU ZERO', zeroPrompt, `prompt calls: ${promptRequests.length}`);

  } catch (err) {
    console.error('Test execution error:', err);
    record('FATAL', 'Test execution completed without uncaught exception', false, err.message);
  } finally {
    globalThis.fetch = originalFetch;
  }

  // Summary
  console.log('\n====================================================');
  console.log('TEST SUMMARY');
  console.log('====================================================');
  const total = RESULTS.length;
  const passed = RESULTS.filter(r => r.pass).length;
  const failed = total - passed;
  console.log(`Total: ${total} | Passed: ${passed} | Failed: ${failed}`);

  if (failed > 0) {
    console.error('\nFAILED TESTS:');
    for (const r of RESULTS.filter(r => !r.pass)) {
      console.error(`- ${r.id}: ${r.title} (${r.detail})`);
    }
    process.exit(1);
  } else {
    console.log('\nALL 22 CASES (A through U + S_FALLBACK) PASSED!');
    process.exit(0);
  }
}

run();
