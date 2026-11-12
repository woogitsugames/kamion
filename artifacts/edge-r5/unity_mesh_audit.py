"""Read serialized Unity meshes for the next round's independent geometry audit.

No Unity process, asset mutations or production imports. Unsupported layouts fail
explicitly; do not accept an empty host mesh as evidence for its sector subassets.
"""
import re
from pathlib import Path

import numpy as np

_FORMAT = {0: '<f4', 1: '<f2', 2: 'u1', 3: 'i1', 4: '<u2',
           5: '<i2', 6: 'u1', 7: 'i1', 8: '<u2', 9: '<i2',
           10: '<u4', 11: '<i4'}


def read_meshes(path):
    source = Path(path).read_text(encoding='utf-8-sig')
    meshes = {}
    for document in re.split(r'^--- !u!43 &[^\r\n]+\r?\n', source, flags=re.M)[1:]:
        name = re.search(r'^  m_Name: (.+)$', document, re.M)[1].strip()
        count = int(re.search(r'm_VertexCount: (\d+)', document)[1])
        if not count:
            continue
        channels = [tuple(map(int, values)) for values in re.findall(
            r'- stream: (\d+)\s+offset: (\d+)\s+format: (\d+)\s+dimension: (\d+)', document)]
        if any(stream != 0 for stream, offset, fmt, dim in channels if dim):
            raise ValueError(f'{name}: unsupported multi-stream layout')
        stride = max(offset + np.dtype(_FORMAT[fmt]).itemsize * dim
                     for stream, offset, fmt, dim in channels if dim)
        stride = (stride + 3) // 4 * 4
        data = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)', document)[1])
        if len(data) != count * stride:
            raise ValueError(f'{name}: vertex byte count differs from declared layout')

        def attribute(slot):
            stream, offset, fmt, dim = channels[slot]
            if not dim:
                return None
            dtype = np.dtype(_FORMAT[fmt])
            result = np.ndarray((count, dim), dtype=dtype, buffer=data,
                                offset=offset, strides=(stride, dtype.itemsize)).copy()
            if fmt in (2, 3, 4, 5):
                limit = np.iinfo(dtype).max
                result = np.maximum(result.astype(float) / limit, -1)
            return result

        index_format = int(re.search(r'm_IndexFormat: (\d+)', document)[1])
        if index_format not in (0, 1):
            raise ValueError(f'{name}: unexpected index format')
        dtype = np.dtype('<u2' if index_format == 0 else '<u4')
        indices = np.frombuffer(bytes.fromhex(re.search(
            r'm_IndexBuffer: ([0-9a-fA-F]+)', document)[1]), dtype=dtype).copy()
        submeshes = []
        for first, size, base in re.findall(
                r'firstByte: (\d+)\s+indexCount: (\d+)\s+topology: 0\s+baseVertex: (\d+)', document):
            first, size, base = int(first), int(size), int(base)
            if first % dtype.itemsize or size % 3:
                raise ValueError(f'{name}: unsupported triangle range')
            selected = indices[first // dtype.itemsize:first // dtype.itemsize + size].astype(np.int64) + base
            if len(selected) != size or np.any(selected >= count):
                raise ValueError(f'{name}: indices outside vertices')
            submeshes.append(selected.reshape(-1, 3))
        if not submeshes or name in meshes:
            raise ValueError(f'{name}: empty submesh list or duplicate mesh')
        meshes[name] = dict(positions=attribute(0), normals=attribute(1),
                            colors=attribute(3), uv0=attribute(4), uv1=attribute(5),
                            indices=indices, triangles=submeshes, stride=stride,
                            count=count)
    if not meshes:
        raise ValueError('No populated serialized mesh; cannot report an empty pass')
    return meshes
