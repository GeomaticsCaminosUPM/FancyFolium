/* ============================================================
   map_controls.js  —  FancyFolium
   ============================================================ */

/* ── Utilities ────────────────────────────────────────────── */

function _getLeafletMap(mapId) { return window[mapId] || null; }

function _findLayerByName(lmap, name, mapId) {
  var data = (window._MAPLIB_DATA || {})[mapId] || {};
  var all  = [].concat(data.bgLayers || [], data.rstLayers || [], data.vecLayers || []);
  for (var i = 0; i < all.length; i++) {
    if (all[i].name === name && all[i].js_var && window[all[i].js_var])
      return window[all[i].js_var];
  }
  return null;
}

/* ── Opacity control (works for tile/image/marker/path layers, and
   FeatureGroups by recursing into their children) ────────────────────── */

function _setLayerOpacity(layerObj, value) {
  if (!layerObj) return;
  if (typeof layerObj.eachLayer === 'function') {
    layerObj.eachLayer(function(child) { _setLayerOpacity(child, value); });
    return;
  }
  if (typeof layerObj.setOpacity === 'function') { layerObj.setOpacity(value); return; }
  if (typeof layerObj.setStyle === 'function') { layerObj.setStyle({ opacity: value, fillOpacity: value }); }
}

/* ── Tab switching ────────────────────────────────────────── */

function maplibTab(btn, panelKey) {
  var panel = btn.closest('.maplib-panel');
  panel.querySelectorAll('.maplib-tab').forEach(function(t) { t.classList.remove('active'); });
  panel.querySelectorAll('.maplib-panel-body').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  var body = document.getElementById('maplib-panel-' + panelKey);
  if (body) body.classList.add('active');
}

/* ── Dropdown ─────────────────────────────────────────────── */

function _buildDropdown(containerId, layers, mapId, emptyLabel) {
  var wrap = document.getElementById(containerId);
  if (!wrap) return;
  if (!layers || !layers.length) { wrap.innerHTML = ''; return; }

  var label = document.createElement('div');
  label.className = 'maplib-dropdown-label';
  label.textContent = 'Active layer';

  var sel = document.createElement('select');
  sel.innerHTML = '<option value="">— ' + (emptyLabel || 'None') + ' —</option>';
  var activeVal = '';
  layers.forEach(function(l) {
    var opt = document.createElement('option');
    opt.value = l.name; opt.textContent = l.name;
    sel.appendChild(opt);
    if (l.active) activeVal = l.name;
  });
  if (activeVal) sel.value = activeVal;

  sel.addEventListener('change', function() {
    var lmap = _getLeafletMap(mapId);
    if (!lmap) return;
    layers.forEach(function(l) { var ly = _findLayerByName(lmap, l.name, mapId); if (ly) lmap.removeLayer(ly); });
    if (sel.value) {
      var chosen = _findLayerByName(lmap, sel.value, mapId);
      if (chosen) lmap.addLayer(chosen);
    }
    _refreshLegends(mapId);
    opacityRow.style.display = sel.value ? 'flex' : 'none';
    opacitySlider.value = 100;
    opacityVal.textContent = '100%';
  });

  // Opacity slider, applies to whichever layer is currently selected.
  var opacityRow = document.createElement('div');
  opacityRow.className = 'maplib-dropdown-opacity-row';
  opacityRow.style.display = activeVal ? 'flex' : 'none';
  var gearIcon = document.createElement('span');
  gearIcon.textContent = '⚙';
  gearIcon.style.fontSize = '11px';
  gearIcon.style.color = '#888';
  var opacitySlider = document.createElement('input');
  opacitySlider.type = 'range'; opacitySlider.min = '0'; opacitySlider.max = '100'; opacitySlider.value = '100';
  var opacityVal = document.createElement('span');
  opacityVal.className = 'maplib-opacity-val';
  opacityVal.textContent = '100%';
  opacitySlider.addEventListener('input', function() {
    var lmap = _getLeafletMap(mapId);
    opacityVal.textContent = opacitySlider.value + '%';
    if (!lmap || !sel.value) return;
    var ly = _findLayerByName(lmap, sel.value, mapId);
    if (ly) _setLayerOpacity(ly, parseInt(opacitySlider.value, 10) / 100);
  });
  opacityRow.appendChild(gearIcon);
  opacityRow.appendChild(opacitySlider);
  opacityRow.appendChild(opacityVal);

  wrap.innerHTML = '';
  wrap.appendChild(label);
  wrap.appendChild(sel);
  wrap.appendChild(opacityRow);
}

/* ── Checkboxes ───────────────────────────────────────────── */

