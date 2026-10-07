# 软件工程实验一

学号：202410760241　姓名：朱邦煦

## 一、仓库内容

| 文件 | 说明 |
| --- | --- |
| `HelloWorld.py` | 编程基本功练习(1)：输出 Hello World |
| `HJ212Parser.py` | 编程基本功练习(2)：HJ 212-2017 协议报文解析类库 |
| `README.md` | 项目说明 |

## 二、HJ212Parser 使用方法

```python
from HJ212Parser import HJ212Parser

p = HJ212Parser()
msg = '##0101QN=20160801085857223;ST=32;CN=1062;PW=100000;MN=010000A8900016F000169DC0;Flag=5;CP=&&RtdInterval=30&&1C80\r\n'

p.is_valid_message(msg)         # 报文格式是否合法
p.validate_crc(msg)             # ANSI CRC16 校验是否通过
p.parse_data_segment(msg)       # 数据段结构化 -> dict
p.extract_monitoring_data(msg)  # 提取监测因子实时值 -> {因子编码: float}
```

直接运行 `python HJ212Parser.py` 即可看到自测结果（内置官方附录 A 黄金向量）。

## 三、Git 提交注释规范示例

```
feat: 新增 HJ212Parser 类库，支持报文校验与监测因子提取
test: 用官方附录A报文验证 CRC16=1C80 通过
docs: 补充 README 使用说明
chore: 初始化 HelloWorld
```
