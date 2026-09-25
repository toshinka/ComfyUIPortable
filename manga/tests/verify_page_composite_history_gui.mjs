/**
 * verify_page_composite_history_gui.mjs
 *
 * Verifies Page Composite History GUI requirements under native Mock DOM environment.
 * Tests:
 * A. History action exists.
 * B. Existing Page Composite compose button remains.
 * C. Existing whole-page Generate remains.
 * D. History click issues exactly one GET /api/manga/page-composites?document_id=...&page_id=...
 * E. Request uses current page 0 identity.
 * F. Multi-page fallback uses page 1 identity when currentPageIndex=1 and getters return undefined/null.
 * G. Multiple entries all render.
 * H. Returned ordering is preserved exactly.
 * I. Same-plan-digest entries are not collapsed.
 * J. Empty history renders non-error empty state.
 * K. Selecting a history entry uses exact artifact URL.
 * L. Selection issues exactly one currentness POST.
 * M. Currentness uses CURRENT page identity.
 * N. CURRENT renders.
 * O. STALE renders.
 * P. UNKNOWN renders.
 * Q. History GET failure bounded.
 * R. Artifact failure bounded.
 * S. Currentness failure shows UNKNOWN and keeps list usable.
 * T. Pending history request prevents duplicate history submissions only.
 * U. Authoring mutation ZERO.
 * V. Page switch clears old-page history, selection, preview, and status.
 * W. History selection is never persisted into Authoring.
 * X. No metadata route call unless product actually requires it.
 * Y. No /prompt.
 * Z. No live backend / GPU.
 */

import assert from 'node:assert/strict';

// Setup Mock DOM environment
class MockElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.attributes = {};
    this._datasetInternal = {};
    this.listeners = {};
    this.style = {
      display: '',
      setProperty(prop, val) { this[prop] = String(val); },
      removeProperty(prop) { delete this[prop]; }
    };
    this.className = '';
    this.id = '';
    this.textContent = '';
    this.innerHTML = '';
    this.disabled = false;
    this.type = 'button';
    this.parentElement = null;
    this.src = '';
    this.alt = '';
  }

  get firstChild() {
    return this.children[0] || null;
  }

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

  get classList() {
    const el = this;
    return {
      add(...classes) {
        const current = (el.className || '').split(/\s+/).filter(Boolean);
        for (const c of classes) {
          if (!current.includes(c)) current.push(c);
        }
        el.className = current.join(' ');
      },
      remove(...classes) {
        const current = (el.className || '').split(/\s+/).filter(Boolean);
        el.className = current.filter(c => !classes.includes(c)).join(' ');
      },
      contains(cls) {
        return (el.className || '').split(/\s+/).includes(cls);
      },
      toggle(cls, force) {
        if (force === true) { this.add(cls); return true; }
        if (force === false) { this.remove(cls); return false; }
        if (this.contains(cls)) { this.remove(cls); return false; }
        this.add(cls); return true;
      }
    };
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
    if (typeof name === 'string' && name.startsWith('data-')) {
      const camel = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      if (this._datasetInternal) {
        delete this._datasetInternal[camel];
        delete this._datasetInternal[name.slice(5)];
      }
    }
  }

  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  append(...nodes) {
    for (const n of nodes) {
      if (!n) continue;
      if (typeof n === 'string') {
        const textNode = new MockElement('#text');
        textNode.textContent = n;
        this.appendChild(textNode);
      } else {
        this.appendChild(n);
      }
    }
  }

  replaceChildren(...nodes) {
    this.children = [];
    this.append(...nodes);
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      child.parentElement = null;
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
    this.defaultView = null;
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

  createElement(tagName) {
    return new MockElement(tagName);
  }

  getElementById(id) {
    return this.body.querySelector(`#${id}`);
  }

  querySelector(sel) {
    return this.body.querySelector(sel);
  }

  querySelectorAll(sel) {
    return this.body.querySelectorAll(sel);
  }
}