function _buildCheckboxes(containerId, layers, mapId) {
  var container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  if (!layers || !layers.length) return;

  layers.forEach(function(l) {
    var row = document.createElement('label');
    row.className = 'maplib-check-row';
    var cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = (l.active !== false);
    var span = document.createElement('span');
    span.title = l.name; span.textContent = l.name;

    var gearBtn = document.createElement('button');
    gearBtn.type = 'button';
    gearBtn.className = 'maplib-opacity-btn';
    gearBtn.title = 'Layer opacity';
    gearBtn.textContent = '⚙';

    var opRow = document.createElement('div');
    opRow.className = 'maplib-opacity-row';
    var opSlider = document.createElement('input');
    opSlider.type = 'range'; opSlider.min = '0'; opSlider.max = '100'; opSlider.value = '100';
    var opVal = document.createElement('span');
    opVal.className = 'maplib-opacity-val';
    opVal.textContent = '100%';

    cb.addEventListener('change', function() {
      var lmap = _getLeafletMap(mapId);
      if (!lmap) return;
      var layer = _findLayerByName(lmap, l.name, mapId);
      if (!layer) return;
      if (cb.checked) lmap.addLayer(layer); else lmap.removeLayer(layer);
      _refreshLegends(mapId);
    });

    gearBtn.addEventListener('click', function(e) {
      e.preventDefault(); e.stopPropagation();
      opRow.classList.toggle('open');
    });

    opSlider.addEventListener('input', function(e) {
      e.stopPropagation();
      opVal.textContent = opSlider.value + '%';
      var lmap = _getLeafletMap(mapId);
      if (!lmap) return;
      var layer = _findLayerByName(lmap, l.name, mapId);
      if (layer) _setLayerOpacity(layer, parseInt(opSlider.value, 10) / 100);
    });
    opSlider.addEventListener('click', function(e) { e.stopPropagation(); });

    opRow.appendChild(opSlider);
    opRow.appendChild(opVal);

    row.appendChild(cb); row.appendChild(span); row.appendChild(gearBtn);
    container.appendChild(row);
    container.appendChild(opRow);
  });
}

function _updateSep(sepId, dropLayers, checkLayers) {
  var sep = document.getElementById(sepId);
  if (!sep) return;
  sep.style.display = (dropLayers && dropLayers.length && checkLayers && checkLayers.length) ? 'block' : 'none';
}

/* ── Initial visibility ───────────────────────────────────── */

function _applyInitialVisibility(lmap, data, mapId) {
  function applyGroup(layers) {
    if (!layers || !layers.length) return;
    var drops  = layers.filter(function(l) { return !l.overlay; });
    var checks = layers.filter(function(l) { return  l.overlay; });
    var activeName = '';
    drops.forEach(function(l) { if (l.active) activeName = l.name; });
    drops.forEach(function(l) {
      var ly = _findLayerByName(lmap, l.name, mapId); if (!ly) return;
      if (l.name === activeName) { if (!lmap.hasLayer(ly)) lmap.addLayer(ly); }
      else { if (lmap.hasLayer(ly)) lmap.removeLayer(ly); }
    });
    checks.forEach(function(l) {
      var ly = _findLayerByName(lmap, l.name, mapId); if (!ly) return;
      if (l.active === false) { if (lmap.hasLayer(ly)) lmap.removeLayer(ly); }
      else { if (!lmap.hasLayer(ly)) lmap.addLayer(ly); }
    });
  }
  applyGroup(data.bgLayers);
  applyGroup(data.rstLayers);
  applyGroup(data.vecLayers);
}

/* ── Main init ────────────────────────────────────────────── */

function _populateControls(mapId, data) {
  var bgOv  = (data.bgLayers  || []).filter(function(l) { return  l.overlay; });
  var bgDr  = (data.bgLayers  || []).filter(function(l) { return !l.overlay; });
  var rstOv = (data.rstLayers || []).filter(function(l) { return  l.overlay; });
  var rstDr = (data.rstLayers || []).filter(function(l) { return !l.overlay; });
  var vecOv = (data.vecLayers || []).filter(function(l) { return  l.overlay; });
  var vecDr = (data.vecLayers || []).filter(function(l) { return !l.overlay; });

  _buildDropdown('maplib-bg-dropdown-wrap',    bgDr,  mapId, 'background');
  _buildCheckboxes('maplib-bg-checks',          bgOv,  mapId);
  _updateSep('maplib-bg-sep',    bgDr,  bgOv);
  _buildDropdown('maplib-raster-dropdown-wrap', rstDr, mapId, 'raster');
  _buildCheckboxes('maplib-raster-checks',       rstOv, mapId);
  _updateSep('maplib-raster-sep', rstDr, rstOv);
  _buildDropdown('maplib-vector-dropdown-wrap', vecDr, mapId, 'vector');
  _buildCheckboxes('maplib-vector-checks',       vecOv, mapId);
  _updateSep('maplib-vector-sep', vecDr, vecOv);
}

