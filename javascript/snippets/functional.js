/*
  Functional utils: curry, curryWithPlaceholder, partial, pipe, compose
  Run: node javascript/snippets/functional.js
*/

// ========== 15. Currying ==========
function curry(fn, arity = fn.length) {
  function curried(...args) {
    if (args.length >= arity) {
      return fn.apply(this, args);
    }
    return function (...rest) {
      return curried.apply(this, args.concat(rest));
    };
  }
  return curried;
}

// Placeholder version
const _ = Symbol('curry_placeholder');
function curryWithPlaceholder(fn, arity = fn.length) {
  function mergeArgs(args, rest) {
    const merged = [];
    let restIdx = 0;
    for (const a of args) {
      if (a === _ && restIdx < rest.length) merged.push(rest[restIdx++]);
      else merged.push(a);
    }
    while (restIdx < rest.length) merged.push(rest[restIdx++]);
    return merged;
  }

  function curried(...args) {
    const filled = args.filter(a => a !== _).length;
    if (filled >= arity) {
      return fn.apply(this, args);
    }
    return function (...rest) {
      const next = mergeArgs(args, rest);
      const nextFilled = next.filter(a => a !== _).length;
      if (nextFilled >= arity) return fn.apply(this, next);
      return curried.apply(this, next);
    };
  }
  return curried;
}

// ========== 15. Partial ==========
const P = Symbol('partial_placeholder');
function partial(fn, ...preset) {
  return function (...later) {
    const args = [];
    let idx = 0;
    for (const p of preset) {
      if (p === P) args.push(later[idx++]);
      else args.push(p);
    }
    while (idx < later.length) args.push(later[idx++]);
    return fn.apply(this, args);
  };
}

// ========== 23. pipe / compose ==========
function pipe(...fns) {
  if (fns.some(fn => typeof fn !== 'function')) {
    throw new TypeError('pipe 仅接受函数');
  }
  return function (input) {
    return fns.reduce((acc, fn) => Promise.resolve(acc).then(val => fn.call(this, val)), input);
  };
}

function compose(...fns) {
  return pipe(...fns.reverse());
}

// ========== Minimal tests ==========
(function tests() {
  console.log('--- curry ---');
  function sum(a, b, c) { return a + b + c; }
  const curriedSum = curry(sum);
  console.log(curriedSum(1)(2)(3)); // 6
  console.log(curriedSum(1, 2)(3)); // 6
  console.log(curriedSum(1)(2, 3)); // 6

  console.log('--- curryWithPlaceholder ---');
  function f(a, b, c) { return `${a}-${b}-${c}`; }
  const g = curryWithPlaceholder(f);
  console.log(g(_, 2)(1, 3)); // 1-2-3

  console.log('--- partial ---');
  function add(a, b, c) { return a + b + c; }
  const add1 = partial(add, 1, P, 3);
  console.log(add1(2)); // 6

  console.log('--- pipe/compose (mixed sync/async) ---');
  const double = x => x * 2;
  const plus1 = x => x + 1;
  const asyncSquare = async x => x * x;

  const p1 = pipe(double, plus1, asyncSquare);
  p1(3).then(v => console.log('pipe:', v)); // 49

  const c1 = compose(asyncSquare, plus1, double);
  c1(3).then(v => console.log('compose:', v)); // 49
})();
