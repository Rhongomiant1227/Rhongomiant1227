# Profile images

The profile README uses PNG images so the cards also work in mobile browsers and
clients that do not render SVG `foreignObject`. Each `<picture>` defaults to the
single-column image. Browsers wider than 600 CSS pixels select a two-column image.
Both versions contain the same cards and are rendered at twice their display size.

Install the image dependency and refresh public GitHub data with:

```sh
python -m pip install -r scripts/requirements.txt
python scripts/update_profile_stats.py
```

The daily GitHub Actions workflow runs the same commands and commits both the SVG
source cards and their PNG variants. If an update fails, the README continues to
show the last committed images. The `GITHUB_TOKEN` used in Actions is supplied by
GitHub; it is never included in the images.

`hoyo-hi3.png`, `hoyo-gs.png`, `hoyo-sr.png` and `hoyo-zzz.png` are high-resolution
raster copies of the existing game-card SVG snapshots. After replacing a game
snapshot, rasterize its SVG at 1000 × 330 pixels in a browser that supports
`foreignObject`. Then rebuild both game layouts with:

```sh
python scripts/profile_images.py
```
