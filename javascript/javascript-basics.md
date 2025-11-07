# 基础与类型（≤6 分复习）

- 【1】typeof vs Object.prototype.toString
  - typeof: number/string/boolean/undefined/symbol/bigint/function/object；注意 typeof null === 'object'
  - toString.call(x): [object Array/Date/RegExp/Map/Set/Null/Undefined/Arguments]
  - BigInt/Symbol 判断：typeof 直接返回 'bigint'/'symbol'

- 【2】== 抽象相等
  - 不等价于“一律转数字”
  - 规则要点：
    - null 仅与 undefined 相等
    - '0' == false → true（ToNumber）
    - [] == ![] → true（[] → '' → 0；![] → false → 0）
    - 对象到原始值：ToPrimitive（通常先 valueOf 再 toString），Date 特例

- 【3】NaN 判等与判断
  - NaN !== NaN（IEEE 754）
  - 判断：Number.isNaN(x) 或 Object.is(NaN, NaN)
  - isNaN(…) 会先做强制转换，谨慎使用
