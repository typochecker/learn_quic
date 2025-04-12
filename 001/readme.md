# QUIC 通信演示项目

本项目演示了如何使用 Python 和 aioquic 库实现一个基本的 QUIC 服务器和客户端，并进行通信。

## 项目目录结构

```
001/
├── server/
│   ├── server.py  # QUIC 服务器实现
│   └── __init__.py
├── client/
│   ├── client.py  # QUIC 客户端实现
│   └── __init__.py
├── requirements.txt  # 项目依赖
└── readme.md  # 项目说明
```

## 功能特点

- 服务器端：接收客户端连接，处理流数据，并发送响应
- 客户端：连接到服务器，发送消息，并处理服务器响应
- 使用自签名证书实现 TLS 加密
- 基于 QUIC 协议的可靠数据传输

## 使用说明

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务器：

   ```bash
   python server/server.py
   ```

3. 启动客户端：
   ```bash
   python client/client.py
   ```

## 注意事项

- 服务器会自动生成自签名证书用于 TLS 加密
- 客户端默认忽略证书验证（仅用于演示目的）
- 默认服务器监听在 0.0.0.0:4433
- 客户端默认连接到 127.0.0.1:4433

## 依赖

- Python 3.7+
- aioquic
- cryptography
- asyncio
- certifi

## 实现原理

1. 服务器通过 aioquic 库监听 UDP 端口
2. 客户端通过 QUIC 协议连接到服务器
3. 建立连接后，客户端发送消息到服务器
4. 服务器处理收到的消息并返回响应
5. 客户端接收并处理服务器的响应

这个简单的演示展示了 QUIC 协议的基本使用，包括连接建立、流控制和数据传输。
