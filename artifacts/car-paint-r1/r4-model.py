"""INACTIVE R4 numeric model; no production import or asset writes."""
import numpy as np


def payload(vertices, dimensions):
    """Signed height above sill and affine axle coordinate, no geometry change.

    The second coordinate is deliberately broad. Vertex interpolation cannot resolve
    detailed spray silhouettes on the existing sparse topology.
    """
    v = np.asarray(vertices)
    y = v[:, 1]
    front = dimensions['L'] / 2 - dimensions['foh']
    rear = front - dimensions['wb']
    return np.column_stack([v[:, 2] - dimensions['sill'], (y-rear)/dimensions['wb']])


def longitudinal_weight(axle_coordinate):
    u = np.asarray(axle_coordinate)
    front = np.clip(1-np.abs(u-.87)/.28,0,1)
    rear = np.clip(1-np.abs(u+.13)/.28,0,1)
    rear_face = np.clip((-u-.20)*8,0,1)
    return np.maximum(np.maximum(front,rear),rear_face)


def opacity(height, weight, level):
    """Monotone height profile for fixed longitudinal weight; minimal level0 dust."""
    a = np.asarray(level) / 3
    amount = .08 + .92 * a
    falloff = .16 + .06 * a
    return .5 * amount * np.exp2(-np.maximum(height, 0) / falloff * 1.442695) * (.72 + .28 * weight)


def film_hash(origins, gi_rect):
    # Runtime matrices and GI rect are float32; model those operations before floor.
    p = np.asarray(origins, dtype=np.float32)
    rect = np.asarray(gi_rect, dtype=np.float32)
    c = np.floor((p - rect) * np.float32(4) + np.float32(.37)).astype(np.int64).astype(np.uint32)
    with np.errstate(over='ignore'):
        h = c[:, 0] * np.uint32(1664525) + c[:, 1] * np.uint32(1013904223)
        h ^= h >> np.uint32(16)
        h *= np.uint32(2246822519)
        h ^= h >> np.uint32(13)
    levels = np.where(h < np.uint32(429496730), 0,
              np.where(h < np.uint32(1932735283), 1,
              np.where(h < np.uint32(3435973837), 2, 3)))
    return levels, (h & np.uint32(1023)) / 1024
