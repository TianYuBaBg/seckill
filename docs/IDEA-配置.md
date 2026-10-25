# IDEA 报「不支持发行版本 5 / 8」怎么办

> 现象：在 IDEA 里点 Run / Build，报 `java: 错误: 不支持发行版本 5`。
> 真相：**不是代码问题**。项目用 Maven 编译是绿的（看 `ci` 徽章），是 IDEA 自己的编译级别被设成了 5。
> JDK 9 以后就删掉了对 Java 5 的支持，所以报这个错。

## 先做 30 秒判定

在 PowerShell（不是 IDEA 的控制台）里：

```powershell
cd D:\me\seckill
mvn -q -DskipTests compile
```

- **没有输出** → 项目没问题，纯 IDEA 配置问题，往下走
- **有报错** → 把报错发我，那是另一回事

## 修复（4 处）

| 位置 | 怎么进 | 改成 |
|---|---|---|
| Project SDK / 语言级别 | `Ctrl+Alt+Shift+S` → **Project** | SDK = **17**；Language level = **17** |
| 模块语言级别 | 同窗口 → **Modules** → seckill → Sources | Language level = **17** |
| 编译器目标字节码 | `Ctrl+Alt+S` → Compiler → Java Compiler | Project bytecode version = **17**；模块 target = **17** |
| 重新加载 Maven | 右侧 Maven 面板 → 🔄 Reload All Maven Projects | 让 IDEA 读到 pom 里的 17 |

> 注意：Project 级和 Modules 级的语言级别是**两个独立设置**，只改一个不生效。

## 一劳永逸（推荐）

`Ctrl+Alt+S` → `Build Tools` → `Maven` → **Runner**：

- **JRE** 选 **17**
- 勾上 ✅ **Delegate IDE build/run actions to Maven**

勾上后 IDEA 不再用自己的 javac 配置，编译/运行全部交给 Maven，也就是用 `pom.xml` 里的 17——
这类「IDEA 说 Java 5 / Java 8 不支持」的问题从此不会再出现。

## 还不行就按顺序试

1. `Build → Rebuild Project`
2. `File → Invalidate Caches / Restart` → 勾 `Clear file system cache` → 重启
3. 贴给我：`java -version` 的输出 + `Project Structure → Project` 的截图
   （机器上装了多个 JDK 时，IDEA 很可能选到 JDK 8 或更老的）

## 为什么 pom.xml 里要写 release 17

```xml
<maven.compiler.source>17</maven.compiler.source>
<maven.compiler.target>17</maven.compiler.target>
<maven.compiler.release>17</maven.compiler.release>
```

Spring Boot 父 pom 会把 `<java.version>` 映射成编译参数，但有些 IDE 在导入失败时会**回退到 Maven 插件的默认值 5**。
显式写死这三行之后，任何走 Maven 的编译都不会再掉到 5。
