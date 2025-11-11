# 前端架构设计·详解版（题 21–30）

模块联邦（MF）架构：shared/singleton/strictVersion 的取舍？远程失效的回退与用户可感知降级如何设计？
Monorepo：pnpm workspaces + TS Project References 如何落地？CI 如何基于受影响图做增量构建与变更集发布？
构建与产物切分：manualChunks、路由级分包、contenthash 长缓存策略；如何避免分包抖动？
性能预算与监控：为 LCP/CLS/INP 设预算与报警门槛；前端可观测如何做采样、指纹、归并与脱敏？
安全架构：CSP/Trusted Types/SRI 的落地路径；CSRF 与同站策略；如何做供应链安全与依赖审计？
i18n 与可访问性：词库拆分与懒加载；Intl 的复数/时区/本地化；关键 a11y 检查清单？
资源与图片：响应式图片 srcset/sizes、WebP/AVIF、LQIP/Blurhash，占位与延迟加载策略如何选？
API 层架构：REST/GraphQL/tRPC 的契约、演进与缓存（SWR/stale-while-revalidate）；如何做请求去重/超时/中断？
离线与可靠性：Service Worker 缓存策略（缓存优先/网络优先/预缓存）、后台同步、乐观更新与回滚？
微前端路由与集成：跨应用路由同步与会话关联、样式与运行时隔离、统一监控上报与配额管理？

---

## 21) 模块联邦（MF）架构：共享依赖、路由集成与降级

- TL;DR：主应用运行时加载远程模块，shared 共享运行时单例，需解决版本冲突、失败回退与隔离。

- 心智模型：
  - Host（壳）+ Remotes（子应用/业务模块）；通过 remoteEntry 揭示暴露模块表。
  - shared：如 react/react-dom 单例，声明 requiredVersion、strictVersion、fallback。

- 代码片段：
  ```js
  // Host webpack.config.js
  new ModuleFederationPlugin({
    remotes: { user: 'userApp@https://cdn.example.com/user/remoteEntry.js' },
    shared: { react: { singleton: true, requiredVersion: '^18' }, 'react-dom': { singleton: true } }
  })
  ```

- 场景：灰度装载新业务、跨团队独立发布、A/B 实验。

- 边界与建议：
  - 失败回退：远程加载失败时提供占位/降级；监控埋点。
  - 样式隔离：CSS Modules/Shadow DOM；运行时隔离可选 iframe。
  - 统一路由与鉴权：壳应用掌控路由与权限，远程仅提供页面工厂。

---

## 22) Monorepo 设计

- TL;DR：pnpm workspaces + TS Project References + Turborepo/Nx 的缓存流水线，提升复用与构建效率。

- 心智模型：
  - packages/** 各包独立版本；apps/** 应用依赖包。
  - 受影响图决定增量构建与测试。

- 代码片段：
  ```json
  // pnpm-workspace.yaml
  packages:
    - 'packages/*'
    - 'apps/*'
  ```

- 建议：严格 peerDependencies、changesets 发布、CI 并行缓存。

---

## 23) 构建与产物切分

- TL;DR：手动分包（manualChunks）、路由级拆分、contenthash 长缓存；预取/预加载改善感知速度。

- 片段（Rollup/Vite）：
  ```js
  export default {
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react','react-dom']
          }
        }
      }
    }
  }
  ```

- 建议：稳定分包命名、防止碎片化；CDN 缓存策略与 HTTP/2/3 复用。

---

## 24) 性能预算与监控

- TL;DR：定义路由级预算（JS/CSS/图片体积、LCP/INP/CLS），上线后以 RUM 上报监控并预警。

- 片段：
  ```js
  // web-vitals
  import { onLCP, onINP, onCLS } from 'web-vitals'
  onLCP(console.log); onINP(console.log); onCLS(console.log)
  ```

- 建议：Source map 上传（Sentry）、错误指纹、采样与去抖；慢接口 SLO 与报警。

---

## 25) 安全架构

- TL;DR：CSP + Trusted Types 抗 XSS；SRI 校验第三方；CSRF 通过 SameSite/双重提交防护。

- 片段：
  ```http
  Content-Security-Policy: script-src 'self' 'nonce-<rand>'; object-src 'none'; base-uri 'self'
  ```

- 建议：依赖审计（osv、npm audit）、锁定依赖版本、最小权限策略。

---

## 26) i18n 与可访问性

- TL;DR：词库拆分懒加载；Intl 处理日期/复数/地域；a11y 从语义标签、可聚焦顺序、对比度做起。

- 片段：
  ```js
  new Intl.PluralRules('zh').select(3) // 'other'
  ```

- 建议：路由前缀化、语言协商、读屏测试。

---

## 27) 资源与图片策略

- TL;DR：响应式图片（srcset/sizes）、现代格式 WebP/AVIF、渐进加载（LQIP/Blurhash）。

- 片段：
  ```html
  <img src="/img/600.jpg" srcset="/img/600.jpg 600w, /img/1200.jpg 1200w" sizes="(max-width:600px) 600px, 1200px" />
  ```

---

## 28) API 层架构

- TL;DR：BFF 聚合、契约优先，SWR/stale-while-revalidate 缓存；可靠性：重试/退避/去重/超时/中断。

- 片段：
  ```ts
  const ctrl = new AbortController()
  const p = fetch('/api', { signal: ctrl.signal })
  setTimeout(()=>ctrl.abort(), 800)
  ```

---

## 29) 离线与可靠性

- TL;DR：Service Worker 策略（缓存优先/网络优先/预缓存）、后台同步、乐观更新 + 回滚。

- 片段：
  ```js
  self.addEventListener('fetch', e => {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)))
  })
  ```

---

## 30) 微前端路由与集成

- TL;DR：主应用统一路由/鉴权/监控；子应用暴露页面工厂；共享依赖与样式隔离并存。

- 建议：跨应用会话与埋点统一、失败回退与占位、性能配额管理。
