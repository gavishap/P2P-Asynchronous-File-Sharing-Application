from enum import Enum, auto
import logging
import asyncio
import struct
import msgpack

logger = logging.getLogger(__name__)

#message
class MessageType(Enum):
    REQUEST_REGISTERY = auto()
    REQUEST_TO_PUBLISH = auto()
    REQUEST_FILES_LIST = auto()
    REQUEST_FILE_LOCATION = auto()
    REQUEST_CHUNKS_REGISTER = auto()
    REPLY_REGISTERY = auto()
    REPLY_FILES_LIST = auto()
    REPLY_PUBLISH = auto()
    REPLY_FILES_LOCATION = auto()
    PEER_REQUESTS_CHUNK = auto()
    PEER_REP_CHUNK = auto()
    PEER_PING_PONG = auto()


def _message_log(message):
    log_message = {key: message[key] for key in message if key != 'data'}
    log_message['type'] = MessageType(message['type']).name
    return log_message


async def read_message(reader):
    assert isinstance(reader, asyncio.StreamReader)
    # receive length header -> msgpack load (dict)
    raw_msg_len = await reader.readexactly(4)
    msglen = struct.unpack('>I', raw_msg_len)[0]
    raw_msg = await reader.readexactly(msglen)

    msg = msgpack.loads(raw_msg)
    logger.debug('Message received {}'.format(_message_log(msg)))
    return msg


async def write_message(writer, message):
    assert isinstance(writer, asyncio.StreamWriter)
    logger.debug('Writing {}'.format(_message_log(message)))
    # use value of enum since Enum is not JSON serializable
    if isinstance(message['type'], MessageType):
        message['type'] = message['type'].value
    # msgpack (bytes) -> add length header (bytes)
    raw_msg = msgpack.dumps(message)
    raw_msg = struct.pack('>I', len(raw_msg)) + raw_msg
    writer.write(raw_msg)
    await writer.drain()
