/* A small Web Mercator raster map renderer authored for this app.
 * The compatibility API keeps the companion HUD independent of the renderer.
 * All code is local; there is no third party JS bundle or external CDN request.
 */
(function () {
  'use strict';
  function point(ll, z) {
    var lat = Math.max(-85, Math.min(85, Number(ll[0]))) * Math.PI / 180;
    var n = 256 * Math.pow(2, z);
    return [(Number(ll[1]) + 180) / 360 * n, (1 - Math.log(Math.tan(lat) + 1 / Math.cos(lat)) / Math.PI) / 2 * n];
  }
  function unpoint(p, z) {
    var n = 256 * Math.pow(2, z);
    return [Math.atan(Math.sinh(Math.PI * (1 - 2 * p[1] / n))) * 180 / Math.PI, p[0] / n * 360 - 180];
  }
  function bounds(points) {
    var a = points.map(function (p) { return Number(p[0]); }), b = points.map(function (p) { return Number(p[1]); });
    var lo = [Math.min.apply(null, a), Math.min.apply(null, b)], hi = [Math.max.apply(null, a), Math.max.apply(null, b)];
    return { lo: lo, hi: hi, pad: function (k) {
      var d = [(hi[0] - lo[0]) * k, (hi[1] - lo[1]) * k];
      return bounds([[lo[0] - d[0], lo[1] - d[1]], [hi[0] + d[0], hi[1] + d[1]]]);
    } };
  }
  function MapView(id, opts) {
    this.el = document.getElementById(id); this.el.classList.add('leaflet-container');
    this.options = opts; this.center = [0.7, -0.7]; this.zoom = 11;
    this.min = opts.minZoom || 0; this.max = opts.maxZoom || 18;
    this.events = {}; this.layers = new Set(); this.tileLayer = null;
    this.tilePane = document.createElement('div'); this.tilePane.className = 'leaflet-tile-pane';
    this.markerPane = document.createElement('div'); this.markerPane.className = 'leaflet-marker-pane';
    this.el.append(this.tilePane, this.markerPane); this.pending = false;
    this.pointers = new window.Map(); this.drag = null; this.moved = false;
    var self = this;
    this.el.addEventListener('wheel', function (e) {
      e.preventDefault(); self.zoomAt(e.clientX, e.clientY, self.zoom + (e.deltaY < 0 ? 0.5 : -0.5));
    }, { passive: false });
    this.el.addEventListener('dblclick', function (e) { self.zoomAt(e.clientX, e.clientY, self.zoom + 1); });
    this.el.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.leaflet-marker-icon')) return;
      e.preventDefault(); self.el.setPointerCapture(e.pointerId);
      self.pointers.set(e.pointerId, [e.clientX, e.clientY]); self.startDrag();
    });
    this.el.addEventListener('pointermove', function (e) {
      if (!self.pointers.has(e.pointerId) || !self.drag) return;
      self.pointers.set(e.pointerId, [e.clientX, e.clientY]);
      var pts = Array.from(self.pointers.values()), d = self.drag;
      var mid = pts.length > 1 ? [(pts[0][0]+pts[1][0])/2, (pts[0][1]+pts[1][1])/2] : pts[0];
      var dx = mid[0] - d.mid[0], dy = mid[1] - d.mid[1];
      if (!self.moved && Math.hypot(dx,dy) > 3) { self.moved = true; self.emit('dragstart', e); }
      var zoom = d.zoom;
      if (pts.length > 1 && d.distance) zoom += Math.log2(Math.hypot(pts[0][0]-pts[1][0],pts[0][1]-pts[1][1]) / d.distance);
      self.zoom = Math.max(self.min, Math.min(self.max, zoom));
      var scale = Math.pow(2, self.zoom - d.zoom), cp = point(d.center, self.zoom);
      self.center = unpoint([cp[0]-dx*scale, cp[1]-dy*scale], self.zoom); self.draw();
    });
    function up(e) {
      if (!self.pointers.has(e.pointerId)) return;
      self.pointers.delete(e.pointerId);
      if (self.pointers.size) self.startDrag();
      else { self.drag = null; if (!self.moved) self.emit('click', e); }
    }
    this.el.addEventListener('pointerup', up); this.el.addEventListener('pointercancel', up);
  }
  MapView.prototype.startDrag = function () {
    var p = Array.from(this.pointers.values());
    this.drag = { center: this.center.slice(), zoom: this.zoom,
      mid: p.length > 1 ? [(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2] : p[0],
      distance: p.length > 1 ? Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]) : 0 };
    this.moved = false;
  };
  MapView.prototype.on = function (name, fn) { (this.events[name] || (this.events[name] = [])).push(fn); return this; };
  MapView.prototype.emit = function (name, ev) { (this.events[name] || []).forEach(function (fn) { fn(ev); }); };
  MapView.prototype.getZoom = function () { return this.zoom; };
  MapView.prototype.setMinZoom = function (v) { this.min = v; return this; };
  MapView.prototype.setMaxZoom = function (v) { this.max = v; return this; };
  MapView.prototype.setView = function (ll, z) {
    this.center = ll.slice(); this.zoom = Math.max(this.min, Math.min(this.max, z == null ? this.zoom : z));
    this.draw(); return this;
  };
  MapView.prototype.flyTo = MapView.prototype.setView;
  MapView.prototype.panTo = function (ll) { return this.setView(ll); };
  MapView.prototype.zoomIn = function () { return this.setView(this.center, this.zoom + 0.5); };
  MapView.prototype.zoomOut = function () { return this.setView(this.center, this.zoom - 0.5); };
  MapView.prototype.zoomAt = function (x, y, zoom) {
    var r = this.el.getBoundingClientRect(), old = point(this.center, this.zoom);
    var offset = [x-r.left-r.width/2,y-r.top-r.height/2];
    var ll = unpoint([old[0]+offset[0],old[1]+offset[1]],this.zoom);
    this.zoom = Math.max(this.min,Math.min(this.max,zoom)); var p = point(ll,this.zoom);
    this.center = unpoint([p[0]-offset[0],p[1]-offset[1]],this.zoom); this.draw();
  };
  MapView.prototype.fitBounds = function (b, opts) {
    if (Array.isArray(b)) b = bounds(b);
    if (!b || !b.lo || !b.hi || !b.lo.every(Number.isFinite) || !b.hi.every(Number.isFinite)) return this;
    opts = opts || {}; var tl = opts.paddingTopLeft || [30,30], br = opts.paddingBottomRight || [30,30];
    var p = point(b.lo,0), q = point(b.hi,0);
    var w = Math.max(100,this.el.clientWidth-tl[0]-br[0]), h = Math.max(100,this.el.clientHeight-tl[1]-br[1]);
    var z = Math.min(Math.log2(w/Math.max(Math.abs(q[0]-p[0]),1e-8)), Math.log2(h/Math.max(Math.abs(q[1]-p[1]),1e-8)));
    z = Math.max(this.min,Math.min(opts.maxZoom || this.max,this.max,Math.floor(z*2)/2));
    var scale = Math.pow(2,z);
    return this.setView(unpoint([(p[0]+q[0])*scale/2-(tl[0]-br[0])/2,(p[1]+q[1])*scale/2-(tl[1]-br[1])/2],z),z);
  };
  MapView.prototype.flyToBounds = MapView.prototype.fitBounds;
  MapView.prototype.invalidateSize = function () { this.draw(); return this; };
  MapView.prototype.hasLayer = function (layer) { return this.layers.has(layer); };
  MapView.prototype.removeLayer = function (layer) {
    this.layers.delete(layer); if (layer.el) layer.el.remove(); layer.map = null; this.draw(); return this;
  };
  MapView.prototype.draw = function () {
    if (this.pending) return; this.pending = true; var self = this;
    requestAnimationFrame(function () { self.pending = false; self.paint(); });
  };
  MapView.prototype.paint = function () {
    var self = this, w = this.el.clientWidth, h = this.el.clientHeight, c = point(this.center,this.zoom);
    if (this.tileLayer) {
      var layer = this.tileLayer, z = Math.min(Math.floor(this.zoom),layer.options.maxNativeZoom || 18);
      var size = 256*Math.pow(2,this.zoom-z), n = Math.pow(2,z);
      var left = c[0]-w/2, top = c[1]-h/2, needed = new Set();
      for (var x=Math.max(0,Math.floor(left/size));x<=Math.min(n-1,Math.floor((left+w)/size));x++) {
        for (var y=Math.max(0,Math.floor(top/size));y<=Math.min(n-1,Math.floor((top+h)/size));y++) {
          var key = z+'/'+x+'/'+y; needed.add(key); var img = layer.images.get(key);
          if (!img) {
            img = document.createElement('img'); img.className = 'leaflet-tile'; img.alt = ''; img.draggable = false;
            img.src = layer.url.replace('{z}',z).replace('{x}',x).replace('{y}',y);
            img.onerror = function () { this.hidden = true; };
            layer.images.set(key,img); this.tilePane.appendChild(img);
          }
          img.style.cssText = 'left:'+(x*size-left)+'px;top:'+(y*size-top)+'px;width:'+(size+0.5)+'px;height:'+(size+0.5)+'px';
        }
      }
      layer.images.forEach(function (img,key) { if (!needed.has(key)) { img.remove(); layer.images.delete(key); } });
    }
    this.layers.forEach(function (layer) {
      if (!layer.ll || !layer.el) return;
      var p = point(layer.ll,self.zoom), a = layer.icon.iconAnchor || [0,0];
      layer.el.style.left = (p[0]-c[0]+w/2-a[0])+'px'; layer.el.style.top = (p[1]-c[1]+h/2-a[1])+'px';
    });
  };
  function Tiles(url, opts) { this.url = url; this.options = opts || {}; this.images = new window.Map(); }
  Tiles.prototype.addTo = function (map) { this.map = map; map.tileLayer = this; map.draw(); return this; };
  Tiles.prototype.setUrl = function (url) { this.url = url; this.images.forEach(function (i) { i.remove(); }); this.images.clear(); this.map.draw(); return this; };
  function Group() { this.children = new Set(); }
  Group.prototype.addTo = function (map) { this.map = map; return this; };
  Group.prototype.clearLayers = function () { var map = this.map; this.children.forEach(function (c) { map.removeLayer(c); }); this.children.clear(); return this; };
  function Marker(ll, opts) { this.ll = ll; this.options = opts || {}; this.icon = this.options.icon || {}; this.handlers = {}; }
  Marker.prototype.addTo = function (target) {
    var map = target instanceof Group ? target.map : target; if (target instanceof Group) target.children.add(this);
    this.map = map; map.layers.add(this);
    if (!this.el) {
      this.el = document.createElement('div'); this.el.className = 'leaflet-marker-icon';
      var self = this;
      this.el.addEventListener('click', function (e) { e.stopPropagation(); if (self.handlers.click) self.handlers.click(e); });
    }
    this.setIcon(this.icon);
    if (this.label) {
      this.el.title = this.label; this.el.setAttribute('aria-label', this.label);
      this.el.onkeydown = function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.currentTarget.click(); } };
    }
    map.markerPane.appendChild(this.el); map.draw(); return this;
  };
  Marker.prototype.setIcon = function (icon) {
    this.icon = icon;
    if (this.el) {
      this.el.className = 'leaflet-marker-icon '+(icon.className || ''); this.el.innerHTML = icon.html || '';
      this.el.style.width = (icon.iconSize || [28,28])[0]+'px'; this.el.style.height = (icon.iconSize || [28,28])[1]+'px';
      this.el.style.zIndex = String(1000 + (this.options.zIndexOffset || 0));
      if (this.options.interactive === false) this.el.setAttribute('aria-hidden','true');
      else { this.el.tabIndex = 0; this.el.setAttribute('role','button'); }
    }
    if (this.map) this.map.draw(); return this;
  };
  Marker.prototype.bindTooltip = function (label) {
    // Decode the HUD's already escaped label as plain text for accessibility.
    var text = document.createElement('span'); text.innerHTML = label;
    this.label = text.textContent;
    return this;
  };
  Marker.prototype.on = function (event, fn) { this.handlers[event] = fn; return this; };
  Marker.prototype.getElement = function () { return this.el; };
  Marker.prototype.setLatLng = function (ll) { this.ll = ll; if (this.map) this.map.draw(); return this; };
  window.L = { map: function (id,o) { return new MapView(id,o); },
    tileLayer: function (url,o) { return new Tiles(url,o); }, layerGroup: function () { return new Group(); },
    marker: function (ll,o) { return new Marker(ll,o); }, divIcon: function (o) { return o; },
    latLngBounds: bounds, DomEvent: { stopPropagation: function (e) { e.stopPropagation(); } },
    _project: point, _unproject: unpoint };
})();