function maplibInit(mapId, data) {
  if (!data) return;
  _populateControls(mapId, data);

  var lmap = _getLeafletMap(mapId);
  if (lmap) {
    _applyInitialVisibility(lmap, data, mapId);
    _enforceZOrder(lmap, data);
    _moveScaleBar(lmap);
  }
  _refreshLegends(mapId);
  _initStatsPanel(mapId, data);
}

/* ── Move scale bar to top-left ───────────────────────────── */

function _moveScaleBar(lmap) {
  // Leaflet renders scale in bottom-left by default; we relocate to top-left via CSS.
  // The CSS rule `.leaflet-top.leaflet-left .leaflet-control-scale` handles placement.
  // Here we move the DOM node into the top-left corner container.
  setTimeout(function() {
    var scaleEl = document.querySelector('.leaflet-control-scale');
    var topLeft = document.querySelector('.leaflet-top.leaflet-left');
    if (scaleEl && topLeft && scaleEl.parentNode !== topLeft) {
      topLeft.appendChild(scaleEl);
    }
  }, 200);
}

/* ── Z-order ──────────────────────────────────────────────── */

function _enforceZOrder(lmap, data) {
  if (!lmap.getPane('maplibBackground')) lmap.createPane('maplibBackground').style.zIndex = 200;
  if (!lmap.getPane('maplibRaster'))     lmap.createPane('maplibRaster').style.zIndex = 300;
  if (!lmap.getPane('maplibVector'))     lmap.createPane('maplibVector').style.zIndex = 400;
  var allBg  = data.bgLayers  || [];
  var allRst = data.rstLayers || [];
  var allVec = data.vecLayers || [];
  lmap.eachLayer(function(layer) {
    var name = layer.options && layer.options.name; if (!name) return;
    if (allBg.some(function(l)  { return l.name === name; })) layer.options.pane = 'maplibBackground';
    if (allRst.some(function(l) { return l.name === name; })) layer.options.pane = 'maplibRaster';
    if (allVec.some(function(l) { return l.name === name; })) layer.options.pane = 'maplibVector';
  });
}

/* ── Legend rendering ─────────────────────────────────────── */

/* Per-histogram-box display preferences, keyed by legend name.
   pct: show % of total instead of raw count.
   log: use a logarithmic (instead of linear) scale to size the bars. */
function _refreshLegends(mapId) {
  var container = document.getElementById('maplib-legend-' + mapId);
  if (!container) return;
  var legends = (window._MAPLIB_LEGENDS || {})[mapId] || {};
  var data    = (window._MAPLIB_DATA    || {})[mapId] || {};
  var lmap    = _getLeafletMap(mapId);
  var visibleNames = new Set();
  if (lmap) {
    var all = [].concat(data.bgLayers || [], data.rstLayers || [], data.vecLayers || []);
    all.forEach(function(e) {
      if (e.js_var && window[e.js_var] && lmap.hasLayer(window[e.js_var])) visibleNames.add(e.name);
    });
  }
  var html = '';
  Object.keys(legends).forEach(function(name) {
    if (!visibleNames.has(name)) return;
    // Each layer name maps to a *list* of legend specs (e.g. a colour legend
    // plus a separate marker-values legend), not a single spec.
    var specList = legends[name]; if (!specList) return;
    (Array.isArray(specList) ? specList : [specList]).forEach(function(spec) {
      if (!spec) return;
      if (spec.type === 'numeric') {
        var grad = spec.colors.map(function(s) { return s[1]; }).join(', ');
        var unit = spec.unit ? ' ' + spec.unit : '';
        html += '<div class="maplib-legend-box"><div class="maplib-legend-title">' + _esc(spec.name || name) + '</div>'
              + '<div class="maplib-legend-grad" style="background:linear-gradient(to right,' + grad + ')"></div>'
              + '<div class="maplib-legend-labels"><span>' + _fmt(spec.vmin) + unit + '</span><span>' + _fmt(spec.vmax) + unit + '</span></div></div>';
      } else if (spec.type === 'categorical' && spec.entries) {
        var sw = spec.entries.map(function(e) {
          return '<div class="maplib-legend-swatch-row"><span class="maplib-legend-swatch" style="background:' + e.color + '"></span><span>' + _esc(e.label) + '</span></div>';
        }).join('');
        html += '<div class="maplib-legend-box"><div class="maplib-legend-title">' + _esc(spec.name || name) + '</div>' + sw + '</div>';
      } else if (spec.type === 'markers' && spec.entries) {
        // Skip the icon glyph when it's identical to the label (e.g. a
        // marker_column that already holds emoji values as its own text) —
        // showing the same symbol twice in one row is just noise.
        var mk = spec.entries.map(function(e) {
          var iconHtml = (e.icon && e.icon !== e.label)
            ? '<span class="maplib-legend-marker-icon">' + _esc(e.icon) + '</span>' : '';
          return '<div class="maplib-legend-swatch-row">' + iconHtml + '<span>' + _esc(e.label) + '</span></div>';
        }).join('');
        html += '<div class="maplib-legend-box"><div class="maplib-legend-title">' + _esc(spec.name || name) + '</div>' + mk + '</div>';
      }
    });
  });
  container.innerHTML = html;
}

