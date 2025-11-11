// Minimal reactivity implementation to illustrate ReactiveEffect / track / trigger
// Usage: node vue/source-reading/reactivity-mini.js

let activeEffect = null;
const targetMap = new WeakMap(); // WeakMap<Target, Map<Key, Set<Effect>>>
// Simple microtask-based scheduler for flushing jobs
const jobQueue = new Set();
let isFlushing = false;
const resolved = Promise.resolve();
function queueJob(job) {
  jobQueue.add(job);
  if (!isFlushing) {
    isFlushing = true;
    resolved.then(() => {
      try {
        jobQueue.forEach(j => j());
      } finally {
        isFlushing = false;
        jobQueue.clear();
      }
    });
  }
}

class ReactiveEffect {
  constructor(fn, scheduler) {
    this.fn = fn;
    this.scheduler = scheduler;
    this.deps = []; // Dep sets that track this effect
  }
  run() {
    const parent = activeEffect;
    try {
      activeEffect = this;
      return this.fn();
    } finally {
      activeEffect = parent;
    }
  }
}

function track(target, key) {
  console.log('track ====')
  if (!activeEffect) return;
  let depsMap = targetMap.get(target);
  if (!depsMap) targetMap.set(target, (depsMap = new Map()));
  let dep = depsMap.get(key);
  if (!dep) depsMap.set(key, (dep = new Set()));
  if (!dep.has(activeEffect)) {
    dep.add(activeEffect);
    activeEffect.deps.push(dep);
    // debug
    console.log('[track]', key, 'dep size =', dep.size);
  }
}

function trigger(target, key) {
  const depsMap = targetMap.get(target);
  if (!depsMap) return;
  const dep = depsMap.get(key);
  if (!dep) return;
  // Snapshot to avoid effects modifying the set while iterating
  [...dep].forEach(effect => {
    if (effect.scheduler) effect.scheduler();
    else effect.run();
  });
}

function reactive(obj) {
  return new Proxy(obj, {
    get(t, k, r) {
      const res = Reflect.get(t, k, r);
      track(t, k);
      return typeof res === 'object' && res !== null ? reactive(res) : res;
    },
    set(t, k, v, r) {
      const old = t[k];
      const ok = Reflect.set(t, k, v, r);
      if (old !== v) trigger(t, k);
      return ok;
    },
  });
}

function ref(value) {
  const dep = new Set();
  const wrapper = {
    get value() {
      if (activeEffect) {
        if (!dep.has(activeEffect)) dep.add(activeEffect), activeEffect.deps.push(dep);
      }
      return value;
    },
    set value(v) {
      if (v !== value) {
        value = v;
        [...dep].forEach(e => (e.scheduler ? e.scheduler() : e.run()));
      }
    },
  };
  // Auto-wrap objects as reactive for parity with Vue
  if (typeof value === 'object' && value !== null) value = reactive(value);
  return wrapper;
}

function effect(fn, scheduler) {
  const e = new ReactiveEffect(fn, scheduler);
  e.run();
  // Return a runner like Vue does
  const runner = e.run.bind(e);
  runner.effect = e;
  return runner;
}

function computed(getter) {
  let dirty = true;
  let cache;
  const runner = new ReactiveEffect(() => getter(), () => {
    dirty = true;
    // notify external readers by triggering on our ref-like object
    trigger(wrapper, 'value');
  });
  const wrapper = {
    get value() {
      if (dirty) {
        cache = runner.run();
        dirty = false;
      }
      track(wrapper, 'value');
      return cache;
    },
  };
  return wrapper;
}

// Deep traverse utility to collect dependencies for reactive objects
function traverse(value, seen = new Set()) {
  if (typeof value !== 'object' || value === null || seen.has(value)) return value;
  seen.add(value);
  for (const k in value) traverse(value[k], seen);
  return value;
}

// Basic watch implementation: supports function/ref/reactive as source
// options: { immediate=false, flush='pre'|'post'|'sync' }
function watch(source, cb, options = {}) {
  const { immediate = false, flush = 'pre' } = options;

  let getter;
  if (typeof source === 'function') getter = source;
  else if (source && typeof source === 'object' && 'value' in source) getter = () => source.value;
  else getter = () => traverse(source);

  let oldValue;
  let cleanup;
  let stopped = false;
  const onCleanup = (fn) => (cleanup = fn);

  const job = () => {
    if (stopped) return;
    const newValue = runner.run();
    if (cleanup) { try { cleanup(); } catch {} finally { cleanup = undefined; } }
    cb(newValue, oldValue, onCleanup);
    oldValue = newValue;
  };

  const scheduler = () => {
    if (flush === 'sync') job();
    else queueJob(job);
  };

  const runner = new ReactiveEffect(getter, scheduler);

  if (immediate) job();
  else oldValue = runner.run();

  return () => { stopped = true; if (cleanup) cleanup(); };
}

// watchEffect: runs the effect immediately and re-runs when its deps change
function watchEffect(effectFn, options = {}) {
  const { flush = 'pre' } = options;
  let cleanup;
  const onCleanup = (fn) => (cleanup = fn);

  const job = () => {
    if (cleanup) { try { cleanup(); } catch {} finally { cleanup = undefined; } }
    runner.run();
  };

  const runner = new ReactiveEffect(() => {
    effectFn(onCleanup);
  }, () => {
    if (flush === 'sync') job();
    else queueJob(job);
  });

  // immediate run
  job();
  return () => { if (cleanup) cleanup(); };
}

// Demo to map concepts
function runDemo() {
  const state = reactive({ count: 0 });
  const double = computed(() => state.count * 2);

  effect(() => {
    // This creates a ReactiveEffect; reading state.count tracks dependency
    console.log('render -> count =', state.count);
  });
  console.log('runDemo', '====')
//   // Mutations will trigger the tracked effect
  state.count++;
//   state.count++;
}

if (require.main === module) {
  runDemo();
}

module.exports = { reactive, ref, effect, computed, watch, watchEffect, ReactiveEffect, track, trigger, runDemo };
