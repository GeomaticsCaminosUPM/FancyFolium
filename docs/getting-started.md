# Getting started

## Installation

```bash
pip install fancyfolium
# or, for raster support (raster_layer / vector_to_raster):
pip install "fancyfolium[raster]"
```

## Control panel

Every map gets a floating control panel (top-right), a legend stack
(bottom-right), and a statistics-panel button (bottom-left, 📊) - all
injected automatically.

- **Dropdown** sections (`overlay=False` layers): radio-style, only one
  active at a time.
- **Checkbox** sections (`overlay=True` layers): any combination can be
  toggled independently.
- **⚙** next to each layer reveals an opacity slider for that layer alone.
- Legends (bottom-right) update automatically as layers are toggled.
- **📊** (bottom-left) opens the statistics panel - pick any vector/marker
  layer to see a live histogram of its colormap column.

## Colourmaps (`cmap`)

`cmap` accepts a named string (`"viridis"`, `"plasma"`, `"rdylgn"`,
`"rdylgn_r"`, `"Reds"`/`"Blues"`/`"Greens"`/`"Purples"`/`"Oranges"`/`"Yellows"`),
a `t -> hex` callable, a `{value: hex}` dict, or an ordered list of hex
colours (the last two imply categorical treatment). See
{func}`~FancyFolium.resolve_cmap` for the full resolution rules.

## Count columns

Pass `count=True` on `vector_layer`/`marker_layer`/`vector_to_raster` to
treat a column as a **counts** field (storeys, population, occurrences):
validated to hold only whole numbers (see
{func}`~FancyFolium.validate_count_column`), with the colour scale
defaulting to `vmin=0`/`vmax=column.max()` instead of the general numeric
p10/p90 default. Mutually exclusive with `categorical`.

## Emoji markers

`marker_layer`'s `marker_column` holds a categorical class shown as each
point's icon; `marker=` can be a fixed string, a `{category: emoji}` dict,
or omitted to show the raw `marker_column` value. See
{func}`~FancyFolium.emoji_for_categories` for an automatic per-category emoji
helper.

## Statistics panel & histograms

Pick any vector/marker layer in the 📊 panel to see a histogram of its
colormap column - binned for numeric columns, one bar per category for
categorical ones, or grouped by `marker_column` for marker layers that use
it. Two toggle buttons apply everywhere:

- **`#` / `%`** - count vs. percent-of-total on the y-axis.
- **`lin` / `log`** - linear vs. logarithmic *bin edges* for numeric
  histograms (not the y-axis) - much better resolution for skewed data
  like building heights.

## Next steps

- {doc}`examples` for a short, step-by-step walkthrough (one raster layer, one
  polygon layer, one marker layer) - runnable directly in Google Colab, no
  install needed.
- The API reference (sidebar) for every function's full parameter list.