const mockDocument = new MockDocument();
globalThis.document = mockDocument;
globalThis.window = {
  document: mockDocument,
  listeners: {},
  addEventListener(event, fn) {
    this.listeners[event] = this.listeners[event] || [];
    this.listeners[event].push(fn);
  },
  removeEventListener(event, fn) {
    if (!this.listeners[event]) return;
    this.listeners[event] = this.listeners[event].filter(f => f !== fn);
  },
  async dispatchEvent(event) {
    const handlers = [...(this.listeners[event.type] || [])];
    for (const h of handlers) {
      await h(event);
    }
  }
};
mockDocument.defaultView = globalThis.window;

function createGenerationViewPrerequisites(container) {
  const form = new MockElement('FORM');
  form.className = 'mg-form';
  const actions = new MockElement('DIV');
  actions.className = 'mg-actions';
  form.appendChild(actions);

  const genBtn = new MockElement('BUTTON');
  genBtn.id = 'mg-gen-execute';
  genBtn.type = 'button';
  genBtn.textContent = 'Whole Page Generate';
  actions.appendChild(genBtn);

  container.appendChild(form);

  const stage = new MockElement('DIV');
  stage.id = 'mg-stage';
  container.appendChild(stage);

  const stageOverlay = new MockElement('DIV');
  stageOverlay.id = 'mg-stage-overlay';
  container.appendChild(stageOverlay);

  const stageNeutral = new MockElement('DIV');
  stageNeutral.id = 'mg-stage-neutral';
  container.appendChild(stageNeutral);
}

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
    checkpoints: [{ id: 'v1-5-pruned.safetensors', available: true }],
    samplers: ['euler'],
    schedulers: ['normal'],
    product_bounds: { max_pixels: 4194304 },
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
    positive_raw: 'manga page scene',
    negative_raw: 'blurry',
    setCatalog(c) { this.catalog = c; },
    setJob(j) {},
    ...overrides
  };

  return state;
}

// Import view & store
const { mountGenerationView } = await import('../app/src/view/generation_view.js');
const storeModule = await import('../app/src/state/authoring_store.js');
const authoringStore = storeModule.authoringStore || new storeModule.AuthoringStore();

const RESULTS = [];
function record(id, title, pass, detail = '') {
  RESULTS.push({ id, title, pass, detail });
  const mark = pass ? '[✓ PASS]' : '[✗ FAIL]';
  console.log(`${mark} ${id}: ${title} - ${detail}`);
}