function _esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function _fmt(v) {
  if (v === null || v === undefined) return '';
  var n = parseFloat(v);
  return isNaN(n) ? String(v) : (Math.abs(n) >= 1000 ? n.toFixed(0) : n.toPrecision(3));
}

/* ═══════════════════════════════════════════════════════════
   STATS PANEL
   ═══════════════════════════════════════════════════════════ */

var _maplibStatsChart = null;   // holds the Chart.js instance
var _maplibStatsPanelOpen = false;
// Display preferences for the currently-open histogram: pct = count vs.
// percent-of-total on the y-axis, log = linear vs. logarithmic y-axis scale.
var _maplibStatsPrefs = { pct: false, log: false };

function _initStatsPanel(mapId, data) {
  var vecLayers = data.vecLayers || [];
  if (!vecLayers.length) return;

  // ── Toggle button ──────────────────────────────────────
  var btn = document.createElement('div');
  btn.className = 'maplib-stats-btn';
  btn.title = 'Open statistics panel';
  btn.innerHTML = '📊';
  btn.addEventListener('click', function() { _toggleStatsPanel(mapId, data); });
  document.body.appendChild(btn);

  // ── Panel ──────────────────────────────────────────────
  var panel = document.createElement('div');
  panel.id = 'maplib-stats-panel-' + mapId;
  panel.className = 'maplib-stats-panel';

  // Header
  var header = document.createElement('div');
  header.className = 'maplib-stats-header';

  var lbl = document.createElement('label');
  lbl.textContent = 'Layer';
  lbl.htmlFor = 'maplib-stats-sel-' + mapId;

  var sel = document.createElement('select');
  sel.id = 'maplib-stats-sel-' + mapId;
  var emptyOpt = document.createElement('option');
  emptyOpt.value = ''; emptyOpt.textContent = '— choose layer —';
  sel.appendChild(emptyOpt);
  vecLayers.forEach(function(l) {
    var opt = document.createElement('option');
    opt.value = l.name; opt.textContent = l.name;
    sel.appendChild(opt);
  });

  // Pins control (for numeric layers)
  var pinsWrap = document.createElement('div');
  pinsWrap.className = 'maplib-stats-pins-wrap';
  pinsWrap.id = 'maplib-stats-pins-wrap-' + mapId;
  var pinsLbl = document.createElement('label');
  pinsLbl.textContent = 'Bins:';
  var pinsInput = document.createElement('input');
  pinsInput.type = 'number';
  pinsInput.min = '2'; pinsInput.max = '100'; pinsInput.value = '10';
  pinsInput.id = 'maplib-stats-pins-' + mapId;
  pinsWrap.appendChild(pinsLbl);
  pinsWrap.appendChild(pinsInput);
  pinsWrap.style.display = 'none';

  // Count/% and linear/log toggle buttons
  var togglesWrap = document.createElement('div');
  togglesWrap.className = 'maplib-stats-toggles';
  togglesWrap.id = 'maplib-stats-toggles-' + mapId;
  togglesWrap.style.display = 'none';
  var pctBtn = document.createElement('button');
  pctBtn.type = 'button';
  pctBtn.className = 'maplib-hist-toggle-btn maplib-hist-toggle-pct';
  pctBtn.title = 'Toggle count / percent';
  pctBtn.textContent = '#';
  var logBtn = document.createElement('button');
  logBtn.type = 'button';
  logBtn.className = 'maplib-hist-toggle-btn maplib-hist-toggle-log';
  logBtn.title = 'Toggle linear / logarithmic bin sizing (useful for skewed data, e.g. a few very tall buildings among many short ones)';
  logBtn.textContent = 'lin';
  togglesWrap.appendChild(pctBtn);
  togglesWrap.appendChild(logBtn);

  var closeBtn = document.createElement('button');
  closeBtn.className = 'maplib-stats-close';
  closeBtn.innerHTML = '✕';
  closeBtn.addEventListener('click', function() { _toggleStatsPanel(mapId, data); });

  header.appendChild(lbl);
  header.appendChild(sel);
  header.appendChild(pinsWrap);
  header.appendChild(togglesWrap);
  header.appendChild(closeBtn);

  // Body
  var body = document.createElement('div');
  body.className = 'maplib-stats-body';
  body.id = 'maplib-stats-body-' + mapId;
  body.innerHTML = '<div class="maplib-stats-empty">Select a layer to view statistics</div>';

  panel.appendChild(header);
  panel.appendChild(body);
  document.body.appendChild(panel);

  // Events — re-read window._MAPLIB_DATA[mapId] at fire time (rather than the
  // captured `data`) so a merge_maps() city switch is reflected here too.
  sel.addEventListener('change', function() {
    var live = (window._MAPLIB_DATA || {})[mapId] || data;
    _renderHistogram(mapId, live, sel.value, parseInt(pinsInput.value) || 10);
  });
  pinsInput.addEventListener('input', function() {
    var live = (window._MAPLIB_DATA || {})[mapId] || data;
    if (sel.value) _renderHistogram(mapId, live, sel.value, parseInt(pinsInput.value) || 10);
  });
  pctBtn.addEventListener('click', function() {
    _maplibStatsPrefs.pct = !_maplibStatsPrefs.pct;
    pctBtn.classList.toggle('active', _maplibStatsPrefs.pct);
    pctBtn.textContent = _maplibStatsPrefs.pct ? '%' : '#';
    var live = (window._MAPLIB_DATA || {})[mapId] || data;
    if (sel.value) _renderHistogram(mapId, live, sel.value, parseInt(pinsInput.value) || 10);
  });
  logBtn.addEventListener('click', function() {
    _maplibStatsPrefs.log = !_maplibStatsPrefs.log;
    logBtn.classList.toggle('active', _maplibStatsPrefs.log);
    logBtn.textContent = _maplibStatsPrefs.log ? 'log' : 'lin';
    var live = (window._MAPLIB_DATA || {})[mapId] || data;
    if (sel.value) _renderHistogram(mapId, live, sel.value, parseInt(pinsInput.value) || 10);
  });
}

