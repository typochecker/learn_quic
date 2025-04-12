import asyncio
import logging
import ssl
from typing import Dict

from aioquic.asyncio.client import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived

logger = logging.getLogger("quic_client")


class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ack_waiter: Dict[int, asyncio.Future[None]] = {}

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, StreamDataReceived):
            # 当收到流数据时
            stream_id = event.stream_id
            data = event.data.decode()
            logger.info(f"服务器响应 (流 {stream_id}): {data}")

            # 如果有等待此流响应的waiter，通知它
            waiter = self._ack_waiter.pop(stream_id, None)
            if waiter:
                waiter.set_result(data)

        # 处理其他事件
        super().quic_event_received(event)

    async def send_message(self, message: str) -> str:
        """
        向服务器发送消息并等待响应
        """
        # 创建新的流
        stream_id = self._quic.get_next_available_stream_id()

        # 设置等待响应的future
        waiter = self._loop.create_future()
        self._ack_waiter[stream_id] = waiter

        logger.info(f"发送消息 (流 {stream_id}): {message}")

        # 发送数据
        self._quic.send_stream_data(stream_id, message.encode())

        # 等待响应
        try:
            return await asyncio.wait_for(waiter, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"等待流 {stream_id} 响应超时")
            self._ack_waiter.pop(stream_id, None)
            return "超时，没有收到响应"


async def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.INFO,
    )

    # 配置SSL上下文
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # 在实际应用中，应启用证书验证

    # 配置QUIC
    configuration = QuicConfiguration(
        alpn_protocols=["http/1.1"],
        is_client=True,
        verify_mode=ssl.CERT_NONE,  # 在实际应用中，应启用证书验证
    )

    # 连接到服务器
    logger.info("连接到服务器...")
    async with connect(
        "127.0.0.1",
        4433,
        configuration=configuration,
        create_protocol=QuicClientProtocol,
        # ssl=ssl_context,
    ) as client:
        client = cast(QuicClientProtocol, client)

        # 发送几条消息并获取响应
        messages = ["你好，QUIC服务器！", "这是第二条测试消息", "测试完成，再见！"]

        for i, message in enumerate(messages):
            response = await client.send_message(message)
            logger.info(f"消息 {i + 1} 响应: {response}")
            await asyncio.sleep(1)  # 稍等片刻再发送下一条消息

        logger.info("客户端测试完成")


def cast(type_, obj):
    """简单的类型转换函数"""
    return obj


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("客户端已停止")
