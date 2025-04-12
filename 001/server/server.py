import asyncio
import datetime  # 确保导入完整的datetime
import logging
import ssl

from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.asyncio.server import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived

logger = logging.getLogger("quic_server")


# 处理从客户端接收的流数据
class QuicServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.streams = {}

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, StreamDataReceived):
            # 当收到流数据时
            data = event.data.decode()
            stream_id = event.stream_id
            logger.info(f"接收到来自流 {stream_id} 的数据: {data}")

            # 发送响应
            response = f"服务器收到消息: {data}".encode()
            self._quic.send_stream_data(stream_id, response)
            logger.info(f"发送响应到流 {stream_id}: {response.decode()}")

        # 处理其他事件
        super().quic_event_received(event)


async def handle_stream(reader, writer):
    pass  # 不需要实现，使用QuicServerProtocol处理


async def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.INFO,
    )

    # 创建SSL上下文
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # 为了测试，我们生成自签名证书
    # 在实际应用中，应该使用正式的TLS证书

    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # 创建自签名证书
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "QUIC Demo"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=10)
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # 保存证书和私钥到文件
    cert_path = "server_cert.pem"
    key_path = "server_key.pem"

    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # 加载证书和私钥
    ssl_context.load_cert_chain(cert_path, key_path)

    # 配置QUIC
    configuration = QuicConfiguration(
        alpn_protocols=["http/1.1"],
        is_client=False,
        max_datagram_frame_size=65536,
    )
    configuration.load_cert_chain(cert_path, key_path)

    # 启动服务器
    server = await serve(
        host="0.0.0.0",
        port=4433,
        configuration=configuration,
        create_protocol=QuicServerProtocol,
    )

    logger.info("服务器启动，监听在 0.0.0.0:4433")

    # 保持服务器运行
    try:
        await asyncio.Future()
    finally:
        server.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