function _updateStatsPanelLayers(mapId, data) {
  var sel = document.getElementById('maplib-stats-sel-' + mapId);
  if (!sel) return;
  sel.innerHTML = '';
  var emptyOpt = document.createElement('option');
  emptyOpt.value = ''; emptyOpt.textContent = '— choose layer —';
  sel.appendChild(emptyOpt);
  (data.vecLayers || []).forEach(function(l) {
    var opt = document.createElement('option');
    opt.value = l.name; opt.textContent = l.name;
    sel.appendChild(opt);
  });
  var body = document.getElementById('maplib-stats-body-' + mapId);
  if (body) body.innerHTML = '<div class="maplib-stats-empty">Select a layer to view statistics</div>';
}

function _toggleStatsPanel(mapId, data) {
  var panel = document.getElementById('maplib-stats-panel-' + mapId);
  if (!panel) return;
  _maplibStatsPanelOpen = !_maplibStatsPanelOpen;
  if (_maplibStatsPanelOpen) {
    panel.classList.add('open');
    // Re-render if a layer is already selected
    var sel = document.getElementById('maplib-stats-sel-' + mapId);
    var pins = parseInt((document.getElementById('maplib-stats-pins-' + mapId) || {}).value) || 10;
    if (sel && sel.value) _renderHistogram(mapId, data, sel.value, pins);
  } else {
    panel.classList.remove('open');
  }
}

/* ── Extract feature values + colors from a Folium GeoJson layer ── */

function _extractLayerData(jsVar) {
  var layerObj = window[jsVar];
  if (!layerObj) return null;

  var features = [];

  // FeatureGroup wrapping a GeoJson: iterate children
  if (layerObj.eachLayer) {
    layerObj.eachLayer(function(child) {
      if (child.toGeoJSON) {
        var gj = child.toGeoJSON();
        var feats = gj.type === 'FeatureCollection' ? gj.features : [gj];
        feats.forEach(function(f) { features.push(f); });
      }
    });
  } else if (layerObj.toGeoJSON) {
    var gj = layerObj.toGeoJSON();
    features = gj.type === 'FeatureCollection' ? gj.features : [gj];
  }

  return features;
}

/* ── Get the color for a layer entry (from legend or fallback) ── */

function _getLayerColors(mapId, layerName, features) {
  var legends  = (window._MAPLIB_LEGENDS || {})[mapId] || {};
  var spec     = legends[layerName];
  // Try to read __color from each feature's properties (injected by Python style_fn)
  var hasColor = features.length > 0 && features[0].properties && features[0].properties.__color;
  if (hasColor) {
    return features.map(function(f) { return f.properties.__color || '#4a90d9'; });
  }
  return features.map(function() { return '#4a90d9'; });
}

/* ── Build histogram from numeric values ─────────────────────── */

