# Deer Flow

进行了如下修改

1. 自定义智能体可以被其他智能体作为子智能体引用，在 config.yml 中新增 subagents 字段
2. 自定义智能体可以定义独立的工具，定义在 tools/ 目录中
3. 自定义智能体可以设置独立的skills

自定义智能体目录如下：

```
system-design-agent
  config.yml
    name:
    description:

    subagents:
    - thrustor-design-agent
    - tank-design-agent
    - valve-design-agent

  tools.py

  skills/
    custom1-skill/
    custom1-skill/
```