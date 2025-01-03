# 零知识证明匿名投票系统

进阶密码学期末展示——基于零知识证明的匿名投票系统，使用Python实现。系统确保投票的匿名性和不可篡改性，同时保证每个注册选民只能投票一次。

## 功能

- 基于零知识证明的投票者身份验证
- 匿名投票提交
- 防止双重投票
- 定时计票统计
- Web界面支持

## 安装要求

```bash
pip install -r requirements.txt
```

## 使用说明

1. 启动服务器：
```bash
python app.py
```

2. 访问 http://localhost:5000 进入投票系统

3. 注册成为投票者

4. 使用系统生成的凭证进行投票

## 系统架构

- `app.py`: 主应用程序入口
- `voting/`: 核心投票逻辑
  - `zk_proof.py`: 零知识证明实现
  - `voter.py`: 投票者管理
  - `ballot.py`: 选票处理
- `templates/`: Web界面模板
- `static/`: 静态资源文件