function _buildNumericHistogram(values, colors, nBins, useLogBins) {
  if (!values.length) return null;
  var mn = Math.min.apply(null, values);
  var mx = Math.max.apply(null, values);
  if (mn === mx) { mn -= 0.5; mx += 0.5; }

  // Log-spaced bin *edges* (not a log y-axis): most real-world distributions
  // (building heights, populations, …) are right-skewed — a few very large
  // values alongside many small ones — so evenly-spaced edges dump almost
  // everything into the first bin. Spacing edges logarithmically instead
  // gives every order of magnitude its own share of bins.
  var canLog = useLogBins && mn > 0;
  var edges = [];
  if (canLog) {
    var logMn = Math.log(mn), logMx = Math.log(mx);
    for (var e = 0; e <= nBins; e++) edges.push(Math.exp(logMn + (e / nBins) * (logMx - logMn)));
  } else {
    var step0 = (mx - mn) / nBins;
    for (var e2 = 0; e2 <= nBins; e2++) edges.push(mn + e2 * step0);
  }

  var bins = [], binColors = [], counts = [];
  for (var i = 0; i < nBins; i++) {
    var lo = edges[i];
    var hi = edges[i + 1];
    bins.push(lo.toPrecision(3) + '–' + hi.toPrecision(3));
    var cnt = 0;
    var rSum = 0, gSum = 0, bSum = 0, cCnt = 0;
    values.forEach(function(v, idx) {
      var inBin = (i < nBins - 1) ? (v >= lo && v < hi) : (v >= lo && v <= hi);
      if (inBin) {
        cnt++;
        // parse hex color for averaging
        var hex = (colors[idx] || '#4a90d9').replace('#','');
        if (hex.length === 6) {
          rSum += parseInt(hex.slice(0,2),16);
          gSum += parseInt(hex.slice(2,4),16);
          bSum += parseInt(hex.slice(4,6),16);
          cCnt++;
        }
      }
    });
    counts.push(cnt);
    if (cCnt > 0) {
      binColors.push('rgba(' + Math.round(rSum/cCnt) + ',' + Math.round(gSum/cCnt) + ',' + Math.round(bSum/cCnt) + ',0.82)');
    } else {
      binColors.push('rgba(74,144,217,0.82)');
    }
  }
  return { labels: bins, counts: counts, colors: binColors };
}

/* ── Build histogram from categorical (or marker_column-grouped) values ── */

function _buildCategoricalHistogram(values, colors, icons) {
  var catMap = {}, colorMap = {}, iconMap = {};
  values.forEach(function(v, idx) {
    var key = String(v);
    catMap[key]  = (catMap[key]  || 0) + 1;
    if (!colorMap[key]) colorMap[key] = colors[idx] || '#4a90d9';
    if (icons && icons[idx] && !iconMap[key]) iconMap[key] = icons[idx];
  });
  var labels = Object.keys(catMap).sort();
  var counts = labels.map(function(k) { return catMap[k]; });
  var cols   = labels.map(function(k) {
    var hex = (colorMap[k] || '#4a90d9').replace('#','');
    if (hex.length === 6) {
      return 'rgba(' + parseInt(hex.slice(0,2),16) + ',' + parseInt(hex.slice(2,4),16) + ',' + parseInt(hex.slice(4,6),16) + ',0.82)';
    }
    return 'rgba(74,144,217,0.82)';
  });
  var iconList = icons ? labels.map(function(k) { return iconMap[k] || ''; }) : null;
  return { labels: labels, counts: counts, colors: cols, icons: iconList };
}

/* ── Render histogram ─────────────────────────────────────── */

