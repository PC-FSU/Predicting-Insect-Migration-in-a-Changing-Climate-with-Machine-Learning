#!/usr/bin/env python3
"""Split and clip downloaded WorldClim CMIP6 bioclim files to the study window.

Input:  data/data/GCM_ensemble/<GCM>/ssp<N>/wc2.1_10m_bioc_<GCM>_ssp<N>_<period>.tif
        (19 bands, global, 10 arc-min; from scripts/download_gcm_ensemble.sh)
Output: data/data/GCM_ensemble/<GCM>/ssp<N>/<period>/Clipped/In_tiff_format/Bio{1..19}.tif
        on exactly the grid and US-boundary mask of the existing clipped layers
        (lon -124.8333..-66.8333, lat 24.5..49.5, 348 x 150 cells, EPSG:4326, nodata NaN).

Self-test: with --check <global ACCESS-CM2 ssp245 2041-2060 file> the script
clips that file and compares Bio1 with data/data/SSP_245/.../Clipped/In_tiff_format/Bio1.tif.
"""

from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/data/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif"


MASK = ROOT / "data/data/SSP_245/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format/Bio1.tif"


def clip_file(src_path: Path, out_dir: Path, template: Path = TEMPLATE, mask: Path = MASK) -> None:
    """Crop to the study window and apply the US-boundary mask of the existing future layers."""
    with rasterio.open(template) as t:
        bounds, t_transform, t_shape = t.bounds, t.transform, (t.height, t.width)
    with rasterio.open(mask) as mk:
        keep = np.isfinite(mk.read(1))
    out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as src:
        win = from_bounds(*bounds, transform=src.transform)
        win = Window(round(win.col_off), round(win.row_off), round(win.width), round(win.height))
        assert (win.height, win.width) == t_shape, (win, t_shape)
        transform = src.window_transform(win)
        assert np.allclose([transform.c, transform.f], [t_transform.c, t_transform.f], atol=1e-6)
        assert src.count == 19, src.count
        for band in range(1, 20):
            arr = src.read(band, window=win).astype("float32")
            arr[~keep] = np.nan
            profile = dict(driver="GTiff", height=win.height, width=win.width, count=1, dtype="float32",
                           crs=src.crs, transform=transform, nodata=np.nan, compress="deflate")
            with rasterio.open(out_dir / f"Bio{band}.tif", "w", **profile) as dst:
                dst.write(arr, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT / "data/data/GCM_ensemble"))
    ap.add_argument("--check", default=None, help="global ACCESS-CM2 ssp245 2041-2060 file to self-test against the existing layers")
    args = ap.parse_args()

    if args.check:
        tmp = Path(args.check).parent / "check_clip"
        clip_file(Path(args.check), tmp)
        with rasterio.open(tmp / "Bio1.tif") as a, rasterio.open(ROOT / "data/data/SSP_245/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format/Bio1.tif") as b:
            x, y = a.read(1), b.read(1)
            m = np.isfinite(x) & np.isfinite(y)
            print("self-test: shapes", x.shape, y.shape, "| nan pattern equal:", bool((np.isfinite(x) == np.isfinite(y)).all()), "| max |diff|:", float(np.abs(x[m] - y[m]).max()))
        return 0

    pat = re.compile(r"wc2\.1_10m_bioc_(?P<gcm>[A-Za-z0-9\-]+)_ssp(?P<ssp>\d{3})_(?P<period>\d{4}-\d{4})\.tif$")
    n = 0
    for f in sorted(glob.glob(f"{args.root}/*/ssp*/wc2.1_10m_bioc_*.tif")):
        mobj = pat.search(f)
        if not mobj:
            continue
        gcm, ssp, period = mobj["gcm"], mobj["ssp"], mobj["period"].replace("-", "_")
        out_dir = Path(args.root) / gcm / f"ssp{ssp}" / period / "Clipped" / "In_tiff_format"
        if (out_dir / "Bio19.tif").exists():
            continue
        clip_file(Path(f), out_dir)
        n += 1
        print("clipped", gcm, ssp, period)
    print(f"done, {n} files clipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
