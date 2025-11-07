1、
typeof 只能判断基本类型，
Object.prototype.toString 能判断所有类型
====
2、
== 判断会出现隐式转换， 会先转换为数字 
对象转换会先调用 valueOf 再调用 toString

====
3、
NaN 不等于任何值

====
4、
不懂概念

====
5、
我知道箭头函数绑定的是当前作用域上一层的this
其他是 谁调用 this 就指向谁，比如 new
否则则是全局的 this

====
6、
闭包本质是允许外部函数访问内部的函数变量，函数变量不会销毁。
常见的比如 setTimeout

====
7、
先查找自身的 原型，Class.prototype，再查找 Class.prototype.__proto__ ，直到最终是 null

in 可以找到原型链上的属性， 
hasOwnProperty 只能找到自身的属性

====
8、
```
function Person(name) {
    let a = {}
    a.name = name
    return a
}

=====
9、
static 是挂在 Class 上的属性
实力方法是在 原型上的
私有字段则是挂在 new 的对象上，自有的属性。

====
10、先执行正常代码，在这个过程，微任务会被压入到 堆栈中，然后是 宏任务。 然后再执行微任务，再执行宏任务。如果一个宏任务里面 有一个 或者多个微任务，则压入到 堆栈，然后执行这些微任务，之后再执行宏任务。 
setTimout 和 setInterval 都是宏任务

不过我有个疑问就是，如果正在执行宏任务，并且有多个宏任务。第一个宏任务里面有微任务，那么第一个宏任务执行结束，是否就开始执行微任务，还是所有宏任务都执行完，在执行微任务？

=====
11、
race 是一个返回就返回
all 必须全部返回，一个报错就全部报错
allSettled 必须全部返回，但是能感知到哪个成功，哪个失败。
any 我还不清楚。

====
12、本质是 promise的语法糖。 并发执行的话，最坏放在 promise.all 或者 allSettle里面。
await 处理错误的话，需要加try catch.

=======
13、
ES6 是静态编译的。 CommonJS 是动态编译的。
ES6 可以做tree-shaking， 因为是静态编译。
ES6 引用的模块，如果被修改，其他引用的也会用修改后的，
但是 CommonJS 像是一个深copy。
ES6 支持默认导出

=====
14、
import 是可以动态加载的，运行时再加载，懒加载会用到。
底层原理有点像，动态的拼接一个 <script> 脚本标签。

====
15、
function Curr(fn) {
    return (...args) => {
        return fn(...args)
    }
}

偏函数 我不太了解。可以说明并记录到文档中

====
16、
防抖常用在输入的场景
节流用在 鼠标滚轮滑动，或者鼠标指针滑动的场景。
具体的意思是，防抖是期望，短时间内，只响应一次
而节流是 每隔一段时间只响应一次。

边界和场景坑我不太了解

=====
17、浅copy 只 copy 第一层
而深copy 是会遍历 copy 整个对象。

Symbol 和不可枚举的属性，我理解则需要判断后再 new 一个出来

循环引用我理解是一个常见的问题。 可能会导致内存泄漏？ 
如何防止循环引用？还有互相引用导致内存泄漏

const a = {
    b: {
        c:1
    }
}

a.b = a
这个是循环引用么？ 为什么有这样的场景？


=====
18、
Object.defineProperty 无法去监听 数组和对象新增的元素或者属性。 数组的一些增删改查都监控不到。
而 proxy 可以做到

====
19. 同步
window.onError
异步用 unhandleRejection 的钩子。


=====
20、
souce map 和 错误上报相结合。常见方案如何sentry

======
21、
一会我在js 文件上写


====
22
一会我在js 文件上写

====
23.

function com(...args) {
    let arr = [...args]
    return function (arg) {
        arr.reduce((pre, cur) => {
            return cur(pre)
        }, arg)
    }
}

====
24. 
一会我在js 文件上写

===
25.
一会我在js 文件上写