function _renderHistogram(mapId, data, layerName, nBins) {
  var body = document.getElementById('maplib-stats-body-' + mapId);
  if (!body) return;

  var vecLayers = data.vecLayers || [];
  var entry = null;
  for (var i = 0; i < vecLayers.length; i++) {
    if (vecLayers[i].name === layerName) { entry = vecLayers[i]; break; }
  }
  if (!entry) {
    body.innerHTML = '<div class="maplib-stats-empty">Layer data not available</div>';
    return;
  }

  var values, colors, icons = null, isNum, groupedByMarker = false;

  if (entry.rows && entry.rows.length) {
    // marker_layer(): per-row data collected server-side (see layers/marker.py),
    // since Marker/CircleMarker instances don't carry GeoJSON properties.
    if (entry.marker_column) {
      // marker_column is always categorical: bucket by it (icons per bucket),
      // regardless of whether `column` itself is numeric or categorical.
      values = entry.rows.map(function(r) { return r.mk; }).filter(function(v) { return v !== null && v !== undefined; });
      colors = entry.rows.filter(function(r) { return r.mk !== null && r.mk !== undefined; }).map(function(r) { return r.color; });
      icons  = entry.rows.filter(function(r) { return r.mk !== null && r.mk !== undefined; }).map(function(r) { return r.icon; });
      isNum = false;
      groupedByMarker = true;
    } else {
      values = entry.rows.map(function(r) { return r.v; }).filter(function(v) { return v !== null && v !== undefined; });
      colors = entry.rows.filter(function(r) { return r.v !== null && r.v !== undefined; }).map(function(r) { return r.color; });
      isNum = values.length > 0 && typeof values[0] === 'number';
    }
  } else {
    if (!entry.js_var) {
      body.innerHTML = '<div class="maplib-stats-empty">Layer data not available</div>';
      return;
    }
    var features = _extractLayerData(entry.js_var);
    if (!features || !features.length) {
      body.innerHTML = '<div class="maplib-stats-empty">No features found</div>';
      return;
    }
    // Use the column this layer was actually built with (matches its legend);
    // fall back to the first non-internal property only if none was recorded.
    var sample = features[0].properties || {};
    var colName = entry.column || null;
    if (!colName || !(colName in sample)) {
      var propKeys = [];
      Object.keys(sample).forEach(function(k) { if (k !== '__color' && k !== '__popup_html') propKeys.push(k); });
      colName = null;
      propKeys.forEach(function(k) {
        if (!colName) {
          var v = sample[k];
          if (v !== null && v !== undefined) colName = k;
        }
      });
    }
    if (!colName) {
      body.innerHTML = '<div class="maplib-stats-empty">No plottable columns found</div>';
      return;
    }
    values = features.map(function(f) { return (f.properties || {})[colName]; }).filter(function(v) { return v !== null && v !== undefined; });
    colors = _getLayerColors(mapId, layerName, features);
    isNum  = values.length > 0 && typeof values[0] === 'number';
  }

  // Show/hide bins control (only meaningful for un-grouped numeric data)
  var pinsWrap = document.getElementById('maplib-stats-pins-wrap-' + mapId);
  if (pinsWrap) pinsWrap.style.display = (isNum && !groupedByMarker) ? 'flex' : 'none';
  var togglesWrap = document.getElementById('maplib-stats-toggles-' + mapId);
  if (togglesWrap) togglesWrap.style.display = 'flex';
  // The log/lin toggle only affects how numeric bin *edges* are chosen; it's
  // meaningless once rows are grouped by a categorical marker_column.
  var logBtn = togglesWrap ? togglesWrap.querySelector('.maplib-hist-toggle-log') : null;
  if (logBtn) logBtn.style.display = (isNum && !groupedByMarker) ? '' : 'none';

  var hist = (isNum && !groupedByMarker)
    ? _buildNumericHistogram(values, colors, nBins, _maplibStatsPrefs.log)
    : _buildCategoricalHistogram(values, colors, icons);

  if (!hist) {
    body.innerHTML = '<div class="maplib-stats-empty">Could not compute histogram</div>';
    return;
  }

  var total = hist.counts.reduce(function(a, b) { return a + b; }, 0) || 1;
  var displayCounts = _maplibStatsPrefs.pct
    ? hist.counts.map(function(c) { return c / total * 100; })
    : hist.counts.slice();
  var axisLabel = _maplibStatsPrefs.pct ? '%' : 'Count';

  // Build stats summary
  var summaryHtml = '';
  if (isNum && !groupedByMarker) {
    var sum = values.reduce(function(a,b){return a+b;},0);
    var mean = sum / values.length;
    var variance = values.reduce(function(a,v){return a+Math.pow(v-mean,2);},0) / values.length;
    var std = Math.sqrt(variance);
    summaryHtml = '<b>n</b> ' + values.length
      + '&nbsp;&nbsp;<b>μ</b> ' + mean.toPrecision(4)
      + '&nbsp;&nbsp;<b>σ</b> ' + std.toPrecision(3);
  } else {
    summaryHtml = '<b>n</b> ' + values.length + '&nbsp;&nbsp;<b>cats</b> ' + hist.labels.length;
  }

  // Build DOM
  body.innerHTML = '';
  var canvasWrap = document.createElement('div');
  canvasWrap.className = 'maplib-stats-canvas-wrap';
  var canvas = document.createElement('canvas');
  canvasWrap.appendChild(canvas);

  var summary = document.createElement('div');
  summary.className = 'maplib-stats-summary';
  summary.innerHTML = summaryHtml;

  body.appendChild(canvasWrap);
  body.appendChild(summary);

  // Destroy old chart
  if (_maplibStatsChart) { _maplibStatsChart.destroy(); _maplibStatsChart = null; }

  // Render with Chart.js (loaded from CDN inline below)
  function doChart(Chart) {
    _maplibStatsChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: hist.labels,
        datasets: [{
          data: displayCounts,
          backgroundColor: hist.colors,
          borderColor: hist.colors.map(function(c) { return c.replace(',0.82)', ',1)'); }),
          borderWidth: 1,
          borderRadius: 3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: hist.icons ? 46 : 22 } },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                var v = ctx.parsed.y;
                return axisLabel + ': ' + (_maplibStatsPrefs.pct ? v.toFixed(1) + '%' : v);
              }
            }
          },
        },
        scales: {
          x: {
            ticks: { font: { size: 10 }, maxRotation: 35, color: '#555' },
            grid: { display: false },
          },
          y: {
            ticks: { font: { size: 10 }, color: '#555' },
            grid: { color: '#f0f0f0' },
            title: { display: true, text: axisLabel, font: { size: 10 }, color: '#888' },
          }
        },
        animation: { duration: 300 },
      },
      plugins: [{
        // Draw the value above each bar; for marker_column-grouped bars,
        // also draw the icon once above that — but only when the icon is
        // actually a distinct symbol from the class's own text label (the
        // x-axis tick, from hist.labels), so a marker_column that already
        // holds emoji values (icon === label) doesn't get the same glyph
        // rendered twice.
        id: 'maplibBarLabels',
        afterDatasetsDraw: function(chart) {
          var ctx2 = chart.ctx;
          chart.data.datasets.forEach(function(dataset, i) {
            var meta = chart.getDatasetMeta(i);
            meta.data.forEach(function(bar, index) {
              var val = dataset.data[index];
              if (!val && val !== 0) return;
              var label = _maplibStatsPrefs.pct ? val.toFixed(1) + '%' : _fmt(val);
              var rawIcon = hist.icons && hist.icons[index];
              var icon = (rawIcon && rawIcon !== hist.labels[index]) ? rawIcon : null;
              ctx2.save();
              ctx2.textAlign = 'center';
              ctx2.textBaseline = 'bottom';
              var y = bar.y - 2;
              if (icon) {
                ctx2.font = '13px Segoe UI, Arial, sans-serif';
                ctx2.fillText(icon, bar.x, y);
                y -= 15;
              }
              ctx2.font = '600 10px Segoe UI, Arial, sans-serif';
              ctx2.fillStyle = '#333';
              ctx2.fillText(label, bar.x, y);
              ctx2.restore();
            });
          });
        }
      }]
    });
  }

  // Load Chart.js from CDN if not already loaded
  if (window.Chart) {
    doChart(window.Chart);
  } else {
    var script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
    script.onload = function() { doChart(window.Chart); };
    document.head.appendChild(script);
  }
}

