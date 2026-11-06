import base64
import ctypes
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_tri_hash_preservation_bridge import quickxor_bytes, dropbox_content_hash_bytes

def test_quickxor_matches_streaming_c_implementation(tmp_path):
    import subprocess
    source = Path("scripts/quickxorhash.c")
    lib = tmp_path / "libquickxorhash.so"
    subprocess.run(["cc", "-O3", "-shared", "-fPIC", str(source), "-o", str(lib)], check=True)
    dll = ctypes.CDLL(str(lib))
    update = dll.quickxor_update
    update.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64]
    data = bytes((i * 37 + 11) % 256 for i in range(4097))
    state = (ctypes.c_ubyte * 20)()
    offset = 0
    for start in range(0, len(data), 113):
        chunk = data[start:start + 113]
        buf = ctypes.create_string_buffer(chunk)
        update(state, ctypes.cast(buf, ctypes.c_void_p), len(chunk), offset)
        offset += len(chunk)
    for i, b in enumerate(struct.pack("<Q", len(data))):
        state[12 + i] ^= b
    assert base64.b64encode(bytes(state)).decode("ascii") == quickxor_bytes(data)

def test_quickxor_empty_file_vector():
    assert quickxor_bytes(b"") == base64.b64encode(bytes(20)).decode("ascii")

def test_dropbox_content_hash_single_block():
    data = b"motorcycle-simulation-preservation-bridge"
    expected = hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()
    assert dropbox_content_hash_bytes(data) == expected

def test_dropbox_content_hash_chunk_boundary():
    data = b"a" * (4 * 1024 * 1024 + 17)
    expected = hashlib.sha256(
        hashlib.sha256(data[:4 * 1024 * 1024]).digest() +
        hashlib.sha256(data[4 * 1024 * 1024:]).digest()
    ).hexdigest()
    assert dropbox_content_hash_bytes(data) == expected