async function run() {
  console.log('====================================================');
  console.log('MANGA WORKSPACE PAGE COMPOSITE HISTORY GUI VERIFICATION');
  console.log('====================================================\n');

  const originalFetch = globalThis.fetch;

  try {
    const historyRequests = [];
    const composeRequests = [];
    const currentnessRequests = [];
    const metadataRequests = [];
    const promptRequests = [];

    let currentnessStatusToReturn = 'CURRENT';
    let shouldHistoryFail = false;
    let historyErrorMessage = 'Internal server error';
    let shouldCurrentnessFail = false;
    let pendingDelayMs = 0;

    const fixtureHistoryEntries = [
      {
        composite_id: 'comp_001_digest_aaa',
        page_id: 'page_0',
        composition_plan_digest: 'digest_shared_123',
        created_at: '2026-09-25T10:00:00.000Z'
      },
      {
        composite_id: 'comp_002_digest_aaa_dup_plan',
        page_id: 'page_0',
        composition_plan_digest: 'digest_shared_123',
        created_at: '2026-09-25T10:05:00.000Z'
      },
      {
        composite_id: 'comp_003_digest_bbb',
        page_id: 'page_0',
        composition_plan_digest: 'digest_different_456',
        created_at: '2026-09-25T10:10:00.000Z'
      }
    ];

    let historyToReturn = [...fixtureHistoryEntries];

    globalThis.fetch = async (url, options = {}) => {
      const method = (options.method || 'GET').toUpperCase();
      const urlStr = String(url);

      if (pendingDelayMs > 0) {
        await new Promise(r => setTimeout(r, pendingDelayMs));
      }

      // History GET
      if (urlStr.includes('/api/manga/page-composites') && method === 'GET' && !urlStr.includes('/artifact') && !urlStr.match(/\/api\/manga\/page-composites\/[^\/?#]+$/)) {
        historyRequests.push({ method, url: urlStr });
        if (shouldHistoryFail) {
          return {
            ok: false,
            status: 500,
            json: async () => ({ ok: false, error: historyErrorMessage })
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, entries: historyToReturn })
        };
      }

      // Compose POST
      if (urlStr.includes('/api/manga/page-composites/compose') && method === 'POST') {
        const body = options.body ? JSON.parse(options.body) : {};
        composeRequests.push({ method, url: urlStr, body });
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, composite_id: 'comp_composed_new' })
        };
      }

      // Currentness POST
      if (urlStr.includes('/currentness') && method === 'POST') {
        const body = options.body ? JSON.parse(options.body) : {};
        currentnessRequests.push({ method, url: urlStr, body });
        if (shouldCurrentnessFail) {
          return {
            ok: false,
            status: 500,
            json: async () => ({ ok: false, error: 'Currentness evaluation failed' })
          };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, status: currentnessStatusToReturn, reason: 'MATCH_IN_TEST' })
        };
      }

      // Metadata GET
      if (urlStr.match(/\/api\/manga\/page-composites\/[^\/?#]+$/) && method === 'GET') {
        metadataRequests.push({ method, url: urlStr });
        return {
          ok: true,
          status: 200,
          json: async () => ({ ok: true, composite_id: 'comp_meta' })
        };
      }

      // /prompt or /queue
      if (urlStr.includes('/prompt') || urlStr.includes('/queue')) {
        promptRequests.push({ method, url: urlStr });
        return { ok: false, status: 500 };
      }

      return { ok: true, status: 200, json: async () => ({}) };
    };

    const initialDoc = {
      id: 'doc_manga_test_1',
      schema_id: 'TEGAKI_AUTHORING_DOCUMENT',
      schema_version: '1.0.0',
      pages: [
        {
          id: 'page_0',
          page_number: 1,
          width_px: 512,
          height_px: 512,
          panels: [{ id: 'panel_1', prompt: 'scene 1' }],
          scenes: [],
          visual_frames: [],
          cast: [],
          character_instances: [],
          guides: []
        },
        {
          id: 'page_1',
          page_number: 2,
          width_px: 512,
          height_px: 512,
          panels: [{ id: 'panel_2', prompt: 'scene 2' }],
          scenes: [],
          visual_frames: [],
          cast: [],
          character_instances: [],
          guides: []
        }
      ]
    };

    let currentDoc = initialDoc;
    const storeListeners = [];
    authoringStore.subscribe = (fn) => {
      storeListeners.push(fn);
      return () => {
        const idx = storeListeners.indexOf(fn);
        if (idx !== -1) storeListeners.splice(idx, 1);
      };
    };
    authoringStore.setDocument = (doc) => {
      currentDoc = doc;
      for (const fn of [...storeListeners]) fn();
    };
    authoringStore.getPage = (idx = 0) => currentDoc.pages[idx] || null;
    authoringStore.getCurrentPageIndex = () => undefined;
    authoringStore.getCurrentPageId = () => null;
    authoringStore.getCurrentPage = () => null;
    authoringStore.getDocument = () => currentDoc;
    authoringStore.setDocument(initialDoc);

    const docBefore = JSON.parse(JSON.stringify(authoringStore.getDocument()));

    const viewState = makeGenerationViewStateFixture({ currentPageIndex: 0, currentPageId: 'page_0' });
    viewState.authoringStore = authoringStore;

    const container = new MockElement('DIV');
    mockDocument.body.appendChild(container);
    createGenerationViewPrerequisites(container);
    mountGenerationView(container, { authoringStore, store: authoringStore, state: viewState });

    // Elements
    const historyBtn = container.querySelector('[data-testid="page-composite-history-btn"]');
    const compositeBtn = container.querySelector('[data-testid="page-composite-btn"]');
    const wholePageBtn = container.querySelector('#mg-gen-execute') || container.querySelector('[data-testid="generate-page-btn"]');
    const historyList = container.querySelector('[data-testid="page-composite-history-list"]');
    const historyError = container.querySelector('[data-testid="page-composite-history-error"]');
    const previewBox = container.querySelector('[data-testid="page-composite-preview"]');
    const previewImg = container.querySelector('[data-testid="page-composite-img"]');
    const statusLabel = container.querySelector('[data-testid="page-composite-status"]');

    // CASE A: History action exists
    const hasHistoryBtn = Boolean(historyBtn && (historyBtn.textContent.includes('履歴') || historyBtn.textContent.includes('合成履歴')));
    record('CASE_A', 'History action exists', hasHistoryBtn, `history button text: "${historyBtn?.textContent || ''}"`);

    // CASE B: Existing Page Composite compose button remains
    const hasCompositeBtn = Boolean(compositeBtn && compositeBtn.textContent.includes('ページ合成'));
    record('CASE_B', 'Existing Page Composite compose button remains', hasCompositeBtn, `composite button text: "${compositeBtn?.textContent || ''}"`);

    // CASE C: Existing whole-page Generate remains
    record('CASE_C', 'Existing whole-page Generate remains', Boolean(wholePageBtn), 'whole page button present');

    // CASE D & E: History click issues exactly one GET with current page 0 identity
    historyRequests.length = 0;
    await historyBtn.click();

    const historyCalledOnce = historyRequests.length === 1 && historyRequests[0].method === 'GET';
    const reqUrl = historyRequests[0]?.url || '';
    const hasDocParam = reqUrl.includes('document_id=doc_manga_test_1');
    const hasPage0Param = reqUrl.includes('page_id=page_0');

    record('CASE_D', 'History click issues exactly one GET /api/manga/page-composites', historyCalledOnce, `calls: ${historyRequests.length}, url: ${reqUrl}`);
    record('CASE_E', 'Request uses current page 0 identity', hasDocParam && hasPage0Param, `document_id present: ${hasDocParam}, page_id=page_0: ${hasPage0Param}`);

    // CASE F: Multi-page fallback uses page 1 identity when currentPageIndex=1 and getters return undefined/null
    viewState.currentPageIndex = 1;
    viewState.currentPageId = null;
    authoringStore.getCurrentPageIndex = () => undefined;
    authoringStore.getCurrentPageId = () => null;
    authoringStore.getCurrentPage = () => null;
    authoringStore.getDocument = () => initialDoc;

    historyRequests.length = 0;
    await historyBtn.click();
    const fallbackUrl = historyRequests[0]?.url || '';
    const hasPage1Fallback = fallbackUrl.includes('page_id=page_1');
    record('CASE_F', 'Multi-page fallback uses page 1 identity when currentPageIndex=1', hasPage1Fallback, `url: ${fallbackUrl}`);

    // Restore to page 0 for remaining tests
    viewState.currentPageIndex = 0;
    viewState.currentPageId = 'page_0';
    historyRequests.length = 0;
    await historyBtn.click();

    // CASE G: Multiple entries all render
    const renderedItems = historyList.querySelectorAll('[data-testid="page-composite-history-item"]');
    record('CASE_G', 'Multiple entries all render', renderedItems.length === 3, `count: ${renderedItems.length}`);

    // CASE H: Returned ordering is preserved exactly
    const idsRendered = renderedItems.map(item => item.dataset.compositeId || item.getAttribute('data-composite-id'));
    const orderPreserved = idsRendered[0] === fixtureHistoryEntries[0].composite_id &&
                           idsRendered[1] === fixtureHistoryEntries[1].composite_id &&
                           idsRendered[2] === fixtureHistoryEntries[2].composite_id;
    record('CASE_H', 'Returned ordering is preserved exactly', orderPreserved, `rendered ids: ${idsRendered.join(', ')}`);

    // CASE I: Same-plan-digest entries are not collapsed
    const sharedDigestItems = renderedItems.filter(item => (item.dataset.compositeId || '').includes('digest_aaa'));
    record('CASE_I', 'Same-plan-digest entries are not collapsed', sharedDigestItems.length === 2, `shared digest count: ${sharedDigestItems.length}`);

    // CASE J: Empty history renders non-error empty state
    historyToReturn = [];
    historyRequests.length = 0;
    await historyBtn.click();
    const emptyEl = historyList.querySelector('[data-testid="page-composite-history-empty"]');
    const emptyTextMatches = emptyEl?.textContent?.includes('履歴なし');
    const noErrorOnEmpty = historyError.style.display === 'none';
    record('CASE_J', 'Empty history renders non-error empty state', Boolean(emptyEl && emptyTextMatches && noErrorOnEmpty), `text: "${emptyEl?.textContent}", error visible: ${historyError.style.display !== 'none'}`);

    // Restore entries and reload
    historyToReturn = [...fixtureHistoryEntries];
    await historyBtn.click();
    const activeItems = historyList.querySelectorAll('[data-testid="page-composite-history-item"]');

    // CASE K & L & M: Selecting a history entry displays preview and calls currentness with CURRENT page identity
    currentnessRequests.length = 0;
    currentnessStatusToReturn = 'CURRENT';

    const itemToSelect = activeItems[0];
    await itemToSelect.click();

    const expectedArtifactUrl = `/api/manga/page-composites/${fixtureHistoryEntries[0].composite_id}/artifact`;
    const previewShown = previewBox.style.display === 'block';
    const previewSrcMatches = previewImg.src === expectedArtifactUrl;
    record('CASE_K', 'Selecting a history entry uses exact artifact URL', previewShown && previewSrcMatches, `src: ${previewImg.src}, visible: ${previewShown}`);

    const curCalledOnce = currentnessRequests.length === 1 && currentnessRequests[0].method === 'POST';
    const curTargetUrl = currentnessRequests[0]?.url || '';
    const curPayload = currentnessRequests[0]?.body || {};
    const curMatchesSelected = curTargetUrl.includes(fixtureHistoryEntries[0].composite_id);
    const curUsesCurrentPage = curPayload.page_id === 'page_0' && curPayload.page_index === 0;

    record('CASE_L', 'Selection issues exactly one currentness POST', curCalledOnce && curMatchesSelected, `calls: ${currentnessRequests.length}, url: ${curTargetUrl}`);
    record('CASE_M', 'Currentness uses CURRENT page identity', curUsesCurrentPage, `payload page_id: "${curPayload.page_id}", index: ${curPayload.page_index}`);

    // CASE N: CURRENT renders
    const statusTextN = statusLabel.textContent;
    const statusAttrN = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    record('CASE_N', 'CURRENT renders', statusTextN === 'CURRENT' && statusAttrN === 'CURRENT', `text: "${statusTextN}", data-status: "${statusAttrN}"`);

    // CASE O: STALE renders
    currentnessRequests.length = 0;
    currentnessStatusToReturn = 'STALE';
    await activeItems[1].click();
    const statusTextO = statusLabel.textContent;
    const statusAttrO = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    record('CASE_O', 'STALE renders', statusTextO === 'STALE' && statusAttrO === 'STALE', `text: "${statusTextO}", data-status: "${statusAttrO}"`);

    // CASE P: UNKNOWN renders
    currentnessRequests.length = 0;
    currentnessStatusToReturn = 'UNKNOWN';
    await activeItems[2].click();
    const statusTextP = statusLabel.textContent;
    const statusAttrP = statusLabel.dataset.status || statusLabel.getAttribute('data-status');
    record('CASE_P', 'UNKNOWN renders', statusTextP === 'UNKNOWN' && statusAttrP === 'UNKNOWN', `text: "${statusTextP}", data-status: "${statusAttrP}"`);

    // CASE Q: History GET failure bounded
    shouldHistoryFail = true;
    historyErrorMessage = 'Database timeout in D:\\GitHub\\ComfyUIPortable\\manga\\history.sqlite';
    await historyBtn.click();
    const errorVisibleQ = historyError.style.display !== 'none';
    const errorTextQ = historyError.textContent;
    const pathRedactedQ = !/([a-zA-Z]:\\[^ \t\r\n]+|\/manga\/)/i.test(errorTextQ);
    record('CASE_Q', 'History GET failure bounded without leaking paths', errorVisibleQ && pathRedactedQ, `visible: ${errorVisibleQ}, text: "${errorTextQ}"`);
    shouldHistoryFail = false;

    // Reload history cleanly
    await historyBtn.click();
    const reloadedItems = historyList.querySelectorAll('[data-testid="page-composite-history-item"]');

    // CASE R: Artifact failure bounded
    const compositeError = container.querySelector('[data-testid="page-composite-error"]');
    await previewImg.dispatchEvent({ type: 'error' });
    const artifactErrorShown = compositeError.style.display !== 'none' && compositeError.textContent.includes('could not be loaded');
    const listStillUsableR = reloadedItems.length === 3;
    record('CASE_R', 'Artifact failure bounded and list remains usable', artifactErrorShown && listStillUsableR, `error visible: ${artifactErrorShown}, items: ${reloadedItems.length}`);

    // CASE S: Currentness failure shows UNKNOWN and keeps list usable
    shouldCurrentnessFail = true;
    await reloadedItems[0].click();
    const statusDegradedS = statusLabel.textContent === 'UNKNOWN' && (statusLabel.dataset.status === 'UNKNOWN' || statusLabel.getAttribute('data-status') === 'UNKNOWN');
    const listStillUsableS = reloadedItems.length === 3;
    record('CASE_S', 'Currentness failure shows UNKNOWN and keeps list usable', statusDegradedS && listStillUsableS, `status: "${statusLabel.textContent}", items: ${reloadedItems.length}`);
    shouldCurrentnessFail = false;

    // CASE T: Pending history request prevents duplicate history submissions only
    pendingDelayMs = 80;
    const historyClickPromise = historyBtn.click();
    await new Promise(r => setTimeout(r, 20));

    const historyDisabledWhilePending = historyBtn.disabled === true;
    const compositeStillEnabled = compositeBtn.disabled === false;
    const wholePageStillEnabled = wholePageBtn.disabled === false;

    await historyClickPromise;
    const historyEnabledAfter = historyBtn.disabled === false;
    pendingDelayMs = 0;

    const duplicateControlled = historyDisabledWhilePending && compositeStillEnabled && wholePageStillEnabled && historyEnabledAfter;
    record('CASE_T', 'Pending history request prevents duplicate history submissions only', duplicateControlled, `history disabled pending: ${historyDisabledWhilePending}, compose enabled: ${compositeStillEnabled}, gen enabled: ${wholePageStillEnabled}, history enabled after: ${historyEnabledAfter}`);

    // CASE U & W: Authoring mutation ZERO and selection never persisted
    const docAfter = JSON.parse(JSON.stringify(authoringStore.getDocument()));
    let docEqual = false;
    try {
      assert.deepEqual(docBefore, docAfter);
      docEqual = true;
    } catch (_) {
      docEqual = false;
    }
    const docStr = JSON.stringify(docAfter);
    const hasLeakedHistory = docStr.includes('comp_001') || docStr.includes('digest_shared_123') || docStr.includes('/artifact');
    record('CASE_U', 'Authoring mutation ZERO', docEqual, `doc equal: ${docEqual}`);
    record('CASE_W', 'History selection is never persisted into Authoring', !hasLeakedHistory, `persisted: ${hasLeakedHistory}`);

    // CASE V: Page switch clears old-page history, selection, preview, and status
    // Switch to page 1
    viewState.currentPageIndex = 1;
    viewState.currentPageId = 'page_1';
    authoringStore.setDocument({ ...initialDoc });

    const historyClearedV = historyList.children.length === 0;
    const previewHiddenV = previewBox.style.display === 'none';
    const srcClearedV = previewImg.src === '';
    const statusClearedV = statusLabel.textContent === '' && !statusLabel.getAttribute('data-status');
    const caseVPass = historyClearedV && previewHiddenV && srcClearedV && statusClearedV;
    record('CASE_V', 'Page switch clears old-page history, selection, preview, and status', caseVPass, `history cleared: ${historyClearedV}, preview hidden: ${previewHiddenV}, src cleared: ${srcClearedV}, status cleared: ${statusClearedV}`);

    // CASE X: No metadata route call
    const zeroMetadata = metadataRequests.length === 0;
    record('CASE_X', 'No metadata route call', zeroMetadata, `metadata calls: ${metadataRequests.length}`);

    // CASE Y: No /prompt
    const zeroPrompt = promptRequests.length === 0;
    record('CASE_Y', 'No /prompt calls', zeroPrompt, `prompt calls: ${promptRequests.length}`);

    // CASE Z: No live backend / GPU
    record('CASE_Z', 'No live backend / GPU', zeroPrompt && zeroMetadata, 'zero live ComfyUI or GPU interactions');

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
    console.log('\nALL 26 CASES (A through Z) PASSED!');
    process.exit(0);
  }
}

run();