/* ── Map switcher (merge_maps) ──────────────────────────────
   merge_maps() reparents every child (tile layers, GeoJson, FeatureGroups,
   …) from the secondary maps onto the first ("base") map, so at runtime
   every layer from every city actually lives on the same single Leaflet
   map instance (window[baseMapId]). Switching cities therefore never needs
   to look up a second Leaflet map object — it only needs to toggle which
   city's layers (by js_var) are attached to that one map, and rebuild the
   control panel / legends from that city's own layer metadata.        ── */

var _maplibSwitcher = null;

function _mapAllLayers(md) {
  return [].concat(md.bgLayers || [], md.rstLayers || [], md.vecLayers || []);
}

function _setMapLayersVisible(lmap, md, visible) {
  _mapAllLayers(md).forEach(function(l) {
    var ly = l.js_var && window[l.js_var];
    if (!ly) return;
    if (visible) { if (!lmap.hasLayer(ly)) lmap.addLayer(ly); }
    else { if (lmap.hasLayer(ly)) lmap.removeLayer(ly); }
  });
}

function maplibInitSwitcher(mapsData) {
  if (!mapsData || !mapsData.length) return;
  var baseMapId = mapsData[0].mapId;
  _maplibSwitcher = { baseMapId: baseMapId, currentId: baseMapId, mapsData: mapsData };
  var lmap = _getLeafletMap(baseMapId);
  if (!lmap) return;
  // Only the first (base) map's layers should be visible initially; every
  // other city's reparented layers must start hidden.
  for (var i = 1; i < mapsData.length; i++) {
    _setMapLayersVisible(lmap, mapsData[i], false);
  }
}

function maplibSwitchMap(selectedMapId) {
  var st = _maplibSwitcher;
  if (!st) return;
  var lmap = _getLeafletMap(st.baseMapId);
  if (!lmap || selectedMapId === st.currentId) return;

  var curData = st.mapsData.find(function(m) { return m.mapId === st.currentId; });
  var newData = st.mapsData.find(function(m) { return m.mapId === selectedMapId; });
  if (!newData) return;

  if (curData) _setMapLayersVisible(lmap, curData, false);
  _setMapLayersVisible(lmap, newData, true);
  st.currentId = selectedMapId;

  // Point the base map's control panel / legends at the newly-shown city.
  window._MAPLIB_DATA[st.baseMapId]    = newData;
  window._MAPLIB_LEGENDS[st.baseMapId] = (window._MAPLIB_LEGENDS || {})[selectedMapId] || {};
  _populateControls(st.baseMapId, newData);
  _applyInitialVisibility(lmap, newData, st.baseMapId);
  _enforceZOrder(lmap, newData);
  _refreshLegends(st.baseMapId);
  _updateStatsPanelLayers(st.baseMapId, newData);

  if (newData.center && newData.zoom) lmap.setView(newData.center, newData.zoom);
}