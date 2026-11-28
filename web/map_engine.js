/* God of War Ragnarök — Pure WebGL2 3D Terrain Map Engine (Zero External Deps)
 * Drop-in compatible with the window.L subset used by companion_gow_map.js,
 * plus 3D camera controls (pitch/yaw/tilt/resetNorth), 16-bit heightmap relief,
 * additive 3D waypoint beacon, 3D Kratos trail, and 0-drift Google Maps multitouch.
 */
(function () {
  'use strict';

  var GRID = 384;
  var FOV_DEG = 40;
  var FOV_RAD = FOV_DEG * Math.PI / 180;
  var TAN_HALF_FOV = Math.tan(FOV_RAD * 0.5);
  var MAX_PITCH = 62;
  var WORLD_SPAN = 2048;
  var MAX_ATLAS_LAYERS = 255;
  var TILE_GRID_N = 16;

  function point(ll, z) {
    var lat = Math.max(-85, Math.min(85, Number(ll[0]))) * Math.PI / 180;
    var n = 256 * Math.pow(2, z);
    return [
      (Number(ll[1]) + 180) / 360 * n,
      (1 - Math.log(Math.tan(lat) + 1 / Math.cos(lat)) / Math.PI) / 2 * n
    ];
  }

  function unpoint(p, z) {
    var n = 256 * Math.pow(2, z);
    return [
      Math.atan(Math.sinh(Math.PI * (1 - 2 * p[1] / n))) * 180 / Math.PI,
      p[0] / n * 360 - 180
    ];
  }

  function bounds(points) {
    var a = points.map(function (p) { return Number(p[0]); });
    var b = points.map(function (p) { return Number(p[1]); });
    var lo = [Math.min.apply(null, a), Math.min.apply(null, b)];
    var hi = [Math.max.apply(null, a), Math.max.apply(null, b)];
    return {
      lo: lo,
      hi: hi,
      pad: function (k) {
        var d = [(hi[0] - lo[0]) * k, (hi[1] - lo[1]) * k];
        return bounds([[lo[0] - d[0], lo[1] - d[1]], [hi[0] + d[0], hi[1] + d[1]]]);
      }
    };
  }

  function hexToRgb01(hex, fallback) {
    if (typeof hex === 'string' && /^#[0-9a-f]{6}$/i.test(hex)) {
      return [
        parseInt(hex.slice(1, 3), 16) / 255,
        parseInt(hex.slice(3, 5), 16) / 255,
        parseInt(hex.slice(5, 7), 16) / 255
      ];
    }
    return fallback.slice();
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }

  function wrapDeg(rad) {
    var d = rad * 180 / Math.PI;
    while (d > 180) d -= 360;
    while (d < -180) d += 360;
    return d;
  }

  function mat4Perspective(fovRad, aspect, near, far) {
    var f = 1.0 / Math.tan(fovRad * 0.5);
    var nf = 1.0 / (near - far);
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (far + near) * nf, -1,
      0, 0, 2 * far * near * nf, 0
    ]);
  }

  function mat4Ortho(l, r, b, t, near, far) {
    var rl = 1.0 / (r - l);
    var tb = 1.0 / (t - b);
    var nf = 1.0 / (near - far);
    return new Float32Array([
      2 * rl, 0, 0, 0,
      0, 2 * tb, 0, 0,
      0, 0, 2 * nf, 0,
      -(r + l) * rl, -(t + b) * tb, (far + near) * nf, 1
    ]);
  }

  function mat4LookAt(ex, ey, ez, cx, cy, cz, ux, uy, uz) {
    var zx = ex - cx, zy = ey - cy, zz = ez - cz;
    var zl = Math.hypot(zx, zy, zz) || 1;
    zx /= zl; zy /= zl; zz /= zl;
    var xx = uy * zz - uz * zy, xy = uz * zx - ux * zz, xz = ux * zy - uy * zx;
    var xl = Math.hypot(xx, xy, xz) || 1;
    xx /= xl; xy /= xl; xz /= xl;
    var yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
    return new Float32Array([
      xx, yx, zx, 0,
      xy, yy, zy, 0,
      xz, yz, zz, 0,
      -(xx * ex + xy * ey + xz * ez),
      -(yx * ex + yy * ey + yz * ez),
      -(zx * ex + zy * ey + zz * ez),
      1
    ]);
  }

  function mat4Mul(a, b) {
    var out = new Float32Array(16);
    for (var c = 0; c < 4; c++) {
      var b0 = b[c * 4], b1 = b[c * 4 + 1], b2 = b[c * 4 + 2], b3 = b[c * 4 + 3];
      out[c * 4]     = a[0] * b0 + a[4] * b1 + a[8]  * b2 + a[12] * b3;
      out[c * 4 + 1] = a[1] * b0 + a[5] * b1 + a[9]  * b2 + a[13] * b3;
      out[c * 4 + 2] = a[2] * b0 + a[6] * b1 + a[10] * b2 + a[14] * b3;
      out[c * 4 + 3] = a[3] * b0 + a[7] * b1 + a[11] * b2 + a[15] * b3;
    }
    return out;
  }

  function mat4Invert(m) {
    var inv = new Float32Array(16);
    var m00 = m[0], m01 = m[1], m02 = m[2], m03 = m[3];
    var m10 = m[4], m11 = m[5], m12 = m[6], m13 = m[7];
    var m20 = m[8], m21 = m[9], m22 = m[10], m23 = m[11];
    var m30 = m[12], m31 = m[13], m32 = m[14], m33 = m[15];
    var b00 = m00 * m11 - m01 * m10, b01 = m00 * m12 - m02 * m10, b02 = m00 * m13 - m03 * m10;
    var b03 = m01 * m12 - m02 * m11, b04 = m01 * m13 - m03 * m11, b05 = m02 * m13 - m03 * m12;
    var b06 = m20 * m31 - m21 * m30, b07 = m20 * m32 - m22 * m30, b08 = m20 * m33 - m23 * m30;
    var b09 = m21 * m32 - m22 * m31, b10 = m21 * m33 - m23 * m31, b11 = m22 * m33 - m23 * m32;
    var det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06;
    if (Math.abs(det) < 1e-12) return null;
    det = 1.0 / det;
    inv[0]  = (m11 * b11 - m12 * b10 + m13 * b09) * det;
    inv[1]  = (m02 * b10 - m01 * b11 - m03 * b09) * det;
    inv[2]  = (m31 * b05 - m32 * b04 + m33 * b03) * det;
    inv[3]  = (m22 * b04 - m21 * b05 - m23 * b03) * det;
    inv[4]  = (m12 * b08 - m10 * b11 - m13 * b07) * det;
    inv[5]  = (m00 * b11 - m02 * b08 + m03 * b07) * det;
    inv[6]  = (m32 * b02 - m30 * b05 - m33 * b01) * det;
    inv[7]  = (m20 * b05 - m22 * b02 + m23 * b01) * det;
    inv[8]  = (m10 * b10 - m11 * b08 + m13 * b06) * det;
    inv[9]  = (m01 * b08 - m00 * b10 - m03 * b06) * det;
    inv[10] = (m30 * b04 - m31 * b02 + m33 * b00) * det;
    inv[11] = (m21 * b02 - m20 * b04 - m23 * b00) * det;
    inv[12] = (m11 * b07 - m10 * b09 - m12 * b06) * det;
    inv[13] = (m00 * b09 - m01 * b07 + m02 * b06) * det;
    inv[14] = (m31 * b01 - m30 * b03 - m32 * b00) * det;
    inv[15] = (m20 * b03 - m21 * b01 + m22 * b00) * det;
    return inv;
  }

  // ══════════ GLSL SHADERS (GoWR Obsidian & Gold Carved Relief) ══════════
  var TERRAIN_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp sampler2D;\n' +
    'in vec2 aUv;\n' +
    'uniform mat4 uVP;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform float uHeightAmp;\n' +
    'uniform float uHasHeight;\n' +
    'uniform sampler2D uHeightTex;\n' +
    'out vec2 vUv;\n' +
    'out vec3 vWorldPos;\n' +
    'out float vHeight01;\n' +
    'out float vValid;\n' +
    'float decodeH(vec3 c) { return (c.r * 256.0 + c.g) / 257.0; }\n' +
    'vec2 sampleH16(vec2 uv) {\n' +
    '  vec2 sz = vec2(textureSize(uHeightTex, 0));\n' +
    '  vec2 p = clamp(uv, 0.0, 1.0) * (sz - 1.0);\n' +
    '  ivec2 i0 = ivec2(floor(p));\n' +
    '  ivec2 i1 = min(i0 + ivec2(1), ivec2(sz) - ivec2(1));\n' +
    '  vec2 f = p - vec2(i0);\n' +
    '  vec3 c00 = texelFetch(uHeightTex, i0, 0).rgb;\n' +
    '  vec3 c10 = texelFetch(uHeightTex, ivec2(i1.x, i0.y), 0).rgb;\n' +
    '  vec3 c01 = texelFetch(uHeightTex, ivec2(i0.x, i1.y), 0).rgb;\n' +
    '  vec3 c11 = texelFetch(uHeightTex, i1, 0).rgb;\n' +
    '  float h = mix(mix(decodeH(c00), decodeH(c10), f.x), mix(decodeH(c01), decodeH(c11), f.x), f.y);\n' +
    '  float m = mix(mix(c00.b, c10.b, f.x), mix(c01.b, c11.b, f.x), f.y);\n' +
    '  return vec2(h, m);\n' +
    '}\n' +
    'void main() {\n' +
    '  vUv = aUv;\n' +
    '  float h01 = 0.0;\n' +
    '  float valid = 1.0;\n' +
    '  if (uHasHeight > 0.5) {\n' +
    '    vec2 hm = sampleH16(aUv);\n' +
    '    float edge = smoothstep(0.0, 0.03, aUv.x) * smoothstep(1.0, 0.97, aUv.x) *\n' +
    '                 smoothstep(0.0, 0.03, aUv.y) * smoothstep(1.0, 0.97, aUv.y);\n' +
    '    valid = hm.y;\n' +
    '    h01 = hm.x * edge;\n' +
    '  }\n' +
    '  float y = h01 * uHeightAmp;\n' +
    '  vec3 wp = vec3(aUv.x * uWorldSize.x, y, aUv.y * uWorldSize.y);\n' +
    '  vWorldPos = wp;\n' +
    '  vHeight01 = h01;\n' +
    '  vValid = valid;\n' +
    '  gl_Position = uVP * vec4(wp, 1.0);\n' +
    '}\n';

  var TERRAIN_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp sampler2D;\n' +
    'precision highp sampler2DArray;\n' +
    'in vec2 vUv;\n' +
    'in vec3 vWorldPos;\n' +
    'in float vHeight01;\n' +
    'in float vValid;\n' +
    'uniform sampler2D uHeightTex;\n' +
    'uniform sampler2DArray uTileAtlas;\n' +
    'uniform sampler2D uTileGrid;\n' +
    'uniform sampler2D uFallbackGrid;\n' +
    'uniform sampler2D uDetailNormTex;\n' +
    'uniform sampler2D uDetailNoiseTex;\n' +
    'uniform sampler2D uIceCracksTex;\n' +
    'uniform sampler2D uNativeSurfaceTex;\n' +
    'uniform sampler2D uTerrainNormTex;\n' +
    'uniform sampler2D uWaterMaskTex;\n' +
    'uniform sampler2D uFlowTex;\n' +
    'uniform sampler2D uShadowMap;\n' +
    'uniform mat4 uLightVP;\n' +
    'uniform float uShadowRes;\n' +
    'uniform float uHasTerrainNorm;\n' +
    'uniform float uHasWaterMask;\n' +
    'uniform float uHasShadowMap;\n' +
    'uniform float uIsLava;\n' +
    'uniform float uUseNativeSurface;\n' +
    'uniform float uHasDetail;\n' +
    'uniform float uIsIcy;\n' +
    'uniform vec4 uMerc0;\n' +        // x_min, y_min, x_max, y_max
    'uniform vec4 uGridMain;\n' +     // tx0, ty0, pow2z, gridN
    'uniform vec4 uGridBack;\n' +     // tx0, ty0, pow2z, gridN
    'uniform vec2 uWorldSize;\n' +
    'uniform float uHeightAmp;\n' +
    'uniform float uHasHeight;\n' +
    'uniform float uHasTiles;\n' +
    'uniform float uMode3D;\n' +
    'uniform float uTime;\n' +
    'uniform vec3 uKeyColor;\n' +
    'uniform vec3 uRimColor;\n' +
    'uniform vec3 uAmbientColor;\n' +
    'uniform vec3 uWaterColor;\n' +
    'uniform vec3 uFogColor;\n' +
    'uniform vec3 uBgColor;\n' +
    'uniform vec3 uCamPos;\n' +
    'out vec4 fragColor;\n' +
    'float decodeH(vec3 c) { return (c.r * 256.0 + c.g) / 257.0; }\n' +
    'float sampleH(vec2 uv) {\n' +
    '  vec2 sz = vec2(textureSize(uHeightTex, 0));\n' +
    '  vec2 p = clamp(uv, 0.0, 1.0) * (sz - 1.0);\n' +
    '  ivec2 i0 = ivec2(floor(p));\n' +
    '  ivec2 i1 = min(i0 + ivec2(1), ivec2(sz) - ivec2(1));\n' +
    '  vec2 f = p - vec2(i0);\n' +
    '  vec3 c00 = texelFetch(uHeightTex, i0, 0).rgb;\n' +
    '  vec3 c10 = texelFetch(uHeightTex, ivec2(i1.x, i0.y), 0).rgb;\n' +
    '  vec3 c01 = texelFetch(uHeightTex, ivec2(i0.x, i1.y), 0).rgb;\n' +
    '  vec3 c11 = texelFetch(uHeightTex, i1, 0).rgb;\n' +
    '  float h = mix(mix(decodeH(c00), decodeH(c10), f.x), mix(decodeH(c01), decodeH(c11), f.x), f.y);\n' +
    '  return h;\n' +
    '}\n' +
    'vec4 sampleGrid(vec2 merc0, vec4 gp, sampler2D gridTex) {\n' +
    '  float scale = gp.z / 256.0;\n' +
    '  vec2 tc = merc0 * scale;\n' +
    '  vec2 ddx = dFdx(tc) * 0.50;\n' +
    '  vec2 ddy = dFdy(tc) * 0.50;\n' +
    '  vec2 tile = floor(tc);\n' +
    '  vec2 sub = fract(tc);\n' +
    '  vec2 gcoord = (tile - gp.xy + 0.5) / gp.w;\n' +
    '  if (gcoord.x < 0.0 || gcoord.x > 1.0 || gcoord.y < 0.0 || gcoord.y > 1.0) return vec4(0.0);\n' +
    '  float idx = floor(texture(gridTex, gcoord).r * 255.0 + 0.5);\n' +
    '  if (idx < 0.5) return vec4(0.0);\n' +
    '  float layer = idx - 1.0;\n' +
    '  vec4 c = textureGrad(uTileAtlas, vec3(sub, layer), ddx, ddy);\n' +
    '  // Contrast-Adaptive Sharpening (CAS) inside tile bounds to keep landmarks, roads & cliffs razor-sharp\n' +
    '  float texel = 1.0 / 256.0;\n' +
    '  vec2 sMin = vec2(0.004);\n' +
    '  vec2 sMax = vec2(0.996);\n' +
    '  vec3 nL = textureGrad(uTileAtlas, vec3(clamp(sub - vec2(texel, 0.0), sMin, sMax), layer), ddx, ddy).rgb;\n' +
    '  vec3 nR = textureGrad(uTileAtlas, vec3(clamp(sub + vec2(texel, 0.0), sMin, sMax), layer), ddx, ddy).rgb;\n' +
    '  vec3 nD = textureGrad(uTileAtlas, vec3(clamp(sub - vec2(0.0, texel), sMin, sMax), layer), ddx, ddy).rgb;\n' +
    '  vec3 nU = textureGrad(uTileAtlas, vec3(clamp(sub + vec2(0.0, texel), sMin, sMax), layer), ddx, ddy).rgb;\n' +
    '  vec3 mn = min(c.rgb, min(min(nL, nR), min(nD, nU)));\n' +
    '  vec3 mx = max(c.rgb, max(max(nL, nR), max(nD, nU)));\n' +
    '  vec3 blur = 0.25 * (nL + nR + nD + nU);\n' +
    '  vec3 sharp = clamp(c.rgb + (c.rgb - blur) * 0.90, mn * 0.90, min(vec3(1.0), mx * 1.07));\n' +
    '  return vec4(sharp, c.a);\n' +
    '}\n' +
    'vec3 acesFilm(vec3 x) {\n' +
    '  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);\n' +
    '}\n' +
    'float sampleShadowPCF(vec3 wp, vec3 N, vec3 L) {\n' +
    '  if (uHasShadowMap < 0.5) return 1.0;\n' +
    '  vec4 lp = uLightVP * vec4(wp, 1.0);\n' +
    '  vec3 proj = lp.xyz / max(lp.w, 1e-5) * 0.5 + 0.5;\n' +
    '  if (proj.x <= 0.002 || proj.x >= 0.998 || proj.y <= 0.002 || proj.y >= 0.998 || proj.z >= 0.999) return 1.0;\n' +
    '  float bias = max(0.0018, 0.0045 * (1.0 - max(dot(N, L), 0.0)));\n' +
    '  float ts = 1.0 / max(256.0, uShadowRes);\n' +
    '  float lit = 0.0;\n' +
    '  for (int dy = -1; dy <= 1; dy++) {\n' +
    '    for (int dx = -1; dx <= 1; dx++) {\n' +
    '      float d = texture(uShadowMap, proj.xy + vec2(float(dx), float(dy)) * ts * 1.45).r;\n' +
    '      lit += (proj.z - bias <= d) ? 1.0 : 0.0;\n' +
    '    }\n' +
    '  }\n' +
    '  return mix(0.42, 1.0, lit / 9.0);\n' +
    '}\n' +
    'void main() {\n' +
    '  vec2 merc0 = mix(uMerc0.xy, uMerc0.zw, vUv);\n' +
    '  vec4 tileCol = vec4(0.0);\n' +
    '  if (uUseNativeSurface > 0.5) {\n' +
    '    tileCol = vec4(texture(uNativeSurfaceTex, vUv).rgb, 1.0);\n' +
    '  } else if (uHasTiles > 0.5) {\n' +
    '    tileCol = sampleGrid(merc0, uGridMain, uTileGrid);\n' +
    '    if (tileCol.a < 0.96) {\n' +
    '      vec4 backCol = sampleGrid(merc0, uGridBack, uFallbackGrid);\n' +
    '      tileCol = mix(backCol, tileCol, clamp(tileCol.a * 1.15, 0.0, 1.0));\n' +
    '    }\n' +
    '  }\n' +
    '  vec3 N = vec3(0.0, 1.0, 0.0);\n' +
    '  float ao = 1.0;\n' +
    '  float rayShadow = 1.0;\n' +
    '  float crest = 0.0;\n' +
    '  float lap = 0.0;\n' +
    '  if (uUseNativeSurface > 0.5 && uHasTerrainNorm > 0.5) {\n' +
    '    vec4 tn = texture(uTerrainNormTex, vUv);\n' +
    '    vec3 rawN = tn.rgb * 2.0 - 1.0;\n' +
    '    N = length(rawN) > 1e-4 ? normalize(rawN) : vec3(0.0, 1.0, 0.0);\n' +
    '    rayShadow = tn.a;\n' +
    '    ao = mix(0.68, 1.06, rayShadow);\n' +
    '    crest = clamp((rayShadow - 0.88) * 2.2, 0.0, 0.28);\n' +
    '  } else if (uHasHeight > 0.5) {\n' +
    '    float eps = 1.0 / max(256.0, float(textureSize(uHeightTex, 0).x));\n' +
    '    float hL = sampleH(vUv - vec2(eps, 0.0));\n' +
    '    float hR = sampleH(vUv + vec2(eps, 0.0));\n' +
    '    float hD = sampleH(vUv - vec2(0.0, eps));\n' +
    '    float hU = sampleH(vUv + vec2(0.0, eps));\n' +
    '    float dx = (hR - hL) * uHeightAmp;\n' +
    '    float dz = (hU - hD) * uHeightAmp;\n' +
    '    float stepX = 2.0 * eps * uWorldSize.x;\n' +
    '    float stepZ = 2.0 * eps * uWorldSize.y;\n' +
    '    N = normalize(vec3(-dx / stepX, 1.0, -dz / stepZ));\n' +
    '    lap = vHeight01 - 0.25 * (hL + hR + hD + hU);\n' +
    '    ao = clamp(0.89 + lap * 6.8, 0.46, 1.14);\n' +
    '    crest = clamp(lap * 8.2, 0.0, 0.38);\n' +
    '  } else if (tileCol.a > 0.04) {\n' +
    '    float lum = dot(tileCol.rgb, vec3(0.299, 0.587, 0.114));\n' +
    '    float gx = clamp(dFdx(lum), -0.055, 0.055);\n' +
    '    float gz = clamp(dFdy(lum), -0.055, 0.055);\n' +
    '    N = normalize(vec3(-gx * 4.2, 1.0, -gz * 4.2));\n' +
    '  }\n' +
    '  vec3 wm = (uUseNativeSurface > 0.5 && uHasWaterMask > 0.5) ? texture(uWaterMaskTex, vUv).rgb : vec3(0.0, 0.0, 0.14);\n' +
    '  float waterMask = wm.r;\n' +
    '  float glowMask = wm.g;\n' +
    '  float surfGloss = wm.b;\n' +
    '  float microGrain = 0.0;\n' +
    '  float iceCrack = 0.0;\n' +
    '  if (uHasDetail > 0.5) {\n' +
    '    vec2 dUv1 = vUv * 22.0;\n' +
    '    vec2 dUv2 = vUv * 68.0;\n' +
    '    vec3 dn1 = texture(uDetailNormTex, dUv1).rgb * 2.0 - 1.0;\n' +
    '    vec3 dn2 = texture(uDetailNormTex, dUv2).rgb * 2.0 - 1.0;\n' +
    '    float detailAmp = mix(0.14, 0.30, clamp(1.0 - N.y, 0.0, 1.0) * 2.2) * (1.0 - waterMask * 0.85);\n' +
    '    vec2 dn = (dn1.xy * 0.62 + dn2.xy * 0.58) * detailAmp;\n' +
    '    N = normalize(vec3(N.x + dn.x, N.y, N.z + dn.y));\n' +
    '    float g1 = texture(uDetailNoiseTex, dUv1).r - 0.5;\n' +
    '    float g2 = texture(uDetailNoiseTex, dUv2).r - 0.5;\n' +
    '    microGrain = (g1 * 0.55 + g2 * 0.45);\n' +
    '    if (uIsIcy > 0.5) {\n' +
    '      float ic1 = texture(uIceCracksTex, vUv * 19.0).r;\n' +
    '      float ic2 = texture(uIceCracksTex, vUv * 43.0 + vec2(0.37, 0.61)).r;\n' +
    '      iceCrack = max(ic1, ic2 * 0.7);\n' +
    '    }\n' +
    '  }\n' +
    '  // Animated real-game TX_flowmap_02 ripples for rivers, seas, icy pools & molten lava\n' +
    '  vec2 flow = (texture(uFlowTex, vUv * 5.0).rg * 2.0 - 1.0);\n' +
    '  float ph0 = fract(uTime * 0.16);\n' +
    '  float ph1 = fract(uTime * 0.16 + 0.5);\n' +
    '  float flowMix = abs(2.0 * ph0 - 1.0);\n' +
    '  if (waterMask > 0.04) {\n' +
    '    vec2 wN0 = texture(uDetailNormTex, vUv * 18.0 + flow * ph0 * 0.18).rg * 2.0 - 1.0;\n' +
    '    vec2 wN1 = texture(uDetailNormTex, vUv * 18.0 + flow * ph1 * 0.18 + vec2(0.37, 0.61)).rg * 2.0 - 1.0;\n' +
    '    vec2 wRipple = mix(wN0, wN1, flowMix) * (0.24 * waterMask);\n' +
    '    N = normalize(vec3(N.x + wRipple.x, N.y, N.z + wRipple.y));\n' +
    '  }\n' +
    '  vec3 Lkey = normalize(vec3(-0.52, 0.74, -0.42));\n' +
    '  vec3 Lrim = normalize(vec3(0.62, 0.38, 0.68));\n' +
    '  vec3 V = normalize(uCamPos - vWorldPos);\n' +
    '  float diffKey = max(dot(N, Lkey), 0.0);\n' +
    '  float diffRim = max(dot(N, Lrim), 0.0);\n' +
    '  float slope = 1.0 - clamp(N.y, 0.0, 1.0);\n' +
    '  vec3 H = normalize(Lkey + V);\n' +
    '  float tileLum = dot(tileCol.rgb, vec3(0.299, 0.587, 0.114));\n' +
    '  float snowMask = smoothstep(0.50, 0.85, tileLum) * (1.0 - slope * 1.4) * (1.0 - waterMask);\n' +
    '  float propShadow = (uUseNativeSurface > 0.5) ? sampleShadowPCF(vWorldPos, N, Lkey) : 1.0;\n' +
    '  float sunVis = (uUseNativeSurface > 0.5 && uHasTerrainNorm > 0.5) ? min(rayShadow, propShadow) : propShadow;\n' +
    '  float reliefFactor = mix(0.26, 1.0, uMode3D);\n' +
    '  float shininess = mix(22.0, 88.0, max(surfGloss, waterMask));\n' +
    '  float fresnel = pow(clamp(1.0 - max(dot(N, V), 0.0), 1e-4, 1.0), 3.6);\n' +
    '  float spec = pow(max(dot(N, H), 1e-4), shininess) * ((0.08 + 0.14 * snowMask + 0.62 * waterMask) * sunVis * reliefFactor);\n' +
    '  // Authentic PS5/PC carved-wood diorama lighting: cool crisp sky ambient in shadows + bright directional sun\n' +
    '  vec3 skyAmb = uAmbientColor * mix(0.68, 0.92, clamp(N.y, 0.0, 1.0)) * mix(0.76, 1.04, rayShadow);\n' +
    '  vec3 sunLit = uKeyColor * (diffKey * 0.98 * sunVis);\n' +
    '  vec3 rimLit = uRimColor * (diffRim * (0.20 + crest * 0.55) * mix(0.45, 1.0, rayShadow));\n' +
    '  vec3 rawLight = skyAmb + sunLit + rimLit;\n' +
    '  vec3 light = mix(vec3(1.05), rawLight, reliefFactor);\n' +
    '  // Unified carved floor grid matching outer floor quad\n' +
    '  vec2 gMain = abs(fract(vWorldPos.xz / 256.0 - 0.5) - 0.5) / max(fwidth(vWorldPos.xz / 256.0), vec2(0.001));\n' +
    '  vec2 gSub = abs(fract(vWorldPos.xz / 64.0 - 0.5) - 0.5) / max(fwidth(vWorldPos.xz / 64.0), vec2(0.001));\n' +
    '  float lineMain = 1.0 - min(min(gMain.x, gMain.y), 1.0);\n' +
    '  float lineSub = 1.0 - min(min(gSub.x, gSub.y), 1.0);\n' +
    '  float radVoid = length((vUv - 0.5) * 1.4);\n' +
    '  float voidFade = clamp(1.0 - radVoid * 0.85, 0.0, 1.0);\n' +
    '  vec3 voidCol = uBgColor + uKeyColor * ((lineMain * 0.06 + lineSub * 0.018) * voidFade);\n' +
    '  vec3 hypsoCol = mix(uWaterColor * 1.3 + uAmbientColor * 0.45, mix(uAmbientColor * 1.45, uKeyColor * 0.65, smoothstep(0.28, 0.88, vHeight01)), smoothstep(0.03, 0.45, vHeight01));\n' +
    '  vec2 edgeD = (vUv - vec2(0.5)) * 2.0;\n' +
    '  float edgeFade = 1.0 - smoothstep(0.68, 0.97, max(abs(edgeD.x), abs(edgeD.y)));\n' +
    '  float stonePresence = step(0.5, uHasHeight) * step(0.2, vValid) * smoothstep(0.015, 0.085, vHeight01 + abs(lap) * 2.5) * edgeFade;\n' +
    '  vec3 baseSurface = mix(voidCol, hypsoCol * light + uKeyColor * (crest * 0.14 * reliefFactor), stonePresence * 0.9);\n' +
    '  // Crisp albedo + fine micro-grain + TRUE LINEAR PBR lighting -> ACES filmic -> sRGB gamma!\n' +
    '  float grainAmp = mix(0.10, 0.040, uUseNativeSurface);\n' +
    '  vec3 cleanTile = clamp(tileCol.rgb + vec3(microGrain * grainAmp), 0.0, 1.0);\n' +
    '  cleanTile = mix(cleanTile, cleanTile * vec3(0.88, 0.95, 1.02) + vec3(0.05, 0.10, 0.15), iceCrack * snowMask * mix(0.26, 0.12, uUseNativeSurface));\n' +
    '  vec3 landRgb;\n' +
    '  if (uUseNativeSurface > 0.5) {\n' +
    '    vec3 linAlb = pow(max(cleanTile, vec3(1e-4)), vec3(2.2));\n' +
    '    vec3 linAmb = pow(max(uAmbientColor, vec3(1e-4)), vec3(2.2));\n' +
    '    vec3 linKey = pow(max(uKeyColor, vec3(1e-4)), vec3(2.2));\n' +
    '    vec3 linRim = pow(max(uRimColor, vec3(1e-4)), vec3(2.2));\n' +
    '    vec3 lSky = linAmb * mix(0.46, 0.95, clamp(N.y, 0.0, 1.0)) * mix(0.55, 1.08, rayShadow);\n' +
    '    vec3 lSun = linKey * (diffKey * 1.68 * sunVis);\n' +
    '    vec3 lRim = linRim * (diffRim * (0.22 + crest * 0.50) * mix(0.35, 1.0, rayShadow));\n' +
    '    vec3 linLight = mix(vec3(1.15), lSky + lSun + lRim, reliefFactor);\n' +
    '    vec3 hdrLand = linAlb * linLight + mix(linKey, vec3(1.0), 0.55) * (spec * 1.25);\n' +
    '    hdrLand += mix(linRim, vec3(0.76, 0.90, 1.0), 0.50) * (fresnel * waterMask * 0.52 * reliefFactor);\n' +
    '    if (glowMask > 0.04) {\n' +
    '      float pulse = 0.88 + 0.16 * sin(uTime * 2.1 + flow.x * 6.0 + flow.y * 5.0);\n' +
    '      vec3 emLin = (uIsLava > 0.5) ? vec3(2.80, 0.52, 0.05) : vec3(0.12, 0.52, 0.78);\n' +
    '      hdrLand += emLin * (glowMask * pulse * (uIsLava > 0.5 ? 1.15 : 0.28));\n' +
    '    }\n' +
    '    landRgb = pow(max(acesFilm(hdrLand * 0.92), vec3(1e-5)), vec3(1.0 / 2.2));\n' +
    '  } else {\n' +
    '    vec3 hdrLand = cleanTile * light + mix(uKeyColor, vec3(1.0), 0.48) * spec;\n' +
    '    landRgb = hdrLand / (vec3(1.0) + max(hdrLand - vec3(0.88), vec3(0.0)) * 0.82);\n' +
    '  }\n' +
    '  float landMix = smoothstep(0.04, 0.35, tileCol.a);\n' +
    '  vec3 col = mix(baseSurface, landRgb, landMix);\n' +
    '  // Aerial perspective + soft rounded squircle table vignette\n' +
    '  float worldSpan = max(uWorldSize.x, uWorldSize.y);\n' +
    '  float distCam = length(uCamPos - vWorldPos);\n' +
    '  float distFog = smoothstep(worldSpan * 1.35, worldSpan * 3.1, distCam) * 0.16;\n' +
    '  col = mix(col, uFogColor, clamp(distFog * uMode3D, 0.0, 0.22));\n' +
    '  float boxD = max(abs(edgeD.x), abs(edgeD.y));\n' +
    '  float radD = length(edgeD) * 0.80;\n' +
    '  float vig = smoothstep(0.66, 0.975, max(boxD, radD));\n' +
    '  col = mix(col, uBgColor, vig);\n' +
    '  fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);\n' +
    '}\n';

  var SHADOW_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec3 aPos;\n' +
    'in vec2 aUv;\n' +
    'uniform mat4 uLightVP;\n' +
    'uniform float uMode3D;\n' +
    'out vec2 vUv;\n' +
    'void main() {\n' +
    '  vUv = aUv;\n' +
    '  vec3 wp = vec3(aPos.x, aPos.y * mix(0.35, 1.0, uMode3D) + 0.6, aPos.z);\n' +
    '  gl_Position = uLightVP * vec4(wp, 1.0);\n' +
    '}\n';

  var SHADOW_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp sampler2D;\n' +
    'in vec2 vUv;\n' +
    'uniform sampler2D uAtlasTex;\n' +
    'void main() {\n' +
    '  if (texture(uAtlasTex, vUv).a < 0.42) discard;\n' +
    '}\n';

  var PROPS_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec3 aPos;\n' +
    'in vec3 aNorm;\n' +
    'in vec2 aUv;\n' +
    'uniform mat4 uVP;\n' +
    'uniform float uMode3D;\n' +
    'out vec3 vWorldPos;\n' +
    'out vec3 vNorm;\n' +
    'out vec2 vUv;\n' +
    'void main() {\n' +
    '  vec3 wp = vec3(aPos.x, aPos.y * mix(0.35, 1.0, uMode3D) + 0.6, aPos.z);\n' +
    '  vWorldPos = wp;\n' +
    '  vNorm = aNorm;\n' +
    '  vUv = aUv;\n' +
    '  gl_Position = uVP * vec4(wp, 1.0);\n' +
    '}\n';

  var PROPS_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp sampler2D;\n' +
    'in vec3 vWorldPos;\n' +
    'in vec3 vNorm;\n' +
    'in vec2 vUv;\n' +
    'uniform sampler2D uAtlasTex;\n' +
    'uniform sampler2D uNormAtlasTex;\n' +
    'uniform sampler2D uShadowMap;\n' +
    'uniform mat4 uLightVP;\n' +
    'uniform float uShadowRes;\n' +
    'uniform float uHasNormAtlas;\n' +
    'uniform float uHasShadowMap;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform vec3 uKeyColor;\n' +
    'uniform vec3 uRimColor;\n' +
    'uniform vec3 uAmbientColor;\n' +
    'uniform vec3 uFogColor;\n' +
    'uniform vec3 uBgColor;\n' +
    'uniform vec3 uCamPos;\n' +
    'uniform float uMode3D;\n' +
    'out vec4 fragColor;\n' +
    'vec3 acesFilm(vec3 x) {\n' +
    '  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);\n' +
    '}\n' +
    'vec3 perturbNormal(vec3 N, vec3 p, vec2 uv, vec3 mapN) {\n' +
    '  vec3 dp1 = dFdx(p);\n' +
    '  vec3 dp2 = dFdy(p);\n' +
    '  vec2 duv1 = dFdx(uv);\n' +
    '  vec2 duv2 = dFdy(uv);\n' +
    '  vec3 dp2perp = cross(dp2, N);\n' +
    '  vec3 dp1perp = cross(N, dp1);\n' +
    '  vec3 T = dp2perp * duv1.x + dp1perp * duv2.x;\n' +
    '  vec3 B = dp2perp * duv1.y + dp1perp * duv2.y;\n' +
    '  float invmax = inversesqrt(max(dot(T, T), dot(B, B)) + 1e-8);\n' +
    '  mat3 TBN = mat3(T * invmax, B * invmax, N);\n' +
    '  return normalize(TBN * mapN);\n' +
    '}\n' +
    'float samplePropShadow(vec3 wp, vec3 N, vec3 L) {\n' +
    '  if (uHasShadowMap < 0.5) return 1.0;\n' +
    '  vec4 lp = uLightVP * vec4(wp, 1.0);\n' +
    '  vec3 proj = lp.xyz / max(lp.w, 1e-5) * 0.5 + 0.5;\n' +
    '  if (proj.x <= 0.002 || proj.x >= 0.998 || proj.y <= 0.002 || proj.y >= 0.998 || proj.z >= 0.999) return 1.0;\n' +
    '  float bias = max(0.0028, 0.0065 * (1.0 - max(dot(N, L), 0.0)));\n' +
    '  float ts = 1.0 / max(256.0, uShadowRes);\n' +
    '  float lit = 0.0;\n' +
    '  for (int dy = -1; dy <= 1; dy++) {\n' +
    '    for (int dx = -1; dx <= 1; dx++) {\n' +
    '      float d = texture(uShadowMap, proj.xy + vec2(float(dx), float(dy)) * ts * 1.25).r;\n' +
    '      lit += (proj.z - bias <= d) ? 1.0 : 0.0;\n' +
    '    }\n' +
    '  }\n' +
    '  return mix(0.48, 1.0, lit / 9.0);\n' +
    '}\n' +
    'void main() {\n' +
    '  vec4 baseTex = texture(uAtlasTex, vUv);\n' +
    '  if (baseTex.a < 0.42) discard;\n' +
    '  vec3 baseCol = baseTex.rgb;\n' +
    '  vec3 N = length(vNorm) > 1e-4 ? normalize(vNorm) : vec3(0.0, 1.0, 0.0);\n' +
    '  if (!gl_FrontFacing) N = -N;\n' +
    '  float mapGloss = 0.40;\n' +
    '  if (uHasNormAtlas > 0.5) {\n' +
    '    vec4 ng = texture(uNormAtlasTex, vUv);\n' +
    '    vec3 mapN = ng.rgb * 2.0 - 1.0;\n' +
    '    mapN.xy *= 0.92;\n' +
    '    if (dot(mapN, mapN) > 0.1) {\n' +
    '      N = perturbNormal(N, vWorldPos, vUv, normalize(mapN));\n' +
    '    }\n' +
    '    mapGloss = ng.a;\n' +
    '  }\n' +
    '  vec3 Lkey = normalize(vec3(-0.52, 0.74, -0.42));\n' +
    '  vec3 Lrim = normalize(vec3(0.60, 0.42, 0.68));\n' +
    '  vec3 V = normalize(uCamPos - vWorldPos);\n' +
    '  float ndl = max(dot(N, Lkey), 0.0);\n' +
    '  float ndr = max(dot(N, Lrim), 0.0);\n' +
    '  float hemi = 0.48 + 0.52 * clamp(N.y, -1.0, 1.0);\n' +
    '  float shadow = samplePropShadow(vWorldPos, N, Lkey);\n' +
    '  vec3 H = normalize(Lkey + V);\n' +
    '  float lum = dot(baseCol, vec3(0.299, 0.587, 0.114));\n' +
    '  float sat = max(baseCol.r, max(baseCol.g, baseCol.b)) - min(baseCol.r, min(baseCol.g, baseCol.b));\n' +
    '  float gloss = clamp(mix(0.32, mapGloss, uHasNormAtlas) + sat * 0.25, 0.10, 0.96);\n' +
    '  float fresnel = pow(clamp(1.0 - max(dot(N, V), 0.0), 1e-4, 1.0), 3.2);\n' +
    '  // TRUE LINEAR PBR with gentle shadow-floor lift so dark walnut wood & slate roofs stay crisp and readable!\n' +
    '  vec3 linBase = mix(pow(max(baseCol, vec3(1e-4)), vec3(2.2)), baseCol * 0.42, 0.18);\n' +
    '  vec3 linAmb = max(pow(max(uAmbientColor, vec3(1e-4)), vec3(2.2)), vec3(0.14, 0.145, 0.16));\n' +
    '  vec3 linKey = pow(max(uKeyColor, vec3(1e-4)), vec3(2.2));\n' +
    '  vec3 linRim = pow(max(uRimColor, vec3(1e-4)), vec3(2.2));\n' +
    '  float specPow = mix(18.0, 96.0, gloss);\n' +
    '  float specMask = clamp(0.16 + gloss * 0.80 + smoothstep(0.45, 0.85, lum) * 0.20, 0.0, 1.0);\n' +
    '  float spec = pow(max(dot(N, H), 1e-4), specPow) * 0.85 * specMask * shadow;\n' +
    '  vec3 specTint = mix(mix(linKey, vec3(1.0), 0.55), linBase * 1.9 + vec3(0.08), clamp(sat * 1.6, 0.0, 0.78));\n' +
    '  vec3 linLight = linAmb * (0.68 * hemi) + linKey * (0.14 + ndl * 1.65 * shadow) + linRim * (ndr * 0.34 + fresnel * 0.24);\n' +
    '  vec3 hdrCol = linBase * linLight + specTint * spec;\n' +
    '  vec3 col = pow(max(acesFilm(hdrCol * 0.86), vec3(1e-5)), vec3(1.0 / 2.2));\n' +
    '  float worldSpan = max(uWorldSize.x, uWorldSize.y);\n' +
    '  float distCam = length(uCamPos - vWorldPos);\n' +
    '  float distFog = smoothstep(worldSpan * 1.35, worldSpan * 3.1, distCam) * 0.15 * uMode3D;\n' +
    '  col = mix(col, uFogColor, distFog);\n' +
    '  vec2 uvW = vWorldPos.xz / max(uWorldSize, vec2(1.0));\n' +
    '  vec2 edgeD = (uvW - vec2(0.5)) * 2.0;\n' +
    '  float boxD = max(abs(edgeD.x), abs(edgeD.y));\n' +
    '  float radD = length(edgeD) * 0.80;\n' +
    '  float vig = smoothstep(0.74, 0.99, max(boxD, radD));\n' +
    '  col = mix(col, uBgColor, vig);\n' +
    '  fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);\n' +
    '}\n';

  var CLOUD_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec4 aQuad;\n' +  // local corner xy (-1..1), uv zw (0..1)
    'in vec4 aCloud;\n' + // cx01, cz01, scale, phase/alt
    'uniform mat4 uVP;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform float uHeightAmp;\n' +
    'uniform float uTime;\n' +
    'out vec2 vUv;\n' +
    'out float vSeed;\n' +
    'out vec3 vWorldPos;\n' +
    'void main() {\n' +
    '  float sp = 0.0045 + fract(aCloud.w * 3.7) * 0.004;\n' +
    '  float cx = fract(aCloud.x + uTime * sp) * uWorldSize.x;\n' +
    '  float cz = fract(aCloud.y + uTime * sp * 0.45) * uWorldSize.y;\n' +
    '  float ang = aCloud.w * 6.283 + uTime * 0.025;\n' +
    '  float ca = cos(ang), sa = sin(ang);\n' +
    '  vec2 rot = vec2(aQuad.x * ca - aQuad.y * sa, aQuad.x * sa + aQuad.y * ca) * aCloud.z;\n' +
    '  float wy = uHeightAmp * (1.12 + aCloud.w * 0.48);\n' +
    '  vec3 wp = vec3(cx + rot.x, wy, cz + rot.y);\n' +
    '  vWorldPos = wp;\n' +
    '  vUv = aQuad.zw;\n' +
    '  vSeed = aCloud.w;\n' +
    '  gl_Position = uVP * vec4(wp, 1.0);\n' +
    '}\n';

  var CLOUD_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp sampler2D;\n' +
    'in vec2 vUv;\n' +
    'in float vSeed;\n' +
    'in vec3 vWorldPos;\n' +
    'uniform sampler2D uCloudTex;\n' +
    'uniform sampler2D uCloudNormTex;\n' +
    'uniform vec3 uKeyColor;\n' +
    'uniform vec3 uAmbientColor;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform float uOpacity;\n' +
    'out vec4 fragColor;\n' +
    'void main() {\n' +
    '  float m = texture(uCloudTex, vUv).r;\n' +
    '  float rad = length((vUv - 0.5) * 2.0);\n' +
    '  float edge = smoothstep(1.0, 0.32, rad);\n' +
    '  float alpha = smoothstep(0.06, 0.62, m) * edge * uOpacity;\n' +
    '  if (alpha < 0.006) discard;\n' +
    '  vec2 wuv = vWorldPos.xz / max(uWorldSize, vec2(1.0));\n' +
    '  vec2 ed = (wuv - 0.5) * 2.0;\n' +
    '  float tableFade = 1.0 - smoothstep(0.68, 0.98, max(abs(ed.x), abs(ed.y)));\n' +
    '  alpha *= tableFade;\n' +
    '  vec3 rawCn = texture(uCloudNormTex, vUv).rgb * 2.0 - 1.0;\n' +
    '  vec3 cn = length(rawCn) > 1e-4 ? normalize(rawCn) : vec3(0.0, 1.0, 0.0);\n' +
    '  float lit = 0.58 + 0.42 * max(dot(cn, normalize(vec3(-0.52, 0.74, -0.42))), 0.0);\n' +
    '  vec3 col = mix(uAmbientColor * 1.15, mix(uKeyColor, vec3(0.92, 0.96, 1.0), 0.55), lit);\n' +
    '  fragColor = vec4(col, alpha);\n' +
    '}\n';

  var FLOOR_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec2 aPos;\n' +
    'uniform mat4 uVP;\n' +
    'out vec2 vPos;\n' +
    'void main() {\n' +
    '  vPos = aPos;\n' +
    '  gl_Position = uVP * vec4(aPos.x, -2.5, aPos.y, 1.0);\n' +
    '}\n';

  var FLOOR_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec2 vPos;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform vec3 uKeyColor;\n' +
    'uniform vec3 uBgColor;\n' +
    'out vec4 fragColor;\n' +
    'void main() {\n' +
    '  vec2 g = abs(fract(vPos / 256.0 - 0.5) - 0.5) / max(fwidth(vPos / 256.0), vec2(0.001));\n' +
    '  vec2 gs = abs(fract(vPos / 64.0 - 0.5) - 0.5) / max(fwidth(vPos / 64.0), vec2(0.001));\n' +
    '  float line = 1.0 - min(min(g.x, g.y), 1.0);\n' +
    '  float sub = 1.0 - min(min(gs.x, gs.y), 1.0);\n' +
    '  float rad = length((vPos / uWorldSize - 0.5) * 1.4);\n' +
    '  float fade = clamp(1.0 - rad * 0.85, 0.0, 1.0);\n' +
    '  fragColor = vec4(uBgColor + uKeyColor * ((line * 0.06 + sub * 0.018) * fade), 1.0);\n' +
    '}\n';

  var RIBBON_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec4 aPosA;\n' +
    'uniform mat4 uVP;\n' +
    'out float vAlpha;\n' +
    'out float vHeightY;\n' +
    'void main() {\n' +
    '  vAlpha = aPosA.w;\n' +
    '  vHeightY = aPosA.y;\n' +
    '  gl_Position = uVP * vec4(aPosA.xyz, 1.0);\n' +
    '}\n';

  var RIBBON_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in float vAlpha;\n' +
    'in float vHeightY;\n' +
    'uniform vec3 uColor;\n' +
    'uniform float uMult;\n' +
    'uniform float uTime;\n' +
    'uniform float uPulse;\n' +
    'out vec4 fragColor;\n' +
    'void main() {\n' +
    '  float wave = mix(1.0, 0.80 + 0.20 * sin(uTime * 3.4 - vHeightY * 0.025), uPulse);\n' +
    '  fragColor = vec4(uColor * mix(1.0, 1.15, uPulse * 0.5), vAlpha * uMult * wave);\n' +
    '}\n';

  var PARTICLE_VS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in vec4 aSeed;\n' + // x01, y01, z01, phase/size
    'uniform mat4 uVP;\n' +
    'uniform vec2 uWorldSize;\n' +
    'uniform float uTime;\n' +
    'uniform float uWeatherMode;\n' + // 0=snow, 1=embers, 2=motes
    'uniform float uDpr;\n' +
    'out float vAlpha;\n' +
    'out float vSeed;\n' +
    'void main() {\n' +
    '  float sp = 0.045 + aSeed.w * 0.055;\n' +
    '  float life = uWeatherMode < 0.5 ? fract(aSeed.y - uTime * sp) : (uWeatherMode < 1.5 ? fract(aSeed.y + uTime * (sp * 0.9)) : fract(aSeed.y + sin(uTime * 0.4 + aSeed.w * 19.0) * 0.08));\n' +
    '  float driftX = uWeatherMode < 0.5 ? (uTime * (0.018 + aSeed.w * 0.012) + sin(uTime * 0.9 + aSeed.w * 31.0) * 0.012) : (sin(uTime * 0.7 + aSeed.w * 27.0) * 0.02);\n' +
    '  float driftZ = uWeatherMode < 0.5 ? (uTime * (0.011 + aSeed.w * 0.008) + cos(uTime * 0.8 + aSeed.w * 23.0) * 0.012) : (cos(uTime * 0.6 + aSeed.w * 17.0) * 0.02);\n' +
    '  vec3 wp = vec3(fract(aSeed.x + driftX) * uWorldSize.x, 35.0 + life * 540.0, fract(aSeed.z + driftZ) * uWorldSize.y);\n' +
    '  vec4 clip = uVP * vec4(wp, 1.0);\n' +
    '  gl_Position = clip;\n' +
    '  float fade = smoothstep(0.0, 0.14, life) * smoothstep(1.0, 0.82, life);\n' +
    '  float baseSz = mix(3.2, 6.2, aSeed.w) * uDpr;\n' +
    '  gl_PointSize = clamp(baseSz * (1350.0 / max(260.0, clip.w)), 1.8, 12.0);\n' +
    '  vAlpha = fade * (0.42 + 0.45 * aSeed.w);\n' +
    '  vSeed = aSeed.w;\n' +
    '}\n';

  var PARTICLE_FS = '#version 300 es\n' +
    'precision highp float;\n' +
    'in float vAlpha;\n' +
    'in float vSeed;\n' +
    'uniform vec3 uColor;\n' +
    'uniform float uTime;\n' +
    'uniform float uWeatherMode;\n' +
    'out vec4 fragColor;\n' +
    'void main() {\n' +
    '  vec2 p = gl_PointCoord - vec2(0.5);\n' +
    '  float r = length(p) * 2.0;\n' +
    '  if (r > 1.0) discard;\n' +
    '  float soft = pow(max(1.0 - r, 1e-4), 1.85);\n' +
    '  float twinkle = 0.78 + 0.22 * sin(uTime * (2.5 + vSeed * 4.0) + vSeed * 43.0);\n' +
    '  vec3 col = uWeatherMode < 0.5 ? mix(vec3(0.86, 0.94, 1.0), vec3(1.0), soft) : uColor;\n' +
    '  fragColor = vec4(col, soft * vAlpha * twinkle);\n' +
    '}\n';

  function compileShader(gl, type, src) {
    var sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      console.warn('GoWR 3D shader error:', gl.getShaderInfoLog(sh));
      gl.deleteShader(sh);
      return null;
    }
    return sh;
  }

  function linkProgram(gl, vsSrc, fsSrc) {
    var vs = compileShader(gl, gl.VERTEX_SHADER, vsSrc);
    var fs = compileShader(gl, gl.FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs) return null;
    var p = gl.createProgram();
    gl.attachShader(p, vs);
    gl.attachShader(p, fs);
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      console.warn('GoWR 3D link error:', gl.getProgramInfoLog(p));
      return null;
    }
    return p;
  }

  function extractRealmFromUrl(url) {
    var m = String(url || '').match(/\/gow-(?:game-)?tiles\/([a-z-]+)\//);
    return m ? m[1] : null;
  }

  function MapView(id, opts) {
    this.el = document.getElementById(id);
    this.el.classList.add('leaflet-container', 'gow-map-stage');
    this.el._gowMap = this;
    this.options = opts || {};
    this.center = [0.7, -0.7];
    this.zoom = 11;
    this.min = this.options.minZoom || 9;
    this.max = this.options.maxZoom || 15;
    this.events = {};
    this.layers = new Set();
    this.tileLayer = null;

    // 3D Camera state
    this.mode3D = true;
    this.autoPitch = true;
    this.pitchDeg = 32;
    this.yawDeg = 0;
    this.targetX = WORLD_SPAN * 0.5;
    this.targetZ = WORLD_SPAN * 0.5;
    this.dist = 1600;
    this.animTarget = null;
    this.vx = 0;
    this.vz = 0;
    this.viewW = this.el.clientWidth || 1280;
    this.viewH = this.el.clientHeight || 800;
    this.vp = new Float32Array(16);
    this.invVP = null;
    this.camPos = [0, 1000, 0];

    // Realm geometry & heightmap
    this.realmKey = null;
    this.realmMeta = null;
    this.merc0 = { x_min: 127.2, x_max: 127.8, y_min: 127.2, y_max: 127.8 };
    this.worldW = WORLD_SPAN;
    this.worldH = WORLD_SPAN;
    this.mToW = WORLD_SPAN;
    this.heightAmp = WORLD_SPAN * 0.085;
    this.hasHeightmap = false;
    this.heightFloats = null;
    this.heightSize = 0;
    this.useNative3D = true;
    this.hasNativeSurface = false;
    this.hasTerrainNorm = false;
    this.hasWaterMask = false;
    this.hasNativeProps = false;
    this.hasNormalAtlas = false;
    this.hasShadowMap = false;
    this.shadowDirty = false;
    this.native3DMeta = null;
    this.propsIndexCount = 0;
    this.palette = {
      bg: [0.024, 0.047, 0.078],
      fog: [0.043, 0.094, 0.149],
      key_light: [0.949, 0.812, 0.510],
      rim_light: [0.455, 0.659, 0.886],
      ambient: [0.157, 0.220, 0.282],
      water: [0.047, 0.110, 0.173],
      beacon: [0.941, 0.784, 0.412],
      trail: [0.902, 0.729, 0.353]
    };

    // Waypoint, Kratos 3D trail, 3D clearing route & animated realm weather particles
    this.waypoint = null;      // { lat, lng, rgb }
    this.trailPoints = [];     // [{ lat, lng }]
    this.showTrail = true;
    this.routePoints = [];     // [{ lat, lng }]
    this.routeColor = [0.941, 0.784, 0.412];
    this.weatherMode = 0;      // 0=snow, 1=embers, 2=motes
    this.weatherEnabled = !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    this.paused = false;

    // DOM layers: 2D fallback tilePane + WebGL2 canvas + projected 3D region labels + markerPane
    this.tilePane = document.createElement('div');
    this.tilePane.className = 'leaflet-tile-pane';
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'gow-gl-canvas';
    this.labelPane = document.createElement('div');
    this.labelPane.className = 'gow-label-pane';
    this.regionLabels = [];
    this.markerPane = document.createElement('div');
    this.markerPane.className = 'leaflet-marker-pane';
    this.tipEl = document.createElement('div');
    this.tipEl.className = 'leaflet-tooltip gow-fs-tip';
    this.tipEl.hidden = true;
    this.activeTipMarker = null;
    this.el.append(this.tilePane, this.canvas, this.labelPane, this.markerPane, this.tipEl);

    this.hasWebGL2 = false;
    this.gl = null;
    this.glGeneration = 0;
    this.loadSeq = 0;
    this.native3DLoadingSeq = 0;
    this.atlasSlots = new window.Map(); // key -> { layer, usedAt, failed, loading, img }
    this.atlasTick = 0;
    this.atlasGenDirty = false;
    this.atlasLayersMax = MAX_ATLAS_LAYERS;

    // Pointer / Multitouch state (1:1 Google Maps physics)
    this.pointers = new window.Map();
    this.dragging = false;
    this.dragMode = 'pan';
    this.moved = false;
    this.wasMultiTouch = false;
    this.downPos = null;
    this.lastPinchDist = 0;
    this.lastCenter = null;
    this.lastAngle = null;
    this.twoStart = null;
    this.twoMode = null;
    this.twistUnlocked = false;
    this.dirty = true;

    var self = this;
    this.contextLost = false;
    this.contextLostTimer = null;
    this.canvas.addEventListener('webglcontextlost', function (e) {
      e.preventDefault();
      self.contextLost = true;
      self.hasWebGL2 = false;
      clearTimeout(self.contextLostTimer);
      // Wait briefly before falling back to 2D DOM tiles so transient Alt-Tab context restores never spam /gow-tiles/
      self.contextLostTimer = setTimeout(function () {
        if (self.contextLost && !self.hasWebGL2) {
          self.el.classList.add('gl-fallback');
          self.draw();
        }
      }, 1500);
    });
    this.canvas.addEventListener('webglcontextrestored', function () {
      self.contextLost = false;
      clearTimeout(self.contextLostTimer);
      self.contextLostTimer = null;
      if (self.tileLayer && self.tileLayer.images) {
        self.tileLayer.images.forEach(function (img) { img.remove(); });
        self.tileLayer.images.clear();
      }
      self.loadSeq++;
      self.native3DLoadingSeq = 0;
      self.hasHeightmap = false;
      self.hasNativeSurface = false;
      self.hasTerrainNorm = false;
      self.hasWaterMask = false;
      self.hasNativeProps = false;
      self.hasNormalAtlas = false;
      self.hasShadowMap = false;
      self.shadowDirty = false;
      self.hasFogCloud = false;
      self.detailLoadedCount = 0;
      self.propsIndexCount = 0;
      self._resetAtlas();
      self._initWebGL();
      if (self.hasWebGL2) {
        self.el.classList.remove('gl-fallback');
        self._resize();
        if (self.realmKey) self._loadRealmResources(self.realmKey);
        self._rebuildWaypointBuffers();
        self._rebuildTrailBuffers();
        self._rebuildRouteBuffers();
        self.dirty = true;
      }
    });

    function recoverIfIncomplete() {
      if (!self.hasWebGL2 || !self.gl || !self.realmKey) return;
      if (self.gl.isContextLost && self.gl.isContextLost()) return;
      self._resize();
      if (self.useNative3D && self.native3DLoadingSeq !== self.loadSeq) {
        var meta = self.native3DMeta;
        var missingSurf = !meta || (meta.has_native_3d && meta.has_surface && !self.hasNativeSurface);
        var missingProps = Boolean(meta && meta.has_native_3d && meta.has_props && !self.hasNativeProps);
        if (missingSurf || missingProps) {
          self._loadNative3DScene(self.realmKey, 0);
        }
      }
      self.dirty = true;
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') recoverIfIncomplete();
    });
    window.addEventListener('online', recoverIfIncomplete);

    this._initWebGL();
    this._bindEvents();
    this._resize();
    this._rafLoop();
  }

  MapView.prototype._initWebGL = function () {
    this.glGeneration = (this.glGeneration || 0) + 1;
    var gen = this.glGeneration;
    var gl = null;
    try {
      gl = this.canvas.getContext('webgl2', {
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
        preserveDrawingBuffer: false
      });
    } catch (e) {
      gl = null;
    }
    this.gl = gl;
    if (!gl) {
      this.hasWebGL2 = false;
      this.el.classList.add('gl-fallback');
      return;
    }
    this.progTerrain = linkProgram(gl, TERRAIN_VS, TERRAIN_FS);
    this.progShadow = linkProgram(gl, SHADOW_VS, SHADOW_FS);
    this.progProps = linkProgram(gl, PROPS_VS, PROPS_FS);
    this.progClouds = linkProgram(gl, CLOUD_VS, CLOUD_FS);
    this.progFloor = linkProgram(gl, FLOOR_VS, FLOOR_FS);
    this.progRibbon = linkProgram(gl, RIBBON_VS, RIBBON_FS);
    this.progParticles = linkProgram(gl, PARTICLE_VS, PARTICLE_FS);
    if (!this.progTerrain || !this.progFloor || !this.progRibbon) {
      this.gl = null;
      this.hasWebGL2 = false;
      this.el.classList.add('gl-fallback');
      return;
    }
    this.hasWebGL2 = true;
    this.el.classList.remove('gl-fallback');

    // Terrain indexed mesh uploaded once (lighter on CPU software & mobile touch GPUs)
    var glRend = '';
    try {
      var dbgInfo = gl.getExtension('WEBGL_debug_renderer_info');
      glRend = String((dbgInfo ? gl.getParameter(dbgInfo.UNMASKED_RENDERER_WEBGL) : '') || gl.getParameter(gl.RENDERER) || '');
    } catch (e) {}
    var isSoftwareGL = /SwiftShader|llvmpipe|Software|Basic Render Driver/i.test(glRend);
    var isMobileGL = /Adreno|Mali|PowerVR|Apple GPU|Xclipse|Immortalis/i.test(glRend) || (typeof navigator !== 'undefined' && (/Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || '') || navigator.maxTouchPoints > 1));
    this.isSoftwareGL = isSoftwareGL;
    this.isMobileGL = isMobileGL;
    var gridN = isSoftwareGL ? 128 : (isMobileGL ? 256 : GRID);
    var vCount = (gridN + 1) * (gridN + 1);
    var uvs = new Float32Array(vCount * 2);
    var p = 0;
    for (var iy = 0; iy <= gridN; iy++) {
      var v = iy / gridN;
      for (var ix = 0; ix <= gridN; ix++) {
        uvs[p++] = ix / gridN;
        uvs[p++] = v;
      }
    }
    var idx = new Uint32Array(gridN * gridN * 6);
    var q = 0;
    for (var y = 0; y < gridN; y++) {
      for (var x = 0; x < gridN; x++) {
        var i0 = y * (gridN + 1) + x;
        var i1 = i0 + 1;
        var i2 = i0 + (gridN + 1);
        var i3 = i2 + 1;
        idx[q++] = i0; idx[q++] = i2; idx[q++] = i1;
        idx[q++] = i1; idx[q++] = i2; idx[q++] = i3;
      }
    }
    this.terrainIndexCount = idx.length;
    this.vaoTerrain = gl.createVertexArray();
    gl.bindVertexArray(this.vaoTerrain);
    var vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, uvs, gl.STATIC_DRAW);
    var locUv = gl.getAttribLocation(this.progTerrain, 'aUv');
    gl.enableVertexAttribArray(locUv);
    gl.vertexAttribPointer(locUv, 2, gl.FLOAT, false, 8, 0);
    var ebo = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ebo);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);

    // Outer void floor quad (-4096..6144)
    this.vaoFloor = gl.createVertexArray();
    gl.bindVertexArray(this.vaoFloor);
    var fbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, fbo);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -4096, -4096, 6144, -4096, 6144, 6144,
      -4096, -4096, 6144, 6144, -4096, 6144
    ]), gl.STATIC_DRAW);
    var locF = gl.getAttribLocation(this.progFloor, 'aPos');
    gl.enableVertexAttribArray(locF);
    gl.vertexAttribPointer(locF, 2, gl.FLOAT, false, 8, 0);
    gl.bindVertexArray(null);

    // 16-bit Heightmap Texture (NEAREST so GLSL bilinear interpolation never mixes R & G bytes!)
    this.heightTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.heightTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB8, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0]));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    // Dynamic WebGL2 Tile Atlas (TEXTURE_2D_ARRAY) — lazy-allocated ONLY if fallback 2D tiles are needed (saves 67 MB VRAM!)
    this.atlasLayersMax = Math.min(isMobileGL ? 96 : MAX_ATLAS_LAYERS, gl.getParameter(gl.MAX_ARRAY_TEXTURE_LAYERS) || 128);
    this.anisoExt = gl.getExtension('EXT_texture_filter_anisotropic') ||
      gl.getExtension('MOZ_EXT_texture_filter_anisotropic') ||
      gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic');
    this.maxAniso = this.anisoExt
      ? Math.min(isMobileGL ? 4 : 16, gl.getParameter(this.anisoExt.MAX_TEXTURE_MAX_ANISOTROPY_EXT) || 8)
      : 1;
    this.tileAtlasAllocated = false;
    this.tileAtlas = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.tileAtlas);
    gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, 1, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    this.tileGridTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.tileGridTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, TILE_GRID_N, TILE_GRID_N, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    this.backGridTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.backGridTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, TILE_GRID_N, TILE_GRID_N, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    this.gridBufMain = new Uint8Array(TILE_GRID_N * TILE_GRID_N * 4);
    this.gridBufBack = new Uint8Array(TILE_GRID_N * TILE_GRID_N * 4);

    // Optional in-game PBR micro-detail textures (micronoise_n, micronoise, ice_cracks)
    this.detailLoadedCount = 0;
    var self = this;
    function makeDetailTex(url, fallbackRgba, onReady) {
      var tex = gl.createTexture();
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(fallbackRgba));
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
      function loadAttempt(nTry) {
        if (self.glGeneration !== gen || self.gl !== gl) return;
        var img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = function () {
          if (self.glGeneration !== gen || self.gl !== gl) return;
          if (img.naturalWidth < 16) {
            if (nTry < 3) setTimeout(function () { loadAttempt(nTry + 1); }, 800 * (nTry + 1));
            return;
          }
          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, tex);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
          gl.generateMipmap(gl.TEXTURE_2D);
          if (self.anisoExt && self.maxAniso > 1) {
            gl.texParameterf(gl.TEXTURE_2D, self.anisoExt.TEXTURE_MAX_ANISOTROPY_EXT, self.maxAniso);
          }
          onReady();
          self.dirty = true;
        };
        img.onerror = function () {
          if (self.glGeneration !== gen || self.gl !== gl || nTry >= 3) return;
          setTimeout(function () { loadAttempt(nTry + 1); }, 800 * (nTry + 1));
        };
        img.src = nTry > 0 ? (url + '&r=' + nTry) : url;
      }
      loadAttempt(0);
      return tex;
    }
    var dRev = '?v=20261128_pbr5';
    this.detailNormTex = makeDetailTex('/api/map-detail/micronoise_n.png' + dRev, [128, 128, 255, 255], function () { self.detailLoadedCount++; });
    this.detailNoiseTex = makeDetailTex('/api/map-detail/micronoise.png' + dRev, [128, 128, 128, 255], function () { self.detailLoadedCount++; });
    this.iceCracksTex = makeDetailTex('/api/map-detail/ice_cracks.png' + dRev, [0, 0, 0, 255], function () {});
    this.flowTex = makeDetailTex('/api/map-detail/flowmap.png' + dRev, [128, 128, 0, 255], function () {});
    this.hasFogCloud = false;
    this.fogCloudTex = makeDetailTex('/api/map-detail/fog_cloud.png' + dRev, [0, 0, 0, 255], function () { self.hasFogCloud = true; });
    this.cloudNormTex = makeDetailTex('/api/map-detail/clouds_n.png' + dRev, [128, 128, 255, 255], function () {});

    // Native reverse-engineered 3D game terrain surface, 2K normal+shadow, water/lava mask & landmark PBR atlases
    function makeClampedTex(rgba) {
      var t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(rgba));
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    }
    this.nativeSurfaceTex = makeClampedTex([20, 30, 42, 255]);
    this.terrainNormTex = makeClampedTex([128, 255, 128, 255]);
    this.waterMaskTex = makeClampedTex([0, 0, 36, 255]);
    this.propsAtlasTex = makeClampedTex([180, 180, 180, 255]);
    this.propsNormTex = makeClampedTex([128, 128, 255, 96]);
    this.hasTerrainNorm = false;
    this.hasWaterMask = false;
    this.hasNormalAtlas = false;

    this.vaoProps = gl.createVertexArray();
    this.vaoPropsShadow = gl.createVertexArray();
    this.vboProps = gl.createBuffer();
    this.eboProps = gl.createBuffer();
    this.propsIndexCount = 0;

    // Real-time directional depth shadow map for 3D landmarks (Tyr's Temple, towers, bridges, cranes)
    this.shadowRes = (isSoftwareGL || isMobileGL) ? 1024 : 2048;
    this.hasShadowMap = false;
    this.shadowDirty = false;
    this.lightVP = new Float32Array(16);
    this.shadowMapTex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.shadowMapTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.DEPTH_COMPONENT24, this.shadowRes, this.shadowRes, 0, gl.DEPTH_COMPONENT, gl.UNSIGNED_INT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    this.shadowFbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.shadowFbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, this.shadowMapTex, 0);
    gl.drawBuffers([gl.NONE]);
    gl.readBuffer(gl.NONE);
    if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
      gl.deleteFramebuffer(this.shadowFbo);
      this.shadowFbo = null;
      gl.bindTexture(gl.TEXTURE_2D, this.shadowMapTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([255, 255, 255, 255]));
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);

    // 3D volumetric cloud mist layer (14 drifting elevated quads using real TX_fog_cloud_04 + TX_m_clouds)
    this.vaoClouds = null;
    this.cloudVertCount = 0;
    if (this.progClouds) {
      var cloudSpecs = [
        [0.14, 0.16, 360, 0.12], [0.84, 0.18, 340, 0.37], [0.18, 0.82, 370, 0.61],
        [0.82, 0.80, 350, 0.84], [0.50, 0.11, 320, 0.23], [0.52, 0.89, 340, 0.72],
        [0.09, 0.50, 310, 0.45], [0.91, 0.52, 330, 0.91], [0.33, 0.31, 250, 0.19],
        [0.68, 0.36, 260, 0.54], [0.30, 0.68, 255, 0.77], [0.69, 0.66, 245, 0.31],
        [0.48, 0.46, 220, 0.65], [0.56, 0.54, 210, 0.08]
      ];
      var cCorners = [
        [-1, -1, 0, 0], [1, -1, 1, 0], [1, 1, 1, 1],
        [-1, -1, 0, 0], [1, 1, 1, 1], [-1, 1, 0, 1]
      ];
      var cBuf = new Float32Array(cloudSpecs.length * 6 * 8);
      var co = 0;
      for (var ci = 0; ci < cloudSpecs.length; ci++) {
        var cs = cloudSpecs[ci];
        for (var vi = 0; vi < 6; vi++) {
          var cc = cCorners[vi];
          cBuf[co++] = cc[0]; cBuf[co++] = cc[1]; cBuf[co++] = cc[2]; cBuf[co++] = cc[3];
          cBuf[co++] = cs[0]; cBuf[co++] = cs[1]; cBuf[co++] = cs[2]; cBuf[co++] = cs[3];
        }
      }
      this.cloudVertCount = cloudSpecs.length * 6;
      this.vaoClouds = gl.createVertexArray();
      gl.bindVertexArray(this.vaoClouds);
      var cbo = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, cbo);
      gl.bufferData(gl.ARRAY_BUFFER, cBuf, gl.STATIC_DRAW);
      var locCq = gl.getAttribLocation(this.progClouds, 'aQuad');
      var locCc = gl.getAttribLocation(this.progClouds, 'aCloud');
      if (locCq >= 0) { gl.enableVertexAttribArray(locCq); gl.vertexAttribPointer(locCq, 4, gl.FLOAT, false, 32, 0); }
      if (locCc >= 0) { gl.enableVertexAttribArray(locCc); gl.vertexAttribPointer(locCc, 4, gl.FLOAT, false, 32, 16); }
      gl.bindVertexArray(null);
    }

    // Waypoint, Trail & 3D Clearing Route VAOs
    this.vaoWpBeam = gl.createVertexArray(); this.bufWpBeam = gl.createBuffer(); this.wpBeamCount = 0;
    this.vaoWpRing = gl.createVertexArray(); this.bufWpRing = gl.createBuffer(); this.wpRingCount = 0;
    this.vaoTrailLine = gl.createVertexArray(); this.bufTrailLine = gl.createBuffer(); this.trailLineCount = 0;
    this.vaoTrailTicks = gl.createVertexArray(); this.bufTrailTicks = gl.createBuffer(); this.trailTickCount = 0;
    this.vaoRouteRibbon = gl.createVertexArray(); this.bufRouteRibbon = gl.createBuffer(); this.routeRibbonCount = 0;
    this.vaoRouteNodes = gl.createVertexArray(); this.bufRouteNodes = gl.createBuffer(); this.routeNodeCount = 0;

    // 3D Realm Weather Particles (deterministic Halton-like distribution, 360 particles)
    this.particleCount = 360;
    this.vaoParticles = null;
    if (this.progParticles) {
      var pArr = new Float32Array(this.particleCount * 4);
      var s = 1337;
      function rnd() { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }
      for (var pi = 0; pi < this.particleCount; pi++) {
        pArr[pi * 4]     = rnd();
        pArr[pi * 4 + 1] = rnd();
        pArr[pi * 4 + 2] = rnd();
        pArr[pi * 4 + 3] = rnd();
      }
      this.vaoParticles = gl.createVertexArray();
      gl.bindVertexArray(this.vaoParticles);
      var pbo = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, pbo);
      gl.bufferData(gl.ARRAY_BUFFER, pArr, gl.STATIC_DRAW);
      var locP = gl.getAttribLocation(this.progParticles, 'aSeed');
      gl.enableVertexAttribArray(locP);
      gl.vertexAttribPointer(locP, 4, gl.FLOAT, false, 16, 0);
      gl.bindVertexArray(null);
    }
  };

  MapView.prototype._applyRealmBounds = function (meta) {
    if (!meta || !meta.merc0) return;
    var prevM0 = this.merc0;
    var prevMToW = this.mToW;
    var oldCenterLL = this.center.slice();
    var oldAnimLL = (prevM0 && prevMToW && this.animTarget)
      ? this._worldXZToLatLng(this.animTarget.x, this.animTarget.z) : null;
    var oldAnimZoom = (prevM0 && prevMToW && this.animTarget)
      ? this._distToZoom(this.animTarget.dist) : null;

    this.realmMeta = meta;
    this.merc0 = {
      x_min: Number(meta.merc0.x_min),
      x_max: Number(meta.merc0.x_max),
      y_min: Number(meta.merc0.y_min),
      y_max: Number(meta.merc0.y_max)
    };
    var sx = Math.max(1e-6, this.merc0.x_max - this.merc0.x_min);
    var sy = Math.max(1e-6, this.merc0.y_max - this.merc0.y_min);
    var span = Math.max(sx, sy);
    this.mToW = WORLD_SPAN / span;
    this.worldW = sx * this.mToW;
    this.worldH = sy * this.mToW;
    this.heightAmp = (meta.height_scale || 0.085) * WORLD_SPAN;
    this.weatherMode = meta.weather === 'snow' ? 0 : (meta.weather === 'embers' ? 1 : 2);
    if (meta.palette) {
      this.palette = {
        bg: hexToRgb01(meta.palette.bg, [0.024, 0.047, 0.078]),
        fog: hexToRgb01(meta.palette.fog, [0.043, 0.094, 0.149]),
        key_light: hexToRgb01(meta.palette.key_light, [0.949, 0.812, 0.510]),
        rim_light: hexToRgb01(meta.palette.rim_light, [0.455, 0.659, 0.886]),
        ambient: hexToRgb01(meta.palette.ambient, [0.157, 0.220, 0.282]),
        water: hexToRgb01(meta.palette.water, [0.047, 0.110, 0.173]),
        beacon: hexToRgb01(meta.palette.beacon, [0.941, 0.784, 0.412]),
        trail: hexToRgb01(meta.palette.trail, [0.902, 0.729, 0.353])
      };
    }
    if (prevM0 && prevMToW) {
      var wz = this._latLngToWorldXZ(oldCenterLL);
      this.targetX = wz[0];
      this.targetZ = wz[1];
      this.dist = this._zoomToDist(this.zoom);
      if (this.animTarget && oldAnimLL) {
        var az = this._latLngToWorldXZ(oldAnimLL);
        this.animTarget.x = az[0];
        this.animTarget.z = az[1];
        if (oldAnimZoom != null) this.animTarget.dist = this._zoomToDist(oldAnimZoom);
      }
      this._clamp();
      this._apply();
    }
    this._rebuildWaypointBuffers();
    this._rebuildTrailBuffers();
    this._rebuildRouteBuffers();
    this.dirty = true;
  };

  MapView.prototype.setRealm = function (realmKey) {
    if (!realmKey || this.realmKey === realmKey) return this;
    this.realmKey = realmKey;
    this.loadSeq++;
    this.native3DLoadingSeq = 0;
    this.hasHeightmap = false;
    this.heightFloats = null;
    this.heightSize = 0;
    this.hasNativeSurface = false;
    this.hasTerrainNorm = false;
    this.hasWaterMask = false;
    this.hasNativeProps = false;
    this.hasNormalAtlas = false;
    this.hasShadowMap = false;
    this.shadowDirty = false;
    this.native3DMeta = null;
    this.propsIndexCount = 0;
    this.trailPoints = [];
    this.routePoints = [];
    this._rebuildTrailBuffers();
    this._rebuildRouteBuffers();
    this._resetAtlas();
    if (this.gl && this.heightTex) {
      var gl = this.gl;
      gl.bindTexture(gl.TEXTURE_2D, this.heightTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB8, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0]));
    }
    this._loadRealmResources(realmKey);
    return this;
  };

  MapView.prototype.setNative3D = function (enabled) {
    this.useNative3D = Boolean(enabled);
    this.dirty = true;
    return this;
  };

  MapView.prototype._loadNative3DScene = function (realmKey, attempt) {
    var self = this;
    var tryNo = attempt || 0;
    var seq = this.loadSeq;
    var gen = this.glGeneration;
    if (!this.gl || self.realmKey !== realmKey) return;
    this.native3DLoadingSeq = seq;
    fetch('/api/realm-3d/' + encodeURIComponent(realmKey) + '/meta.json', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (meta) {
        if (!meta || self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen) return;
        self.native3DMeta = meta;
        self.emit('native3dready', { realm: realmKey, meta: meta });
        self.dirty = true;
        if (!meta.has_native_3d) {
          self.native3DLoadingSeq = 0;
          return;
        }
        var pending = 0;
        function trackDone() {
          pending = Math.max(0, pending - 1);
          if (pending === 0 && self.native3DLoadingSeq === seq) self.native3DLoadingSeq = 0;
        }

        function loadClampedTex(tex, url, onReady, imgTry) {
          var nTry = imgTry || 0;
          if (nTry === 0) pending++;
          var img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = function () {
            if (self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen || !self.gl) {
              trackDone();
              return;
            }
            if (img.naturalWidth < 16) {
              if (nTry < 4) {
                setTimeout(function () {
                  if (self.realmKey === realmKey && self.loadSeq === seq && self.glGeneration === gen && self.gl) {
                    loadClampedTex(tex, url, onReady, nTry + 1);
                  } else {
                    trackDone();
                  }
                }, 600 * (nTry + 1));
              } else {
                trackDone();
              }
              return;
            }
            var gl = self.gl;
            gl.activeTexture(gl.TEXTURE0);
            gl.bindTexture(gl.TEXTURE_2D, tex);
            gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
            gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
            gl.generateMipmap(gl.TEXTURE_2D);
            if (self.anisoExt && self.maxAniso > 1) {
              gl.texParameterf(gl.TEXTURE_2D, self.anisoExt.TEXTURE_MAX_ANISOTROPY_EXT, self.maxAniso);
            }
            onReady();
            trackDone();
            self.dirty = true;
          };
          img.onerror = function () {
            if (self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen || nTry >= 4) {
              trackDone();
              return;
            }
            setTimeout(function () {
              if (self.realmKey === realmKey && self.loadSeq === seq && self.glGeneration === gen && self.gl) {
                loadClampedTex(tex, url, onReady, nTry + 1);
              } else {
                trackDone();
              }
            }, 600 * (nTry + 1));
          };
          img.src = nTry > 0 ? (url + '&r=' + nTry) : url;
        }
        var base3d = '/api/realm-3d/' + encodeURIComponent(realmKey) + '/';
        var revQ = '?v=' + encodeURIComponent(meta.rev || 1);
        if (meta.has_surface) {
          loadClampedTex(self.nativeSurfaceTex, base3d + 'surface.png' + revQ, function () {
            self.hasNativeSurface = true;
          });
        }
        if (meta.has_terrain_normal) {
          loadClampedTex(self.terrainNormTex, base3d + 'terrain_n.png' + revQ, function () {
            self.hasTerrainNorm = true;
          });
        }
        if (meta.has_water_mask) {
          loadClampedTex(self.waterMaskTex, base3d + 'water_mask.png' + revQ, function () {
            self.hasWaterMask = true;
          });
        }

        if (meta.has_props && self.progProps) {
          var atlasReady = false;
          var meshReady = false;
          function checkDone() {
            if (atlasReady && meshReady && self.realmKey === realmKey && self.loadSeq === seq && self.glGeneration === gen) {
              self.hasNativeProps = true;
              self.shadowDirty = true;
              self.dirty = true;
            }
          }
          loadClampedTex(self.propsAtlasTex, base3d + 'atlas.png' + revQ, function () {
            atlasReady = true;
            checkDone();
          });

          if (meta.has_normal_atlas) {
            loadClampedTex(self.propsNormTex, base3d + 'atlas_n.png' + revQ, function () {
              self.hasNormalAtlas = true;
            });
          }

          pending++;
          function loadPropsBin(pTry) {
            fetch(base3d + 'props.bin' + revQ + (pTry > 0 ? ('&r=' + pTry) : ''))
              .then(function (r) { if (!r.ok || r.status === 204) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); })
              .then(function (buf) {
                if (self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen || !self.gl) {
                  trackDone();
                  return;
                }
                if (!buf || buf.byteLength < 16) throw new Error('Truncated props header');
                var dv = new DataView(buf);
                // Magic 'GOWM' = 0x4d574f47 little-endian
                if (dv.getUint32(0, true) !== 0x4d574f47 || dv.getUint32(4, true) !== 1) throw new Error('Bad props magic');
                var nv = dv.getUint32(8, true);
                var ni = dv.getUint32(12, true);
                var vBytes = nv * 32;
                var iBytes = ni * 4;
                if (!nv || !ni || 16 + vBytes + iBytes > buf.byteLength) throw new Error('Truncated props body');
                var verts = new Float32Array(buf, 16, nv * 8);
                var idxs = new Uint32Array(buf, 16 + vBytes, ni);
                var gl = self.gl;
                gl.bindVertexArray(self.vaoProps);
                gl.bindBuffer(gl.ARRAY_BUFFER, self.vboProps);
                gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW);
                var locP = gl.getAttribLocation(self.progProps, 'aPos');
                var locN = gl.getAttribLocation(self.progProps, 'aNorm');
                var locU = gl.getAttribLocation(self.progProps, 'aUv');
                if (locP >= 0) { gl.enableVertexAttribArray(locP); gl.vertexAttribPointer(locP, 3, gl.FLOAT, false, 32, 0); }
                if (locN >= 0) { gl.enableVertexAttribArray(locN); gl.vertexAttribPointer(locN, 3, gl.FLOAT, false, 32, 12); }
                if (locU >= 0) { gl.enableVertexAttribArray(locU); gl.vertexAttribPointer(locU, 2, gl.FLOAT, false, 32, 24); }
                gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.eboProps);
                gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idxs, gl.STATIC_DRAW);
                if (self.progShadow && self.vaoPropsShadow) {
                  gl.bindVertexArray(self.vaoPropsShadow);
                  gl.bindBuffer(gl.ARRAY_BUFFER, self.vboProps);
                  var locSP = gl.getAttribLocation(self.progShadow, 'aPos');
                  var locSU = gl.getAttribLocation(self.progShadow, 'aUv');
                  if (locSP >= 0) { gl.enableVertexAttribArray(locSP); gl.vertexAttribPointer(locSP, 3, gl.FLOAT, false, 32, 0); }
                  if (locSU >= 0) { gl.enableVertexAttribArray(locSU); gl.vertexAttribPointer(locSU, 2, gl.FLOAT, false, 32, 24); }
                  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.eboProps);
                }
                gl.bindVertexArray(null);
                self.propsIndexCount = ni;
                meshReady = true;
                checkDone();
                trackDone();
              })
              .catch(function () {
                if (self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen || pTry >= 4) {
                  trackDone();
                  return;
                }
                setTimeout(function () {
                  if (self.realmKey === realmKey && self.loadSeq === seq && self.glGeneration === gen && self.gl) {
                    loadPropsBin(pTry + 1);
                  } else {
                    trackDone();
                  }
                }, 600 * (pTry + 1));
              });
          }
          loadPropsBin(0);
        }
        if (pending === 0 && self.native3DLoadingSeq === seq) self.native3DLoadingSeq = 0;
      })
      .catch(function () {
        if (self.realmKey !== realmKey || self.loadSeq !== seq || self.glGeneration !== gen) return;
        if (tryNo < 4) {
          setTimeout(function () {
            if (self.realmKey === realmKey && self.loadSeq === seq && self.glGeneration === gen && self.gl) {
              self._loadNative3DScene(realmKey, tryNo + 1);
            }
          }, 700 * (tryNo + 1));
        } else {
          // After retries exhausted, allow fallback tile layer to render instead of blank void
          self.native3DLoadingSeq = 0;
          self.native3DMeta = { realm: realmKey, has_native_3d: false };
          self.dirty = true;
        }
      });
  };

  MapView.prototype._loadRealmResources = function (realmKey, attempt) {
    var self = this;
    var tryNo = attempt || 0;
    var seq = this.loadSeq;
    var gen = this.glGeneration;
    if (tryNo === 0) this._loadNative3DScene(realmKey, 0);
    fetch('/api/realm-height/' + encodeURIComponent(realmKey) + '/meta.json', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (meta) {
        if (!meta || self.realmKey !== realmKey || self.loadSeq !== seq) return;
        self._applyRealmBounds(meta);
        if (meta.has_heightmap === false) return;
        function loadHeightImg(hTry) {
          var img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = function () {
            if (self.realmKey !== realmKey || self.loadSeq !== seq) return;
            var w = img.naturalWidth || img.width;
            var h = img.naturalHeight || img.height;
            if (w < 16 || h < 16) {
              if (hTry < 4) setTimeout(function () { if (self.realmKey === realmKey && self.loadSeq === seq) loadHeightImg(hTry + 1); }, 600 * (hTry + 1));
              return;
            }
            var cvs = document.createElement('canvas');
            cvs.width = w; cvs.height = h;
            var ctx = cvs.getContext('2d');
            ctx.drawImage(img, 0, 0);
            var data = ctx.getImageData(0, 0, w, h).data;
            var flt = new Float32Array(w * h);
            for (var i = 0, j = 0; i < data.length; i += 4, j++) {
              var valid = data[i + 2] > 127 ? 1.0 : 0.0;
              flt[j] = ((data[i] * 256 + data[i + 1]) / 65535.0) * valid;
            }
            self.heightFloats = flt;
            self.heightSize = w;
            self.hasHeightmap = true;
            if (self.gl && self.heightTex && self.glGeneration === gen) {
              var gl = self.gl;
              gl.activeTexture(gl.TEXTURE0);
              gl.bindTexture(gl.TEXTURE_2D, self.heightTex);
              gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
              gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
            }
            self._rebuildWaypointBuffers();
            self._rebuildTrailBuffers();
            self._rebuildRouteBuffers();
            self.dirty = true;
          };
          img.onerror = function () {
            if (self.realmKey !== realmKey || self.loadSeq !== seq || hTry >= 4) return;
            setTimeout(function () {
              if (self.realmKey === realmKey && self.loadSeq === seq) loadHeightImg(hTry + 1);
            }, 600 * (hTry + 1));
          };
          var hRev = meta.rev ? ('?v=' + encodeURIComponent(meta.rev)) : '?v=20261128_pbr6';
          img.src = '/api/realm-height/' + encodeURIComponent(realmKey) + hRev + (hTry > 0 ? ('&r=' + hTry) : '');
        }
        loadHeightImg(0);
      })
      .catch(function () {
        if (self.realmKey !== realmKey || self.loadSeq !== seq || tryNo >= 4) return;
        setTimeout(function () {
          if (self.realmKey === realmKey && self.loadSeq === seq) self._loadRealmResources(realmKey, tryNo + 1);
        }, 700 * (tryNo + 1));
      });
  };

  MapView.prototype._resetAtlas = function () {
    this.atlasSlots.forEach(function (entry) {
      if (entry.img) { entry.img.onload = null; entry.img.onerror = null; }
    });
    this.atlasSlots.clear();
    this.atlasTick = 0;
    this.atlasGenDirty = false;
  };

  MapView.prototype._latLngToWorldXZ = function (ll) {
    var g = point(ll, 0);
    return [
      (g[0] - this.merc0.x_min) * this.mToW,
      (g[1] - this.merc0.y_min) * this.mToW
    ];
  };

  MapView.prototype._worldXZToLatLng = function (wx, wz) {
    var gx = wx / this.mToW + this.merc0.x_min;
    var gy = wz / this.mToW + this.merc0.y_min;
    return unpoint([gx, gy], 0);
  };

  MapView.prototype.sampleHeight = function (lat, lng) {
    if (!this.hasHeightmap || !this.heightFloats || !this.heightSize) return 0;
    var xz = this._latLngToWorldXZ([lat, lng]);
    return this._sampleHeightWorld(xz[0], xz[1]);
  };

  MapView.prototype._sampleHeightWorld = function (wx, wz) {
    if (!this.hasHeightmap || !this.heightFloats || !this.heightSize) return 0;
    var u = clamp(wx / this.worldW, 0, 1);
    var v = clamp(wz / this.worldH, 0, 1);
    var s = this.heightSize;
    var px = u * (s - 1);
    var py = v * (s - 1);
    var x0 = Math.floor(px), y0 = Math.floor(py);
    var x1 = Math.min(s - 1, x0 + 1), y1 = Math.min(s - 1, y0 + 1);
    var fx = px - x0, fy = py - y0;
    var f = this.heightFloats;
    var h00 = f[y0 * s + x0], h10 = f[y0 * s + x1];
    var h01 = f[y1 * s + x0], h11 = f[y1 * s + x1];
    var h01v = (h00 * (1 - fx) + h10 * fx) * (1 - fy) + (h01 * (1 - fx) + h11 * fx) * fy;
    return h01v * this.heightAmp;
  };

  MapView.prototype._zoomToDist = function (z) {
    var vh = Math.max(200, this.viewH);
    return (vh * this.mToW) / (2 * TAN_HALF_FOV * Math.pow(2, z));
  };

  MapView.prototype._distToZoom = function (d) {
    var vh = Math.max(200, this.viewH);
    return Math.log2((vh * this.mToW) / Math.max(1e-6, 2 * TAN_HALF_FOV * d));
  };

  MapView.prototype._pitchForDist = function (d) {
    if (!this.mode3D) return 0.0;
    var z = this._distToZoom(d);
    var t = clamp((z - this.min) / Math.max(1, this.max - this.min), 0, 1);
    return 18.0 + t * 18.0;
  };

  MapView.prototype._minDist = function () { return this._zoomToDist(this.max + 0.45); };
  MapView.prototype._maxDist = function () { return this._zoomToDist(this.min - 1.5); };

  MapView.prototype._clamp = function () {
    this.targetX = clamp(this.targetX, -this.worldW * 0.25, this.worldW * 1.25);
    this.targetZ = clamp(this.targetZ, -this.worldH * 0.25, this.worldH * 1.25);
    this.dist = clamp(this.dist, this._minDist(), this._maxDist());
    this.pitchDeg = clamp(this.pitchDeg, 0, MAX_PITCH);
  };

  MapView.prototype._updateMatrices = function () {
    var aspect = Math.max(0.2, this.viewW / Math.max(1, this.viewH));
    var pRad = Math.max(0.012, this.pitchDeg * Math.PI / 180);
    var yRad = this.yawDeg * Math.PI / 180;
    var horiz = Math.sin(pRad) * this.dist;
    var camY = Math.cos(pRad) * this.dist;
    var camX = this.targetX + Math.sin(yRad) * horiz;
    var camZ = this.targetZ + Math.cos(yRad) * horiz;
    var upX = -Math.sin(yRad);
    var upZ = -Math.cos(yRad);

    this.camPos = [camX, camY, camZ];
    var far = Math.max(16000, this.dist * 6 + WORLD_SPAN * 4);
    var near = Math.max(4, this.dist * 0.02);
    var proj = mat4Perspective(FOV_RAD, aspect, near, far);
    var view = mat4LookAt(camX, camY, camZ, this.targetX, 0, this.targetZ, upX, 0.001, upZ);
    this.vp = mat4Mul(proj, view);
    this.invVP = mat4Invert(this.vp);
    this.zoom = clamp(this._distToZoom(this.dist), this.min - 1.5, this.max + 1.5);
    this.center = this._worldXZToLatLng(this.targetX, this.targetZ);
  };

  MapView.prototype.project3D = function (wx, wy, wz) {
    var m = this.vp;
    var cx = m[0] * wx + m[4] * wy + m[8]  * wz + m[12];
    var cy = m[1] * wx + m[5] * wy + m[9]  * wz + m[13];
    var cw = m[3] * wx + m[7] * wy + m[11] * wz + m[15];
    if (cw <= 1.0) return null;
    var ndcX = cx / cw;
    var ndcY = cy / cw;
    if (ndcX < -1.25 || ndcX > 1.25 || ndcY < -1.25 || ndcY > 1.25) return null;
    return {
      x: (ndcX * 0.5 + 0.5) * this.viewW,
      y: (0.5 - ndcY * 0.5) * this.viewH,
      depth: cw
    };
  };

  MapView.prototype.unprojectGround = function (clientX, clientY) {
    if (!this.invVP) return null;
    var r = this.el.getBoundingClientRect();
    var nx = ((clientX - r.left) / Math.max(1, r.width)) * 2 - 1;
    var ny = 1 - ((clientY - r.top) / Math.max(1, r.height)) * 2;
    var m = this.invVP;
    function mul(z) {
      var w = m[3] * nx + m[7] * ny + m[11] * z + m[15];
      return [
        (m[0] * nx + m[4] * ny + m[8]  * z + m[12]) / w,
        (m[1] * nx + m[5] * ny + m[9]  * z + m[13]) / w,
        (m[2] * nx + m[6] * ny + m[10] * z + m[14]) / w
      ];
    }
    var p0 = mul(-1.0);
    var p1 = mul(1.0);
    var dy = p1[1] - p0[1];
    if (Math.abs(dy) < 1e-6) return null;
    var t = -p0[1] / dy;
    if (t < 0) return null;
    return [p0[0] + (p1[0] - p0[0]) * t, p0[2] + (p1[2] - p0[2]) * t];
  };

  // ══════════ PUBLIC COMPATIBILITY + 3D API ══════════
  MapView.prototype.on = function (name, fn) {
    (this.events[name] || (this.events[name] = [])).push(fn);
    return this;
  };
  MapView.prototype.emit = function (name, ev) {
    (this.events[name] || []).forEach(function (fn) { fn(ev); });
  };
  MapView.prototype.getZoom = function () { return this.zoom; };
  MapView.prototype.setMinZoom = function (v) { this.min = v; this._clamp(); return this; };
  MapView.prototype.setMaxZoom = function (v) { this.max = v; this._clamp(); return this; };

  MapView.prototype.setView = function (ll, z, opts) {
    var targetZ = z == null ? this.zoom : clamp(z, this.min, this.max);
    this.center = ll.slice();
    this.zoom = targetZ;
    if (!this.hasWebGL2) {
      this.draw();
      return this;
    }
    var xz = this._latLngToWorldXZ(ll);
    var dist = this._zoomToDist(targetZ);
    var pitch = this.autoPitch ? this._pitchForDist(dist) : this.pitchDeg;
    if (opts && opts.animate && opts.duration !== 0) {
      this.animTarget = { x: xz[0], z: xz[1], dist: dist, pitch: pitch, yaw: this.yawDeg };
      this.vx = 0; this.vz = 0;
      this.dirty = true;
    } else {
      this.targetX = xz[0];
      this.targetZ = xz[1];
      this.dist = dist;
      this.pitchDeg = pitch;
      this.animTarget = null;
      this.vx = 0; this.vz = 0;
      this._clamp();
      this.dirty = true;
      this._apply();
    }
    return this;
  };

  MapView.prototype.flyTo = function (ll, z, opts) {
    return this.setView(ll, z, Object.assign({ animate: true }, opts || {}));
  };

  MapView.prototype.panTo = function (ll, opts) {
    return this.setView(ll, null, opts);
  };

  MapView.prototype.zoomIn = function () {
    return this.setView(this.center, clamp(this.zoom + 0.5, this.min, this.max), { animate: false });
  };

  MapView.prototype.zoomOut = function () {
    return this.setView(this.center, clamp(this.zoom - 0.5, this.min, this.max), { animate: false });
  };

  MapView.prototype.zoomAt = function (x, y, nextZoom) {
    nextZoom = clamp(nextZoom, this.min, this.max);
    if (!this.hasWebGL2) {
      var r = this.el.getBoundingClientRect(), old = point(this.center, this.zoom);
      var offset = [x - r.left - r.width / 2, y - r.top - r.height / 2];
      var ll = unpoint([old[0] + offset[0], old[1] + offset[1]], this.zoom);
      this.zoom = nextZoom;
      var p = point(ll, this.zoom);
      this.center = unpoint([p[0] - offset[0], p[1] - offset[1]], this.zoom);
      this.draw();
      return;
    }
    var before = this.unprojectGround(x, y);
    this.dist = this._zoomToDist(nextZoom);
    if (this.autoPitch) this.pitchDeg = this._pitchForDist(this.dist);
    this._clamp();
    this._updateMatrices();
    var after = this.unprojectGround(x, y);
    if (before && after) {
      this.targetX += (before[0] - after[0]);
      this.targetZ += (before[1] - after[1]);
      this._clamp();
    }
    this.animTarget = null;
    this.dirty = true;
    this._apply();
  };

  MapView.prototype.fitBounds = function (b, opts) {
    if (Array.isArray(b)) b = bounds(b);
    if (!b || !b.lo || !b.hi || !b.lo.every(Number.isFinite) || !b.hi.every(Number.isFinite)) return this;
    opts = opts || {};
    var tl = opts.paddingTopLeft || [30, 30];
    var br = opts.paddingBottomRight || [30, 30];
    var p = point(b.lo, 0), q = point(b.hi, 0);
    var w = Math.max(100, this.el.clientWidth - tl[0] - br[0]);
    var h = Math.max(100, this.el.clientHeight - tl[1] - br[1]);
    var z = Math.min(
      Math.log2(w / Math.max(Math.abs(q[0] - p[0]), 1e-8)),
      Math.log2(h / Math.max(Math.abs(q[1] - p[1]), 1e-8))
    );
    z = clamp(Math.floor(z * 2) / 2, this.min, Math.min(opts.maxZoom || this.max, this.max));
    var scale = Math.pow(2, z);
    var ll = unpoint([(p[0] + q[0]) * scale / 2 - (tl[0] - br[0]) / 2, (p[1] + q[1]) * scale / 2 - (tl[1] - br[1]) / 2], z);
    return this.setView(ll, z, { animate: opts.animate !== false && opts.duration > 0 });
  };

  MapView.prototype.flyToBounds = MapView.prototype.fitBounds;

  MapView.prototype.invalidateSize = function () {
    this._resize();
    return this;
  };

  MapView.prototype.hasLayer = function (layer) { return this.layers.has(layer); };
  MapView.prototype.removeLayer = function (layer) {
    this.layers.delete(layer);
    if (layer.el) layer.el.remove();
    layer.map = null;
    this.draw();
    return this;
  };

  MapView.prototype.setMode3D = function (enabled) {
    this.mode3D = Boolean(enabled);
    this.autoPitch = this.mode3D;
    this.shadowDirty = true;
    var targetPitch = this.mode3D ? this._pitchForDist(this.dist) : 0.0;
    this.animTarget = {
      x: this.targetX, z: this.targetZ, dist: this.dist,
      pitch: targetPitch, yaw: this.mode3D ? this.yawDeg : 0
    };
    this.dirty = true;
    this.emit('camerachange', this);
    return this;
  };

  MapView.prototype.rotateBy = function (deltaDeg) {
    this.animTarget = {
      x: this.targetX, z: this.targetZ, dist: this.dist,
      pitch: this.pitchDeg, yaw: this.yawDeg + deltaDeg
    };
    this.dirty = true;
    return this;
  };

  MapView.prototype.tiltBy = function (deltaDeg) {
    this.autoPitch = false;
    var np = clamp(this.pitchDeg + deltaDeg, 0, MAX_PITCH);
    this.mode3D = np > 2;
    this.animTarget = {
      x: this.targetX, z: this.targetZ, dist: this.dist,
      pitch: np, yaw: this.yawDeg
    };
    this.dirty = true;
    this.emit('camerachange', this);
    return this;
  };

  MapView.prototype.resetNorth = function () {
    var shortest = ((0 - this.yawDeg) % 360 + 540) % 360 - 180;
    this.animTarget = {
      x: this.targetX, z: this.targetZ, dist: this.dist,
      pitch: this.pitchDeg, yaw: this.yawDeg + shortest
    };
    this.dirty = true;
    return this;
  };

  MapView.prototype.setWaypoint = function (lat, lng, hexColor) {
    if (lat == null || lng == null) {
      this.waypoint = null;
    } else {
      this.waypoint = {
        lat: Number(lat),
        lng: Number(lng),
        rgb: hexToRgb01(hexColor, this.palette.beacon)
      };
    }
    this._rebuildWaypointBuffers();
    this.dirty = true;
    return this;
  };

  MapView.prototype.pushTrailPoint = function (lat, lng) {
    if (typeof lat !== 'number' || typeof lng !== 'number' || !isFinite(lat) || !isFinite(lng)) return this;
    var xz = this._latLngToWorldXZ([lat, lng]);
    var n = this.trailPoints.length;
    if (n > 0) {
      var prev = this._latLngToWorldXZ([this.trailPoints[n - 1].lat, this.trailPoints[n - 1].lng]);
      var d = Math.hypot(xz[0] - prev[0], xz[1] - prev[1]);
      if (d < 4.5) return this;
      if (d > 480) this.trailPoints = []; // fast travel reset
    }
    this.trailPoints.push({ lat: lat, lng: lng });
    if (this.trailPoints.length > 160) this.trailPoints.shift();
    this._rebuildTrailBuffers();
    this.dirty = true;
    return this;
  };

  MapView.prototype.setShowTrail = function (on) {
    this.showTrail = Boolean(on);
    this.dirty = true;
    return this;
  };

  MapView.prototype.setWeatherEnabled = function (on) {
    this.weatherEnabled = Boolean(on);
    this.dirty = true;
    return this;
  };

  MapView.prototype.setPaused = function (on) {
    this.paused = Boolean(on);
    if (!this.paused) this.dirty = true;
    return this;
  };

  MapView.prototype.clearTrail = function () {
    this.trailPoints = [];
    this._rebuildTrailBuffers();
    this.dirty = true;
    return this;
  };

  MapView.prototype.setRoute = function (points, hexColor) {
    if (!Array.isArray(points) || points.length < 2) {
      this.routePoints = [];
    } else {
      this.routePoints = points.filter(function (pt) {
        return pt && typeof pt.lat === 'number' && typeof pt.lng === 'number' && isFinite(pt.lat) && isFinite(pt.lng);
      }).map(function (pt) { return { lat: pt.lat, lng: pt.lng }; });
    }
    this.routeColor = hexToRgb01(hexColor, this.palette.beacon);
    this._rebuildRouteBuffers();
    this.dirty = true;
    return this;
  };

  MapView.prototype._rebuildRouteBuffers = function () {
    var gl = this.gl;
    if (!gl || !this.progRibbon || !this.vaoRouteRibbon) return;
    var rib = [];
    var nodes = [];
    var pts = this.routePoints;
    if (pts && pts.length >= 2) {
      // Sample dense terrain-hugging polyline along every leg
      var sampled = [];
      for (var i = 0; i < pts.length - 1; i++) {
        var a = this._latLngToWorldXZ([pts[i].lat, pts[i].lng]);
        var b = this._latLngToWorldXZ([pts[i + 1].lat, pts[i + 1].lng]);
        var legDist = Math.hypot(b[0] - a[0], b[1] - a[1]);
        var steps = Math.max(6, Math.min(28, Math.ceil(legDist / 45)));
        for (var s = 0; s < steps; s++) {
          var t = s / steps;
          var wx = a[0] + (b[0] - a[0]) * t;
          var wz = a[1] + (b[1] - a[1]) * t;
          var wy = this._sampleHeightWorld(wx, wz) + 8.5;
          sampled.push([wx, wy, wz]);
        }
      }
      var lastXZ = this._latLngToWorldXZ([pts[pts.length - 1].lat, pts[pts.length - 1].lng]);
      sampled.push([lastXZ[0], this._sampleHeightWorld(lastXZ[0], lastXZ[1]) + 8.5, lastXZ[1]]);

      // Extrude into horizontal + vertical cross-ribbon triangles so thickness is crisp on D3D11
      var halfW = 2.6;
      var nS = sampled.length;
      for (var k = 0; k < nS - 1; k++) {
        var p0 = sampled[k], p1 = sampled[k + 1];
        var dx = p1[0] - p0[0], dz = p1[2] - p0[2];
        var len = Math.hypot(dx, dz) || 1.0;
        var nx = -dz / len * halfW, nz = dx / len * halfW;
        var alpha0 = 0.78 - 0.30 * (k / Math.max(1, nS - 1));
        var alpha1 = 0.78 - 0.30 * ((k + 1) / Math.max(1, nS - 1));
        // Flat ribbon above terrain
        rib.push(
          p0[0] - nx, p0[1], p0[2] - nz, alpha0,
          p0[0] + nx, p0[1], p0[2] + nz, alpha0,
          p1[0] + nx, p1[1], p1[2] + nz, alpha1,
          p0[0] - nx, p0[1], p0[2] - nz, alpha0,
          p1[0] + nx, p1[1], p1[2] + nz, alpha1,
          p1[0] - nx, p1[1], p1[2] - nz, alpha1
        );
        // Subtle glowing vertical curtain underneath ribbon
        rib.push(
          p0[0], p0[1],       p0[2], alpha0 * 0.38,
          p1[0], p1[1],       p1[2], alpha1 * 0.38,
          p1[0], p1[1] - 6.0, p1[2], 0.01,
          p0[0], p0[1],       p0[2], alpha0 * 0.38,
          p1[0], p1[1] - 6.0, p1[2], 0.01,
          p0[0], p0[1] - 6.0, p0[2], 0.01
        );
      }

      // Stop beacons (subtle glowing pillars at subsequent route stops; skip stop 1 if main beacon sits there)
      var segs = 12;
      for (var j = 1; j < pts.length; j++) {
        if (j === 1 && this.waypoint &&
            Math.hypot(this.waypoint.lat - pts[j].lat, this.waypoint.lng - pts[j].lng) < 1e-4) {
          continue;
        }
        var cxz = this._latLngToWorldXZ([pts[j].lat, pts[j].lng]);
        var cx = cxz[0], cz = cxz[1];
        var cy = this._sampleHeightWorld(cx, cz);
        var rB = 8.5, rT = 2.0, hT = cy + WORLD_SPAN * 0.08;
        var aNode = 0.36;
        for (var si = 0; si < segs; si++) {
          var a0 = (si / segs) * Math.PI * 2;
          var a1 = ((si + 1) / segs) * Math.PI * 2;
          var c0 = Math.cos(a0), s0 = Math.sin(a0);
          var c1 = Math.cos(a1), s1 = Math.sin(a1);
          nodes.push(
            cx + c0 * rB, cy + 2.0, cz + s0 * rB, aNode,
            cx + c1 * rB, cy + 2.0, cz + s1 * rB, aNode,
            cx + c1 * rT, hT,       cz + s1 * rT, 0.0,
            cx + c0 * rB, cy + 2.0, cz + s0 * rB, aNode,
            cx + c1 * rT, hT,       cz + s1 * rT, 0.0,
            cx + c0 * rT, hT,       cz + s0 * rT, 0.0
          );
        }
      }
    }
    var self = this;
    function upload(vao, buf, arr) {
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.DYNAMIC_DRAW);
      var loc = gl.getAttribLocation(self.progRibbon, 'aPosA');
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 4, gl.FLOAT, false, 16, 0);
      gl.bindVertexArray(null);
      return arr.length / 4;
    }
    this.routeRibbonCount = upload(this.vaoRouteRibbon, this.bufRouteRibbon, rib);
    this.routeNodeCount = upload(this.vaoRouteNodes, this.bufRouteNodes, nodes);
  };

  MapView.prototype._rebuildWaypointBuffers = function () {
    var gl = this.gl;
    if (!gl || !this.progRibbon || !this.vaoWpBeam) return;
    var beam = [];
    var ring = [];
    if (this.waypoint) {
      var xz = this._latLngToWorldXZ([this.waypoint.lat, this.waypoint.lng]);
      var x = xz[0], z = xz[1];
      var y0 = this._sampleHeightWorld(x, z);
      var segs = 16;
      var rBot = 6.5, rTop = 1.6, hTop = y0 + WORLD_SPAN * 0.16;
      var rRing = 18.0;
      for (var i = 0; i < segs; i++) {
        var a0 = (i / segs) * Math.PI * 2;
        var a1 = ((i + 1) / segs) * Math.PI * 2;
        var c0 = Math.cos(a0), s0 = Math.sin(a0);
        var c1 = Math.cos(a1), s1 = Math.sin(a1);
        beam.push(
          x + c0 * rBot, y0 + 1.5, z + s0 * rBot, 0.48,
          x + c1 * rBot, y0 + 1.5, z + s1 * rBot, 0.48,
          x + c1 * rTop, hTop,     z + s1 * rTop, 0.0,
          x + c0 * rBot, y0 + 1.5, z + s0 * rBot, 0.48,
          x + c1 * rTop, hTop,     z + s1 * rTop, 0.0,
          x + c0 * rTop, hTop,     z + s0 * rTop, 0.0
        );
        var yr = y0 + 3.0;
        ring.push(
          x + c0 * rRing, yr, z + s0 * rRing, 0.95,
          x + c1 * rRing, yr, z + s1 * rRing, 0.95,
          x + c0 * (rRing * 0.56), yr, z + s0 * (rRing * 0.56), 0.75,
          x + c1 * (rRing * 0.56), yr, z + s1 * (rRing * 0.56), 0.75
        );
      }
    }
    var self = this;
    function upload(vao, buf, arr) {
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.DYNAMIC_DRAW);
      var loc = gl.getAttribLocation(self.progRibbon, 'aPosA');
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 4, gl.FLOAT, false, 16, 0);
      gl.bindVertexArray(null);
      return arr.length / 4;
    }
    this.wpBeamCount = upload(this.vaoWpBeam, this.bufWpBeam, beam);
    this.wpRingCount = upload(this.vaoWpRing, this.bufWpRing, ring);
  };

  MapView.prototype._rebuildTrailBuffers = function () {
    var gl = this.gl;
    if (!gl || !this.progRibbon || !this.vaoTrailLine) return;
    var rib = [];
    var ticks = [];
    var pts = this.trailPoints;
    var n = pts.length;
    var worldPts = [];
    for (var i = 0; i < n; i++) {
      var t = n > 1 ? i / (n - 1) : 1.0;
      var a = 0.10 + t * t * 0.72;
      var xz = this._latLngToWorldXZ([pts[i].lat, pts[i].lng]);
      var wy = this._sampleHeightWorld(xz[0], xz[1]);
      worldPts.push([xz[0], wy + 5.5, xz[1], a, t]);
      if (i % 6 === 0) {
        ticks.push(xz[0], wy + 5.5, xz[1], a * 0.45, xz[0], wy + 0.5, xz[1], 0.04);
      }
    }
    // Extrude tapered 3D ribbon triangles so Kratos's trail stays crisp on D3D11 (1px lineWidth clamp)
    for (var k = 0; k < worldPts.length - 1; k++) {
      var p0 = worldPts[k], p1 = worldPts[k + 1];
      var dx = p1[0] - p0[0], dz = p1[2] - p0[2];
      var len = Math.hypot(dx, dz) || 1.0;
      var hw0 = 1.2 + p0[4] * 2.0;
      var hw1 = 1.2 + p1[4] * 2.0;
      var nx0 = -dz / len * hw0, nz0 = dx / len * hw0;
      var nx1 = -dz / len * hw1, nz1 = dx / len * hw1;
      rib.push(
        p0[0] - nx0, p0[1], p0[2] - nz0, p0[3],
        p0[0] + nx0, p0[1], p0[2] + nz0, p0[3],
        p1[0] + nx1, p1[1], p1[2] + nz1, p1[3],
        p0[0] - nx0, p0[1], p0[2] - nz0, p0[3],
        p1[0] + nx1, p1[1], p1[2] + nz1, p1[3],
        p1[0] - nx1, p1[1], p1[2] - nz1, p1[3]
      );
    }
    var self = this;
    function upload(vao, buf, arr) {
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.DYNAMIC_DRAW);
      var loc = gl.getAttribLocation(self.progRibbon, 'aPosA');
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 4, gl.FLOAT, false, 16, 0);
      gl.bindVertexArray(null);
      return arr.length / 4;
    }
    this.trailLineCount = upload(this.vaoTrailLine, this.bufTrailLine, rib);
    this.trailTickCount = upload(this.vaoTrailTicks, this.bufTrailTicks, ticks);
  };

  // ══════════ DYNAMIC WEBGL2 TILE ATLAS ══════════
  MapView.prototype._allocAtlasLayer = function () {
    if (this.atlasSlots.size < this.atlasLayersMax) {
      return this.atlasSlots.size;
    }
    var oldestKey = null;
    var oldestTick = Infinity;
    this.atlasSlots.forEach(function (entry, key) {
      if (entry.usedAt < oldestTick) {
        oldestTick = entry.usedAt;
        oldestKey = key;
      }
    });
    if (oldestKey != null) {
      var recycled = this.atlasSlots.get(oldestKey);
      if (recycled.img) { recycled.img.onload = null; recycled.img.onerror = null; }
      this.atlasSlots.delete(oldestKey);
      return recycled.layer;
    }
    return 0;
  };

  MapView.prototype._ensureTile = function (z, x, y) {
    if (!this.tileLayer || !this.gl) return 0;
    var key = this.tileLayer.url + '|' + z + '/' + x + '/' + y;
    var entry = this.atlasSlots.get(key);
    this.atlasTick++;
    if (entry) {
      entry.usedAt = this.atlasTick;
      return entry.loaded ? (entry.layer + 1) : 0;
    }
    var layerIdx = this._allocAtlasLayer();
    entry = { layer: layerIdx, usedAt: this.atlasTick, loaded: false, failed: false, img: null };
    this.atlasSlots.set(key, entry);

    var self = this;
    var gen = this.glGeneration;
    var img = new Image();
    img.crossOrigin = 'anonymous';
    entry.img = img;
    img.onload = function () {
      if (self.atlasSlots.get(key) !== entry || !self.gl || self.glGeneration !== gen || !self.tileAtlasAllocated) return;
      var gl = self.gl;
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D_ARRAY, self.tileAtlas);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
      gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, entry.layer, 256, 256, 1, gl.RGBA, gl.UNSIGNED_BYTE, img);
      entry.loaded = true;
      self.atlasGenDirty = true;
      self.dirty = true;
    };
    img.onerror = function () {
      entry.failed = true;
    };
    img.src = this.tileLayer.url.replace('{z}', z).replace('{x}', x).replace('{y}', y);
    return 0;
  };

  MapView.prototype._ensureTileAtlas = function () {
    if (this.tileAtlasAllocated || !this.gl || !this.tileAtlas) return;
    var gl = this.gl;
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.tileAtlas);
    gl.texImage3D(gl.TEXTURE_2D_ARRAY, 0, gl.RGBA8, 256, 256, this.atlasLayersMax, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    if (this.anisoExt && this.maxAniso > 1) {
      gl.texParameterf(gl.TEXTURE_2D_ARRAY, this.anisoExt.TEXTURE_MAX_ANISOTROPY_EXT, this.maxAniso);
    }
    this.tileAtlasAllocated = true;
  };

  MapView.prototype._syncTileGrids = function () {
    if (!this.gl || !this.tileLayer) return null;
    this._ensureTileAtlas();
    var gl = this.gl;
    var maxNative = this.tileLayer.options.maxNativeZoom || 14;
    var dpr = Math.min(window.devicePixelRatio || 1, 2.0);
    var dprBoost = dpr > 1.25 ? 0.55 : 0.15;
    var zMain = clamp(Math.ceil(this.zoom + 0.35 + dprBoost), this.min, maxNative);
    var zBack = zMain > this.min ? zMain - 1 : Math.min(maxNative, zMain + 1);

    var centerM0 = [
      this.targetX / this.mToW + this.merc0.x_min,
      this.targetZ / this.mToW + this.merc0.y_min
    ];

    var self = this;
    function fillGrid(z, buf, tex, radius) {
      var n = Math.pow(2, z);
      var scale = n / 256.0;
      var cx = Math.floor(centerM0[0] * scale);
      var cy = Math.floor(centerM0[1] * scale);
      var tx0 = cx - Math.floor(TILE_GRID_N / 2);
      var ty0 = cy - Math.floor(TILE_GRID_N / 2);
      buf.fill(0);
      var minTx = Math.max(0, cx - radius, Math.floor(self.merc0.x_min * scale));
      var maxTx = Math.min(n - 1, cx + radius, Math.floor(self.merc0.x_max * scale));
      var minTy = Math.max(0, cy - radius, Math.floor(self.merc0.y_min * scale));
      var maxTy = Math.min(n - 1, cy + radius, Math.floor(self.merc0.y_max * scale));
      // Request tiles center-out so the visible viewport always fills first
      var cells = [];
      for (var gy = 0; gy < TILE_GRID_N; gy++) {
        var ty = ty0 + gy;
        if (ty < minTy || ty > maxTy) continue;
        for (var gx = 0; gx < TILE_GRID_N; gx++) {
          var tx = tx0 + gx;
          if (tx < minTx || tx > maxTx) continue;
          var dx = tx - cx;
          var dy = ty - cy;
          cells.push([dx * dx + dy * dy, gx, gy, tx, ty]);
        }
      }
      cells.sort(function (a, b) { return a[0] - b[0]; });
      for (var ci = 0; ci < cells.length; ci++) {
        var c = cells[ci];
        var idx1 = self._ensureTile(z, c[3], c[4]);
        buf[(c[2] * TILE_GRID_N + c[1]) * 4] = idx1;
      }
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, TILE_GRID_N, TILE_GRID_N, gl.RGBA, gl.UNSIGNED_BYTE, buf);
      return [tx0, ty0, n, TILE_GRID_N];
    }

    var gBack = fillGrid(zBack, this.gridBufBack, this.backGridTex, 5);
    var gMain = fillGrid(zMain, this.gridBufMain, this.tileGridTex, 5);

    if (this.atlasGenDirty) {
      gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.tileAtlas);
      gl.generateMipmap(gl.TEXTURE_2D_ARRAY);
      this.atlasGenDirty = false;
    }
    return { main: gMain, back: gBack };
  };

  // ══════════ RENDER LOOP & PROJECTION ══════════
  MapView.prototype.draw = function () {
    this.dirty = true;
  };

  MapView.prototype._resize = function () {
    var r = this.el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    var maxDpr = this.isMobileGL ? 1.75 : 2.0;
    var dpr = Math.min(window.devicePixelRatio || 1, maxDpr);
    this.viewW = r.width;
    this.viewH = r.height;
    var cw = Math.round(r.width * dpr);
    var ch = Math.round(r.height * dpr);
    if (this.canvas.width !== cw || this.canvas.height !== ch) {
      this.canvas.width = cw;
      this.canvas.height = ch;
    }
    this.dirty = true;
    this._apply();
  };

  MapView.prototype._showTip = function (marker) {
    if (!this.tipEl || !marker || !marker.label) return;
    this.activeTipMarker = marker;
    this.tipEl.textContent = marker.label;
    this.tipEl.hidden = false;
    this._positionTip();
  };

  MapView.prototype._hideTip = function (marker) {
    if (!this.tipEl) return;
    if (!marker || this.activeTipMarker === marker) {
      this.activeTipMarker = null;
      this.tipEl.hidden = true;
    }
  };

  MapView.prototype._positionTip = function () {
    if (!this.tipEl || this.tipEl.hidden || !this.activeTipMarker || !this.activeTipMarker.el) return;
    var el = this.activeTipMarker.el;
    if (el.style.visibility === 'hidden') { this.tipEl.hidden = true; return; }
    var x = parseFloat(el.style.left) + (parseFloat(el.style.width) || 32) * 0.5;
    var y = parseFloat(el.style.top) - 6;
    this.tipEl.style.left = x.toFixed(1) + 'px';
    this.tipEl.style.top = y.toFixed(1) + 'px';
  };

  MapView.prototype.setRegionLabels = function (labels) {
    if (!this.labelPane) return;
    this.labelPane.innerHTML = '';
    this.regionLabels = [];
    var self = this;
    (labels || []).forEach(function (item) {
      if (!item || !item.name || item.lat == null || item.lng == null) return;
      var el = document.createElement('div');
      el.className = 'gow-region-label' + (item.major ? ' is-major' : '');
      el.textContent = item.name;
      self.labelPane.appendChild(el);
      self.regionLabels.push({ ll: [item.lat, item.lng], el: el, major: !!item.major });
    });
    this._projectOverlay();
  };

  MapView.prototype._projectOverlay = function () {
    var self = this;
    var yaw = this.yawDeg;
    if (!this.hasWebGL2) {
      if (!this.contextLost || this.el.classList.contains('gl-fallback')) {
        this._paint2D();
      }
      this._positionTip();
      return;
    }
    var refDepth = Math.max(100, this.dist);
    var scaleT = clamp(this.pitchDeg / 28, 0, 1);
    this.layers.forEach(function (layer) {
      if (!layer.ll || !layer.el) return;
      var xz = self._latLngToWorldXZ(layer.ll);
      var wy = self._sampleHeightWorld(xz[0], xz[1]);
      var p = self.project3D(xz[0], wy + 2.0, xz[1]);
      var a = layer.icon.iconAnchor || [0, 0];
      if (!p) {
        layer.el.style.visibility = 'hidden';
      } else {
        layer.el.style.visibility = 'visible';
        layer.el.style.left = (p.x - a[0]).toFixed(1) + 'px';
        layer.el.style.top = (p.y - a[1]).toFixed(1) + 'px';
        var persp = clamp(Math.pow(refDepth / Math.max(1, p.depth), 0.42), 0.72, 1.16);
        var pinScale = 1 + (persp - 1) * scaleT;
        layer.el.style.setProperty('--pin-scale', pinScale.toFixed(3));
        var baseZ = 1000 + (layer.options.zIndexOffset || 0);
        if (baseZ < 2000 && self.mode3D) {
          var depthBias = clamp(Math.round(300 - (p.depth / refDepth) * 150), 0, 300);
          layer.el.style.zIndex = String(baseZ + depthBias);
        }
      }
    });
    var showLabels = this.zoom >= 10.6;
    var placedLabels = [];
    for (var li = 0; li < this.regionLabels.length; li++) {
      var rl = this.regionLabels[li];
      if (!showLabels) { rl.el.style.visibility = 'hidden'; continue; }
      var lxz = this._latLngToWorldXZ(rl.ll);
      var lwy = this._sampleHeightWorld(lxz[0], lxz[1]);
      var lp = this.project3D(lxz[0], lwy + 10.0, lxz[1]);
      if (!lp) {
        rl.el.style.visibility = 'hidden';
        continue;
      }
      var collide = false;
      for (var pi = 0; pi < placedLabels.length; pi++) {
        if (Math.abs(lp.x - placedLabels[pi][0]) < 156 && Math.abs(lp.y - placedLabels[pi][1]) < 42) {
          collide = true;
          break;
        }
      }
      if (collide) {
        rl.el.style.visibility = 'hidden';
      } else {
        placedLabels.push([lp.x, lp.y]);
        rl.el.style.visibility = 'visible';
        rl.el.style.left = lp.x.toFixed(1) + 'px';
        rl.el.style.top = (lp.y - 22).toFixed(1) + 'px';
        var lPersp = clamp(Math.pow(refDepth / Math.max(1, lp.depth), 0.36), 0.76, 1.15);
        rl.el.style.transform = 'translate(-50%, -50%) scale(' + lPersp.toFixed(3) + ')';
      }
    }
    this._positionTip();
    if (this.events.camerachange) {
      this.emit('camerachange', { target: this, yawDeg: yaw, pitchDeg: this.pitchDeg, mode3D: this.mode3D });
    }
  };

  MapView.prototype._paint2D = function () {
    var self = this, w = this.el.clientWidth, h = this.el.clientHeight, c = point(this.center, this.zoom);
    if (this.tileLayer) {
      var layer = this.tileLayer, z = Math.min(Math.floor(this.zoom), layer.options.maxNativeZoom || 18);
      var size = 256 * Math.pow(2, this.zoom - z), n = Math.pow(2, z);
      var left = c[0] - w / 2, top = c[1] - h / 2, needed = new Set();
      for (var x = Math.max(0, Math.floor(left / size)); x <= Math.min(n - 1, Math.floor((left + w) / size)); x++) {
        for (var y = Math.max(0, Math.floor(top / size)); y <= Math.min(n - 1, Math.floor((top + h) / size)); y++) {
          var key = z + '/' + x + '/' + y; needed.add(key);
          var img = layer.images.get(key);
          if (!img) {
            img = document.createElement('img'); img.className = 'leaflet-tile'; img.alt = ''; img.draggable = false;
            img.src = layer.url.replace('{z}', z).replace('{x}', x).replace('{y}', y);
            img.onerror = function () { this.hidden = true; };
            layer.images.set(key, img); this.tilePane.appendChild(img);
          }
          img.style.cssText = 'left:' + (x * size - left) + 'px;top:' + (y * size - top) + 'px;width:' + (size + 0.5) + 'px;height:' + (size + 0.5) + 'px';
        }
      }
      layer.images.forEach(function (img, key) { if (!needed.has(key)) { img.remove(); layer.images.delete(key); } });
    }
    this.layers.forEach(function (layer) {
      if (!layer.ll || !layer.el) return;
      var p = point(layer.ll, self.zoom), a = layer.icon.iconAnchor || [0, 0];
      layer.el.style.visibility = 'visible';
      layer.el.style.left = (p[0] - c[0] + w / 2 - a[0]) + 'px';
      layer.el.style.top = (p[1] - c[1] + h / 2 - a[1]) + 'px';
    });
  };

  MapView.prototype._renderShadowMap = function () {
    var gl = this.gl;
    if (!gl || !this.shadowFbo || !this.progShadow || !this.vaoPropsShadow) return;
    if (!this.useNative3D || !this.hasNativeProps || this.propsIndexCount <= 0) return;
    var cx = this.worldW * 0.5;
    var cz = this.worldH * 0.5;
    var span = Math.max(this.worldW, this.worldH) * 0.62;
    var lx = -0.52, ly = 0.74, lz = -0.42;
    var llen = Math.hypot(lx, ly, lz) || 1.0;
    lx /= llen; ly /= llen; lz /= llen;
    var distL = 2200.0;
    var lightView = mat4LookAt(cx + lx * distL, ly * distL, cz + lz * distL, cx, 0, cz, 0, 1, 0);
    var lightProj = mat4Ortho(-span, span, -span, span, 300.0, 4400.0);
    this.lightVP = mat4Mul(lightProj, lightView);

    // Drain any unrelated prior error before validating the depth-only shadow pass
    while (gl.getError() !== gl.NO_ERROR) {}
    // Unbind shadowMapTex from any sampler units before rendering into shadowFbo (prevents mobile/ANGLE feedback hazards!)
    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, null);
    gl.activeTexture(gl.TEXTURE11);
    gl.bindTexture(gl.TEXTURE_2D, null);

    gl.bindFramebuffer(gl.FRAMEBUFFER, this.shadowFbo);
    gl.viewport(0, 0, this.shadowRes, this.shadowRes);
    gl.colorMask(false, false, false, false);
    gl.disable(gl.BLEND);
    gl.enable(gl.DEPTH_TEST);
    gl.depthMask(true);
    gl.depthFunc(gl.LESS);
    gl.clear(gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.progShadow);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progShadow, 'uLightVP'), false, this.lightVP);
    gl.uniform1f(gl.getUniformLocation(this.progShadow, 'uMode3D'), this.mode3D ? 1.0 : 0.0);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.propsAtlasTex);
    gl.uniform1i(gl.getUniformLocation(this.progShadow, 'uAtlasTex'), 0);
    gl.bindVertexArray(this.vaoPropsShadow);
    gl.drawElements(gl.TRIANGLES, this.propsIndexCount, gl.UNSIGNED_INT, 0);
    gl.bindVertexArray(null);
    gl.colorMask(true, true, true, true);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (gl.getError() !== gl.NO_ERROR) {
      this.hasShadowMap = false;
      this.shadowFbo = null;
      this.shadowDirty = false;
      return;
    }
    this.hasShadowMap = true;
    this.shadowDirty = false;
  };

  MapView.prototype._renderGL = function () {
    var gl = this.gl;
    if (!gl || !this.progTerrain) return;
    var pal = this.palette;

    // PASS 0: Bake real-time 3D landmark directional depth shadow map when props load or 2D/3D toggles
    if (this.shadowDirty && this.useNative3D && this.hasNativeProps && this.propsIndexCount > 0) {
      this._renderShadowMap();
    }

    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    gl.clearColor(pal.bg[0], pal.bg[1], pal.bg[2], 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // PASS 1: Outer Void / Carved Nordic Floor
    gl.disable(gl.BLEND);
    gl.enable(gl.DEPTH_TEST);
    gl.depthMask(true);
    gl.depthFunc(gl.LEQUAL);
    gl.useProgram(this.progFloor);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progFloor, 'uVP'), false, this.vp);
    gl.uniform2f(gl.getUniformLocation(this.progFloor, 'uWorldSize'), this.worldW, this.worldH);
    gl.uniform3fv(gl.getUniformLocation(this.progFloor, 'uKeyColor'), pal.key_light);
    gl.uniform3fv(gl.getUniformLocation(this.progFloor, 'uBgColor'), pal.bg);
    gl.bindVertexArray(this.vaoFloor);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // PASS 2: Sculpted 3D Terrain Mesh + 2K Carved Wood Normal/Shadow + Water/Lava Flowmap + Real-Time Shadow Map
    // Never spam 100+ fallback /gow-tiles/ requests while native 3D scene is loading!
    var useNativeSurf = this.useNative3D && this.hasNativeSurface;
    var waitingNative = this.useNative3D && (!this.native3DMeta || this.native3DMeta.has_native_3d);
    var grids = (useNativeSurf || waitingNative) ? null : this._syncTileGrids();
    gl.useProgram(this.progTerrain);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progTerrain, 'uVP'), false, this.vp);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progTerrain, 'uLightVP'), false, this.lightVP);
    gl.uniform2f(gl.getUniformLocation(this.progTerrain, 'uWorldSize'), this.worldW, this.worldH);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHeightAmp'), this.heightAmp);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasHeight'), this.hasHeightmap ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasTiles'), grids ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uUseNativeSurface'), useNativeSurf ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasTerrainNorm'), (useNativeSurf && this.hasTerrainNorm) ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasWaterMask'), (useNativeSurf && this.hasWaterMask) ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasShadowMap'), (useNativeSurf && this.hasShadowMap) ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uShadowRes'), this.shadowRes || 1024.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uIsLava'), this.realmKey === 'muspelheim' ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uMode3D'), this.mode3D ? 1.0 : 0.0);
    var tSec = ((typeof performance !== 'undefined' ? performance.now() : Date.now()) % 100000) * 0.001;
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uTime'), tSec);
    gl.uniform4f(gl.getUniformLocation(this.progTerrain, 'uMerc0'),
      this.merc0.x_min, this.merc0.y_min, this.merc0.x_max, this.merc0.y_max);
    if (grids) {
      gl.uniform4fv(gl.getUniformLocation(this.progTerrain, 'uGridMain'), grids.main);
      gl.uniform4fv(gl.getUniformLocation(this.progTerrain, 'uGridBack'), grids.back);
    }
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uKeyColor'), pal.key_light);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uRimColor'), pal.rim_light);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uAmbientColor'), pal.ambient);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uWaterColor'), pal.water);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uFogColor'), pal.fog);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uBgColor'), pal.bg);
    gl.uniform3fv(gl.getUniformLocation(this.progTerrain, 'uCamPos'), this.camPos);

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.heightTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uHeightTex'), 0);
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.tileAtlas);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uTileAtlas'), 1);
    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, this.tileGridTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uTileGrid'), 2);
    gl.activeTexture(gl.TEXTURE3);
    gl.bindTexture(gl.TEXTURE_2D, this.backGridTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uFallbackGrid'), 3);
    gl.activeTexture(gl.TEXTURE4);
    gl.bindTexture(gl.TEXTURE_2D, this.detailNormTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uDetailNormTex'), 4);
    gl.activeTexture(gl.TEXTURE5);
    gl.bindTexture(gl.TEXTURE_2D, this.detailNoiseTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uDetailNoiseTex'), 5);
    gl.activeTexture(gl.TEXTURE6);
    gl.bindTexture(gl.TEXTURE_2D, this.iceCracksTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uIceCracksTex'), 6);
    gl.activeTexture(gl.TEXTURE7);
    gl.bindTexture(gl.TEXTURE_2D, this.nativeSurfaceTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uNativeSurfaceTex'), 7);
    gl.activeTexture(gl.TEXTURE8);
    gl.bindTexture(gl.TEXTURE_2D, this.terrainNormTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uTerrainNormTex'), 8);
    gl.activeTexture(gl.TEXTURE9);
    gl.bindTexture(gl.TEXTURE_2D, this.waterMaskTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uWaterMaskTex'), 9);
    gl.activeTexture(gl.TEXTURE10);
    gl.bindTexture(gl.TEXTURE_2D, this.flowTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uFlowTex'), 10);
    gl.activeTexture(gl.TEXTURE11);
    gl.bindTexture(gl.TEXTURE_2D, this.shadowMapTex);
    gl.uniform1i(gl.getUniformLocation(this.progTerrain, 'uShadowMap'), 11);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uHasDetail'), this.detailLoadedCount >= 2 ? 1.0 : 0.0);
    gl.uniform1f(gl.getUniformLocation(this.progTerrain, 'uIsIcy'), this.weatherMode === 0 ? 1.0 : 0.0);

    gl.bindVertexArray(this.vaoTerrain);
    gl.drawElements(gl.TRIANGLES, this.terrainIndexCount, gl.UNSIGNED_INT, 0);

    // PASS 2B: Native 3D Landmark & Building Meshes (Tyr's Temple, Realm Towers, Bridges, POI Models)
    if (this.useNative3D && this.hasNativeProps && this.propsIndexCount > 0 && this.progProps && this.vaoProps) {
      gl.useProgram(this.progProps);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.progProps, 'uVP'), false, this.vp);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.progProps, 'uLightVP'), false, this.lightVP);
      gl.uniform2f(gl.getUniformLocation(this.progProps, 'uWorldSize'), this.worldW, this.worldH);
      gl.uniform1f(gl.getUniformLocation(this.progProps, 'uMode3D'), this.mode3D ? 1.0 : 0.0);
      gl.uniform1f(gl.getUniformLocation(this.progProps, 'uHasNormAtlas'), this.hasNormalAtlas ? 1.0 : 0.0);
      gl.uniform1f(gl.getUniformLocation(this.progProps, 'uHasShadowMap'), this.hasShadowMap ? 1.0 : 0.0);
      gl.uniform1f(gl.getUniformLocation(this.progProps, 'uShadowRes'), this.shadowRes || 1024.0);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uKeyColor'), pal.key_light);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uRimColor'), pal.rim_light);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uAmbientColor'), pal.ambient);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uFogColor'), pal.fog);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uBgColor'), pal.bg);
      gl.uniform3fv(gl.getUniformLocation(this.progProps, 'uCamPos'), this.camPos);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.propsAtlasTex);
      gl.uniform1i(gl.getUniformLocation(this.progProps, 'uAtlasTex'), 0);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, this.propsNormTex);
      gl.uniform1i(gl.getUniformLocation(this.progProps, 'uNormAtlasTex'), 1);
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, this.shadowMapTex);
      gl.uniform1i(gl.getUniformLocation(this.progProps, 'uShadowMap'), 2);
      gl.bindVertexArray(this.vaoProps);
      gl.drawElements(gl.TRIANGLES, this.propsIndexCount, gl.UNSIGNED_INT, 0);
    }

    // PASS 2C: Volumetric Drifting Mist Clouds above the Carved Diorama (fade out cleanly when zoomed in close!)
    if (this.useNative3D && this.hasNativeSurface && this.weatherEnabled && this.mode3D && this.hasFogCloud && this.progClouds && this.vaoClouds && this.cloudVertCount > 0) {
      var cloudOp = clamp((this.dist - 620.0) / 1100.0, 0.0, 0.22);
      if (this.realmKey === 'muspelheim' || this.realmKey === 'alfheim') cloudOp *= 0.65;
      if (cloudOp > 0.005) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.useProgram(this.progClouds);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.progClouds, 'uVP'), false, this.vp);
      gl.uniform2f(gl.getUniformLocation(this.progClouds, 'uWorldSize'), this.worldW, this.worldH);
      gl.uniform1f(gl.getUniformLocation(this.progClouds, 'uHeightAmp'), this.heightAmp);
      gl.uniform1f(gl.getUniformLocation(this.progClouds, 'uTime'), tSec);
      gl.uniform1f(gl.getUniformLocation(this.progClouds, 'uOpacity'), cloudOp);
      gl.uniform3fv(gl.getUniformLocation(this.progClouds, 'uKeyColor'), pal.key_light);
      gl.uniform3fv(gl.getUniformLocation(this.progClouds, 'uAmbientColor'), pal.ambient);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, this.fogCloudTex);
      gl.uniform1i(gl.getUniformLocation(this.progClouds, 'uCloudTex'), 0);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, this.cloudNormTex);
      gl.uniform1i(gl.getUniformLocation(this.progClouds, 'uCloudNormTex'), 1);
      gl.bindVertexArray(this.vaoClouds);
      gl.drawArrays(gl.TRIANGLES, 0, this.cloudVertCount);
      }
    }

    // PASS 3 & 4: Additive 3D Waypoint Beacon & 3D Kratos Trail
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.depthMask(false);
    gl.useProgram(this.progRibbon);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progRibbon, 'uVP'), false, this.vp);
    var locCol = gl.getUniformLocation(this.progRibbon, 'uColor');
    var locMult = gl.getUniformLocation(this.progRibbon, 'uMult');
    var locTime = gl.getUniformLocation(this.progRibbon, 'uTime');
    var locPulse = gl.getUniformLocation(this.progRibbon, 'uPulse');
    gl.uniform1f(locTime, tSec);

    if (this.waypoint && this.wpBeamCount > 0) {
      var ringBreath = 0.86 + 0.14 * Math.sin(tSec * 3.0);
      gl.uniform3fv(locCol, this.waypoint.rgb);
      gl.uniform1f(locPulse, 1.0);
      gl.uniform1f(locMult, 0.95);
      gl.bindVertexArray(this.vaoWpBeam);
      gl.drawArrays(gl.TRIANGLES, 0, this.wpBeamCount);
      gl.uniform1f(locPulse, 0.0);
      gl.uniform1f(locMult, ringBreath);
      gl.bindVertexArray(this.vaoWpRing);
      gl.drawArrays(gl.LINES, 0, this.wpRingCount);
    }

    if (this.routeRibbonCount > 0) {
      var routePulse = 0.76 + 0.14 * Math.sin(tSec * 2.6);
      gl.uniform3fv(locCol, this.routeColor);
      gl.uniform1f(locPulse, 0.0);
      gl.uniform1f(locMult, routePulse);
      gl.bindVertexArray(this.vaoRouteRibbon);
      gl.drawArrays(gl.TRIANGLES, 0, this.routeRibbonCount);
      if (this.routeNodeCount > 0) {
        gl.uniform1f(locPulse, 1.0);
        gl.uniform1f(locMult, 0.72);
        gl.bindVertexArray(this.vaoRouteNodes);
        gl.drawArrays(gl.TRIANGLES, 0, this.routeNodeCount);
      }
    }

    if (this.showTrail && this.trailLineCount > 0) {
      gl.uniform3fv(locCol, pal.trail);
      gl.uniform1f(locPulse, 0.0);
      gl.uniform1f(locMult, 0.88);
      gl.bindVertexArray(this.vaoTrailLine);
      gl.drawArrays(gl.TRIANGLES, 0, this.trailLineCount);
      if (this.trailTickCount > 0) {
        gl.uniform1f(locMult, 0.45);
        gl.bindVertexArray(this.vaoTrailTicks);
        gl.drawArrays(gl.LINES, 0, this.trailTickCount);
      }
    }

    if (this.weatherEnabled && this.mode3D && this.progParticles && this.vaoParticles) {
      var dpr = Math.min(window.devicePixelRatio || 1, 2.5);
      gl.blendFunc(gl.SRC_ALPHA, this.weatherMode === 0 ? gl.ONE_MINUS_SRC_ALPHA : gl.ONE);
      gl.useProgram(this.progParticles);
      gl.uniformMatrix4fv(gl.getUniformLocation(this.progParticles, 'uVP'), false, this.vp);
      gl.uniform2f(gl.getUniformLocation(this.progParticles, 'uWorldSize'), this.worldW, this.worldH);
      gl.uniform1f(gl.getUniformLocation(this.progParticles, 'uTime'), tSec);
      gl.uniform1f(gl.getUniformLocation(this.progParticles, 'uWeatherMode'), this.weatherMode);
      gl.uniform1f(gl.getUniformLocation(this.progParticles, 'uDpr'), dpr);
      var wCol = this.weatherMode === 0 ? [0.92, 0.96, 1.0] : (this.weatherMode === 1 ? [1.0, 0.56, 0.22] : pal.beacon);
      gl.uniform3fv(gl.getUniformLocation(this.progParticles, 'uColor'), wCol);
      gl.bindVertexArray(this.vaoParticles);
      gl.drawArrays(gl.POINTS, 0, this.particleCount);
    }

    gl.depthMask(true);
    gl.disable(gl.BLEND);
    gl.bindVertexArray(null);
  };

  MapView.prototype._apply = function () {
    if (this.hasWebGL2) {
      this._updateMatrices();
      this._renderGL();
    }
    this._projectOverlay();
  };

  MapView.prototype._rafLoop = function () {
    var self = this;
    var lastBeaconAt = 0;
    function step(now) {
      if (self.animTarget) {
        var a = 0.16;
        self.targetX  += (self.animTarget.x - self.targetX) * a;
        self.targetZ  += (self.animTarget.z - self.targetZ) * a;
        self.dist     += (self.animTarget.dist - self.dist) * a;
        self.pitchDeg += (self.animTarget.pitch - self.pitchDeg) * a;
        self.yawDeg   += (self.animTarget.yaw - self.yawDeg) * a;
        if (
          Math.abs(self.animTarget.x - self.targetX) < 0.6 &&
          Math.abs(self.animTarget.z - self.targetZ) < 0.6 &&
          Math.abs(self.animTarget.dist - self.dist) < 1.2 &&
          Math.abs(self.animTarget.pitch - self.pitchDeg) < 0.08 &&
          Math.abs(self.animTarget.yaw - self.yawDeg) < 0.08
        ) {
          self.targetX = self.animTarget.x;
          self.targetZ = self.animTarget.z;
          self.dist = self.animTarget.dist;
          self.pitchDeg = self.animTarget.pitch;
          self.yawDeg = self.animTarget.yaw;
          self.animTarget = null;
        }
        self._clamp();
        self.dirty = true;
      } else if (!self.dragging && (Math.abs(self.vx) > 0.12 || Math.abs(self.vz) > 0.12)) {
        self.targetX += self.vx;
        self.targetZ += self.vz;
        self.vx *= 0.89;
        self.vz *= 0.89;
        self._clamp();
        self.dirty = true;
      } else if (!self.paused && !self.isSoftwareGL && (self.waypoint || self.routePoints.length > 1 || (self.weatherEnabled && self.mode3D)) && self.hasWebGL2 && (now - lastBeaconAt >= 33)) {
        lastBeaconAt = now;
        self.dirty = true;
      }
      if (self.dirty) {
        self.dirty = false;
        self._apply();
      }
      requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  };

  // ══════════ 0-DRIFT GOOGLE MAPS MULTITOUCH + MOUSE EVENTS ══════════
  MapView.prototype._bindEvents = function () {
    var self = this;
    this.el.addEventListener('contextmenu', function (e) { e.preventDefault(); });

    this.el.addEventListener('wheel', function (e) {
      e.preventDefault();
      var step = e.ctrlKey ? clamp(-e.deltaY * 0.012, -0.45, 0.45) : (e.deltaY < 0 ? 0.5 : -0.5);
      self.zoomAt(e.clientX, e.clientY, self.zoom + step);
    }, { passive: false });

    this.el.addEventListener('dblclick', function (e) {
      if (e.target.closest('.leaflet-marker-icon')) return;
      self.zoomAt(e.clientX, e.clientY, self.zoom + 1);
    });

    this.el.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.leaflet-marker-icon')) return;
      e.preventDefault();
      self._hideTip();
      try { self.el.setPointerCapture(e.pointerId); } catch (_) {}
      self.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      self.dragging = true;
      self.animTarget = null;
      self.vx = 0; self.vz = 0;
      self.el.classList.add('dragging');
      if (self.pointers.size === 1) {
        self.moved = false;
        self.wasMultiTouch = false;
        self.downPos = { x: e.clientX, y: e.clientY, btn: e.button };
        self.dragMode = (e.button === 2 || e.shiftKey || e.ctrlKey) ? 'orbit' : 'pan';
      } else if (self.pointers.size === 2) {
        self.moved = true;
        self.wasMultiTouch = true;
        var pts = Array.from(self.pointers.values());
        var dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        var center = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 };
        var ang = Math.atan2(pts[1].y - pts[0].y, pts[1].x - pts[0].x);
        self.lastPinchDist = dist;
        self.lastCenter = center;
        self.lastAngle = ang;
        self.twoStart = { dist: dist, center: center, ang: ang, pts: [{ x: pts[0].x, y: pts[0].y }, { x: pts[1].x, y: pts[1].y }] };
        self.twoMode = null;
        self.twistUnlocked = false;
      }
    });

    this.el.addEventListener('pointermove', function (e) {
      if (!self.pointers.has(e.pointerId)) return;
      var prev = self.pointers.get(e.pointerId);
      var cur = { x: e.clientX, y: e.clientY };
      self.pointers.set(e.pointerId, cur);

      if (!self.hasWebGL2) {
        var pArr = Array.from(self.pointers.values());
        var mid = pArr.length > 1 ? [(pArr[0].x + pArr[1].x) / 2, (pArr[0].y + pArr[1].y) / 2] : [cur.x, cur.y];
        var dx2 = cur.x - prev.x, dy2 = cur.y - prev.y;
        if (!self.moved && Math.hypot(dx2, dy2) > 3) { self.moved = true; self.emit('dragstart', e); }
        var cp = point(self.center, self.zoom);
        self.center = unpoint([cp[0] - dx2, cp[1] - dy2], self.zoom);
        self.draw();
        return;
      }

      if (self.pointers.size === 1) {
        var dx = cur.x - prev.x;
        var dy = cur.y - prev.y;
        if (self.downPos && Math.hypot(cur.x - self.downPos.x, cur.y - self.downPos.y) > 4) {
          if (!self.moved) { self.moved = true; self.emit('dragstart', e); }
        }
        if (self.dragMode === 'orbit') {
          self.autoPitch = false;
          self.yawDeg -= dx * 0.34;
          self.pitchDeg = clamp(self.pitchDeg + dy * 0.25, 0, MAX_PITCH);
          self.mode3D = self.pitchDeg > 2;
        } else {
          var before = self.unprojectGround(prev.x, prev.y);
          var after = self.unprojectGround(cur.x, cur.y);
          var gx = 0, gz = 0;
          var maxStep = self.dist * 0.45;
          if (before && after && Math.hypot(before[0] - after[0], before[1] - after[1]) < maxStep) {
            gx = before[0] - after[0];
            gz = before[1] - after[1];
          } else {
            var speed = self.dist * 0.0012;
            var yRad = self.yawDeg * Math.PI / 180;
            var c = Math.cos(yRad), s = Math.sin(yRad);
            gx = (-dx * c + dy * s) * speed;
            gz = (-dx * s - dy * c) * speed;
          }
          self.targetX += gx;
          self.targetZ += gz;
          self.vx = self.vx * 0.35 + gx * 0.65;
          self.vz = self.vz * 0.35 + gz * 0.65;
          self._clamp();
          self._updateMatrices();
          if (self.moved) self.emit('dragstart', e);
        }
        self.dirty = true;
      } else if (self.pointers.size === 2) {
        var pts = Array.from(self.pointers.values());
        var dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        var center = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 };
        var ang = Math.atan2(pts[1].y - pts[0].y, pts[1].x - pts[0].x);

        if (!self.twoMode && self.twoStart) {
          var d0x = pts[0].x - self.twoStart.pts[0].x;
          var d0y = pts[0].y - self.twoStart.pts[0].y;
          var d1x = pts[1].x - self.twoStart.pts[1].x;
          var d1y = pts[1].y - self.twoStart.pts[1].y;
          var m0 = Math.hypot(d0x, d0y);
          var m1 = Math.hypot(d1x, d1y);
          var avgDy = (d0y + d1y) * 0.5;
          var avgDx = (d0x + d1x) * 0.5;
          var totalPinch = Math.abs(dist - self.twoStart.dist);
          var totalTwist = Math.abs(wrapDeg(ang - self.twoStart.ang));
          var sepX = Math.abs(pts[1].x - pts[0].x);
          var sepY = Math.abs(pts[1].y - pts[0].y);
          if (
            m0 >= 6 && m1 >= 6 &&
            Math.abs(avgDy) > 12 &&
            Math.sign(d0y) === Math.sign(d1y) &&
            Math.abs(avgDy) > Math.abs(avgDx) * 1.45 &&
            totalPinch < 22 &&
            totalTwist < 9 &&
            sepX > sepY * 0.6
          ) {
            self.twoMode = 'tilt';
          } else if (
            ((m0 >= 4 && m1 >= 4) || totalPinch > 24 || Math.max(m0, m1) > 95) &&
            (totalPinch > 14 || totalTwist > 8 || Math.hypot(avgDx, avgDy) > 18)
          ) {
            self.twoMode = 'transform';
          } else {
            self.dirty = true;
            return;
          }
        }

        if (self.twoMode === 'tilt' && self.lastCenter) {
          var dyTilt = center.y - self.lastCenter.y;
          self.autoPitch = false;
          self.pitchDeg = clamp(self.pitchDeg - dyTilt * 0.30, 0, MAX_PITCH);
          self.mode3D = self.pitchDeg > 2;
        } else {
          var anchor = self.lastCenter ? self.unprojectGround(self.lastCenter.x, self.lastCenter.y) : null;
          if (self.lastPinchDist > 10 && dist > 10) {
            self.dist = clamp(self.dist * (self.lastPinchDist / dist), self._minDist(), self._maxDist());
            if (self.autoPitch) self.pitchDeg = self._pitchForDist(self.dist);
          }
          if (self.lastAngle != null && self.twoStart) {
            var tw = Math.abs(wrapDeg(ang - self.twoStart.ang));
            if (!self.twistUnlocked && tw > 6.5) {
              self.twistUnlocked = true;
            }
            if (self.twistUnlocked) {
              var da = wrapDeg(ang - self.lastAngle);
              if (Math.abs(da) < 30) {
                self.yawDeg += da;
              }
            }
          }
          if (anchor) {
            self._updateMatrices();
            var after2 = self.unprojectGround(center.x, center.y);
            var maxStep2 = self.dist * 0.45;
            if (after2 && Math.hypot(anchor[0] - after2[0], anchor[1] - after2[1]) < maxStep2) {
              self.targetX += (anchor[0] - after2[0]);
              self.targetZ += (anchor[1] - after2[1]);
              self._clamp();
              self._updateMatrices();
            }
          } else {
            self._updateMatrices();
          }
        }
        self.lastPinchDist = dist;
        self.lastCenter = center;
        self.lastAngle = ang;
        self.vx = 0; self.vz = 0;
        self.moved = true;
        self.dirty = true;
        self.emit('dragstart', e);
      }
    });

    function up(e) {
      if (!self.pointers.has(e.pointerId)) return;
      var wasSingleClick = self.pointers.size === 1 && !self.moved && !self.wasMultiTouch &&
        self.downPos && self.downPos.btn === 0;
      self.pointers.delete(e.pointerId);
      if (self.pointers.size < 2) {
        self.lastPinchDist = 0;
        self.lastCenter = null;
        self.lastAngle = null;
        self.twoStart = null;
        self.twoMode = null;
        self.twistUnlocked = false;
      }
      if (self.pointers.size === 1) {
        self.vx = 0; self.vz = 0;
        self.moved = true;
      }
      if (self.pointers.size === 0) {
        self.dragging = false;
        self.wasMultiTouch = false;
        self.el.classList.remove('dragging');
        if (wasSingleClick) self.emit('click', e);
      }
    }
    this.el.addEventListener('pointerup', up);
    this.el.addEventListener('pointercancel', up);
  };

  // ══════════ TILES, LAYER GROUP & MARKER ══════════
  function Tiles(url, opts) {
    this.url = url;
    this.options = opts || {};
    this.images = new window.Map();
  }
  Tiles.prototype.addTo = function (map) {
    this.map = map;
    map.tileLayer = this;
    var r = extractRealmFromUrl(this.url);
    if (r) map.setRealm(r);
    map.draw();
    return this;
  };
  Tiles.prototype.setUrl = function (url) {
    this.url = url;
    this.images.forEach(function (i) { i.remove(); });
    this.images.clear();
    if (this.map) {
      var r = extractRealmFromUrl(url);
      if (r && r !== this.map.realmKey) this.map.setRealm(r);
      this.map._resetAtlas();
      this.map.draw();
    }
    return this;
  };

  function Group() { this.children = new Set(); }
  Group.prototype.addTo = function (map) { this.map = map; return this; };
  Group.prototype.clearLayers = function () {
    var map = this.map;
    this.children.forEach(function (c) { map.removeLayer(c); });
    this.children.clear();
    return this;
  };

  function Marker(ll, opts) {
    this.ll = ll;
    this.options = opts || {};
    this.icon = this.options.icon || {};
    this.handlers = {};
  }
  Marker.prototype.addTo = function (target) {
    var map = target instanceof Group ? target.map : target;
    if (target instanceof Group) target.children.add(this);
    this.map = map;
    map.layers.add(this);
    if (!this.el) {
      this.el = document.createElement('div');
      this.el.className = 'leaflet-marker-icon';
      var self = this;
      this.el.addEventListener('click', function (e) {
        e.stopPropagation();
        if (self.handlers.click) self.handlers.click(e);
      });
    }
    this.setIcon(this.icon);
    if (this.label) {
      this.el.title = this.label;
      this.el.setAttribute('aria-label', this.label);
      var tipMarker = this;
      this.el.addEventListener('mouseenter', function () { tipMarker.map && tipMarker.map._showTip(tipMarker); });
      this.el.addEventListener('mouseleave', function () { tipMarker.map && tipMarker.map._hideTip(tipMarker); });
      this.el.addEventListener('focus', function () { tipMarker.map && tipMarker.map._showTip(tipMarker); });
      this.el.addEventListener('blur', function () { tipMarker.map && tipMarker.map._hideTip(tipMarker); });
      this.el.onkeydown = function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.currentTarget.click(); }
      };
    }
    map.markerPane.appendChild(this.el);
    map.draw();
    return this;
  };
  Marker.prototype.setIcon = function (icon) {
    this.icon = icon;
    if (this.el) {
      this.el.className = 'leaflet-marker-icon ' + (icon.className || '');
      this.el.innerHTML = icon.html || '';
      this.el.style.width = (icon.iconSize || [28, 28])[0] + 'px';
      this.el.style.height = (icon.iconSize || [28, 28])[1] + 'px';
      this.el.style.zIndex = String(1000 + (this.options.zIndexOffset || 0));
      if (this.options.interactive === false) this.el.setAttribute('aria-hidden', 'true');
      else { this.el.tabIndex = 0; this.el.setAttribute('role', 'button'); }
    }
    if (this.map) this.map.draw();
    return this;
  };
  Marker.prototype.bindTooltip = function (label) {
    var text = document.createElement('span');
    text.innerHTML = label;
    this.label = text.textContent;
    return this;
  };
  Marker.prototype.on = function (event, fn) { this.handlers[event] = fn; return this; };
  Marker.prototype.getElement = function () { return this.el; };
  Marker.prototype.setLatLng = function (ll) {
    this.ll = ll;
    if (this.map) this.map.draw();
    return this;
  };

  window.L = {
    map: function (id, o) { return new MapView(id, o); },
    tileLayer: function (url, o) { return new Tiles(url, o); },
    layerGroup: function () { return new Group(); },
    marker: function (ll, o) { return new Marker(ll, o); },
    divIcon: function (o) { return o; },
    latLngBounds: bounds,
    DomEvent: { stopPropagation: function (e) { e.stopPropagation(); } },
    _project: point,
    _unproject: unpoint
  };
})();
