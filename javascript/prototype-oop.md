# 原型与面向对象（≤6 分复习）

- 【7】原型链与属性查找
  - 先查自身；再沿 [[Prototype]]（__proto__）到 Object.prototype；终点 null
  - in 会查原型链；hasOwnProperty 仅自有属性

- 【8】手写 new 的步骤
  - obj = Object.create(Ctor.prototype)
  - ret = Ctor.apply(obj, args)
  - 返回 ret（若为对象）否则返回 obj

- 【9】class 与原型映射
  - 实例方法在 Class.prototype；static 在构造函数上（可被子类继承）
  - 私有字段 #x 存储于私有槽，非可枚举普通属性，无法通过键访问
