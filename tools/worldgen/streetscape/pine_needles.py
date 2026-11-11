"""ADR0088: hash-pinned CC0 needle twig, never the model atlas / cones as a card."""
from pathlib import Path
import hashlib
import json
import logging

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]


def needle_card(n=512, root=REPO):
    """Return RGBA or None for a clean-clone procedural fallback.

    Pigment luminance retains the measured accepted r2 pine texture, not a new
    exposure/lighting gain. Coverage/needle silhouette is assessed in lit scenes.
    """
    try:
        manifest = json.loads((root / 'art-source/world/cc0/pine_needles_manifest.json').read_text())
        images = {}
        for source in manifest['files']:
            path = root / manifest['raw_dir'] / source['file']
            if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('CC0 needle source hash mismatch: ' + source['file'])
            with Image.open(path) as image:
                images[source['map']] = image.copy()
        crop = tuple(manifest['crop_xyxy'])
        rgb = np.array(images['diffuse'].convert('RGB').crop(crop))
        alpha = np.array(images['alpha'].getchannel('R').crop(crop))
        labels, count = ndimage.label(alpha > 32)
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        if not count or sizes.max() < 100:
            raise ValueError('needle crop has no connected twig')
        # The alpha atlas also contains white UV padding around cones. It is not
        # opacity for foliage. Restrict to the actual connected needle-bearing twig.
        keep = ndimage.binary_dilation(labels == sizes.argmax(), iterations=1)
        alpha = np.where(keep, alpha, 0).astype(np.uint8)
        twig = Image.fromarray(np.dstack((rgb, alpha)))
        twig.thumbnail((int(n * .44), int(n * .81)), Image.Resampling.LANCZOS)
        card = Image.new('RGBA', (n, n))
        base = Image.new('RGBA', (n, n))
        base.alpha_composite(twig, (round(n * .5 - twig.width * .60), round(n * .92 - twig.height)))
        for angle in (-32, 0, 32):
            card = Image.alpha_composite(card, base.rotate(angle, Image.Resampling.BICUBIC,
                                                          center=(n * .5, n * .92)))
        a = np.array(card); covered = a[..., 3] > 127
        if covered.sum() < 100:
            raise ValueError('empty composed needle card')
        srgb = a[..., :3].astype(np.float32) / 255
        linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
        luma = linear[covered].mean(0) @ np.array([.2126, .7152, .0722])
        linear *= manifest['covered_mean_linear_luminance_WORKING_VALUE'] / max(float(luma), 1e-6)
        srgb = np.where(linear <= .0031308, linear * 12.92, 1.055 * np.maximum(linear, 0) ** (1 / 2.4) - .055)
        a[..., :3] = np.clip(np.rint(srgb * 255), 0, 255).astype(np.uint8)
        # Preserve colour beneath transparent texels for alpha-to-coverage mips.
        empty = a[..., 3] == 0
        nearest = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
        a[..., :3][empty] = a[nearest[0][empty], nearest[1][empty], :3]
        return Image.fromarray(a)
    except (OSError, ValueError, KeyError, StopIteration) as error:
        logging.warning('CC0 pine needles unavailable (%s); procedural needles retained', error)
        return None
