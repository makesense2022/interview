# 🛡️ 反限流解决方案

当你的IP被限流时，可以使用以下几种方法：

## 📋 已实现的功能

### 1. **用户代理轮换** ✅
- 自动轮换5个不同的浏览器UA
- 每次请求使用不同的UA，模拟不同用户

### 2. **随机延迟** ✅
- 页面访问前：随机延迟 1-3 秒
- 页面加载后：随机等待 1.5-3 秒
- 模拟真实用户浏览行为

### 3. **真实HTTP头** ✅
- Accept、Accept-Language、Accept-Encoding
- DNT、Connection、Upgrade-Insecure-Requests
- 完全模拟真实浏览器请求

### 4. **反自动化检测** ✅
- 禁用 AutomationControlled 特征
- 添加多个反检测参数

## 🚀 立即可用的方法

### 方法1：增加延迟（最简单）
```bash
# 将延迟增加到5秒
python3 crawl_with_clicks.py [URL] --delay 5

# 减少并发数
python3 crawl_with_clicks.py [URL] --concurrent 2 --delay 5
```

### 方法2：分批爬取
```bash
# 只爬取2页，等待一段时间后再继续
python3 crawl_with_clicks.py [URL] --max-pages 2

# 等待30分钟-1小时后
python3 crawl_with_clicks.py [URL] --max-pages 2
```

### 方法3：使用代理（需要额外配置）

#### 免费代理方案
1. **使用免费代理池**
   ```bash
   # 安装代理工具
   pip3 install requests
   
   # 从免费代理网站获取代理
   # https://www.kuaidaili.com/free/
   # https://www.89ip.cn/
   ```

2. **配置代理**
   修改 `crawl_with_clicks.py` 中的浏览器启动参数：
   ```python
   browser = await p.chromium.launch(
       headless=True,
       proxy={
           'server': 'http://proxy-ip:port',
           # 如果需要认证
           # 'username': 'user',
           # 'password': 'pass'
       }
   )
   ```

#### 付费代理方案（推荐）
1. **购买代理服务**
   - 阿布云代理：https://www.abuyun.com/
   - 快代理：https://www.kuaidaili.com/
   - 芝麻代理：http://www.zhimaruanjian.com/

2. **使用方法**
   ```python
   # 在浏览器启动时配置
   proxy = {
       'server': 'http://proxy.abuyun.com:9020',
       'username': 'your_username',
       'password': 'your_password'
   }
   ```

### 方法4：使用VPN（最有效）
```bash
# 1. 连接VPN更换IP
# 2. 运行爬虫
python3 crawl_with_clicks.py [URL]

# 3. 如果再次被限流，断开VPN，换另一个节点
```

### 方法5：等待冷却
```bash
# 停止爬取，等待 1-24 小时
# 大多数网站的限流会在几小时后自动解除
```

## 🎯 推荐策略组合

### 轻度限流
```bash
python3 crawl_with_clicks.py [URL] \
  --delay 5 \          # 增加延迟到5秒
  --concurrent 2 \     # 降低并发到2
  --max-pages 3        # 每次只爬3页
```

### 中度限流
```bash
# 1. 等待1小时
# 2. 使用VPN更换IP
# 3. 运行：
python3 crawl_with_clicks.py [URL] \
  --delay 10 \         # 延迟10秒
  --concurrent 1 \     # 串行处理
  --max-pages 2
```

### 重度限流
```bash
# 1. 购买代理服务
# 2. 配置代理到代码中
# 3. 使用最保守的参数：
python3 crawl_with_clicks.py [URL] \
  --delay 15 \
  --concurrent 1 \
  --max-pages 1
```

## 📊 检测是否被限流

### 常见限流表现
- ❌ 找到 0 个可点击的图片链接
- ❌ HTTP 403 Forbidden
- ❌ HTTP 429 Too Many Requests
- ❌ 页面加载超时
- ❌ 返回验证码页面

### 日志示例
```
找到 0 个可点击的图片链接  ← 被限流
发现缩略图数: 0
找到大图数: 0
```

## 💡 预防限流的最佳实践

1. **合理的延迟**：`--delay 3` 或更高
2. **低并发**：`--concurrent 3` 或更低
3. **分批爬取**：每次只爬几页，分多次完成
4. **避开高峰期**：凌晨或清晨爬取
5. **使用代理**：轮换IP地址
6. **模拟真实行为**：已自动实现随机延迟

## 🔧 当前已优化的参数

脚本已自动包含以下优化：
- ✅ 5个不同的User-Agent轮换
- ✅ 随机延迟（1-3秒）
- ✅ 真实的HTTP请求头
- ✅ 反自动化检测
- ✅ 随机等待时间

## 📞 紧急恢复方案

如果完全无法访问：
```bash
# 1. 立即停止所有爬虫
Ctrl+C

# 2. 等待至少1小时

# 3. 更换网络（切换到手机热点）

# 4. 使用最保守的参数重试
python3 crawl_with_clicks.py [URL] \
  --delay 20 \
  --concurrent 1 \
  --max-pages 1
```

## 🎓 长期解决方案

1. **建立代理池**：准备10+个代理IP轮换使用
2. **分布式爬取**：使用多台机器从不同IP爬取
3. **遵守robots.txt**：尊重网站的爬虫规则
4. **控制频率**：每天只爬取有限的数据量
