/* Rasterizer z-buffer per-piksel: scanline analitik, perspektif benar (1/z),
   pencahayaan specular PER-PIKSEL dari normal terinterpolasi, dan mikro-tekstur
   prosedural dari posisi dunia (tanpa tekstur/gambar eksternal). */
#include <math.h>

static inline float fmin3(float a, float b, float c) {
    float m = a < b ? a : b;
    return m < c ? m : c;
}
static inline float fmax3(float a, float b, float c) {
    float m = a > b ? a : b;
    return m > c ? m : c;
}

/* LUT sinus 1024 entri: mikro-tekstur tanpa sinf per piksel. */
static float TBL[1024];
static float SLUT[3][256];
static int TBL_READY = 0;
static void init_tbl(void) {
    if (TBL_READY) return;
    for (int i = 0; i < 1024; ++i)
        TBL[i] = sinf((float)i * 6.28318530718f / 1024.0f);
    for (int k = 0; k < 3; ++k) {
        float e = (float)(16 << k);          /* 16, 32, 64 */
        for (int i = 0; i < 256; ++i)
            SLUT[k][i] = powf((float)i / 255.0f, e);
    }
    TBL_READY = 1;
}

void raster(int W, int H, int n,
            const float *vx, const float *vy, const float *viz,
            const float *vc, const float *vn, const float *vp,
            const unsigned char *va, const unsigned char *vb,
            const float *pm, const float *lit, const float *env,
            float *zbuf, unsigned char *rgb)
{
    init_tbl();
    const float h1x = lit[0], h1y = lit[1], h1z = lit[2];
    const float h2x = lit[3], h2y = lit[4], h2z = lit[5];
    const float sr = lit[6], sg = lit[7], sb = lit[8];

    for (int t = 0; t < n; ++t) {
        int i0 = 3 * t, i1 = i0 + 1, i2 = i0 + 2;
        float x0 = vx[i0], x1 = vx[i1], x2 = vx[i2];
        float y0 = vy[i0], y1 = vy[i1], y2 = vy[i2];

        int xa = (int)floorf(fmin3(x0, x1, x2));
        int xb = (int)ceilf(fmax3(x0, x1, x2));
        int ya = (int)floorf(fmin3(y0, y1, y2));
        int yb = (int)ceilf(fmax3(y0, y1, y2));
        if (xa < 0) xa = 0;
        if (ya < 0) ya = 0;
        if (xb >= W) xb = W - 1;
        if (yb >= H) yb = H - 1;
        if (xa > xb || ya > yb) continue;

        float den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
        if (den < 1e-8f && den > -1e-8f) continue;
        float invden = 1.0f / den;

        float a0 = (y1 - y2) * invden;
        float c0 = (x2 - x1) * invden;
        float b0 = (-(y1 - y2) * x2 - (x2 - x1) * y2) * invden;
        float a1 = (y2 - y0) * invden;
        float c1 = (x0 - x2) * invden;
        float b1 = (-(y2 - y0) * x2 - (x0 - x2) * y2) * invden;
        float a2 = -a0 - a1;
        float c2 = -c0 - c1;
        float b2 = 1.0f - b0 - b1;

        float z0 = viz[i0], z1 = viz[i1], z2 = viz[i2];
        int c0i = 9 * t, c1i = c0i + 3, c2i = c0i + 6;
        float r0 = vc[c0i], r1 = vc[c1i], r2 = vc[c2i];
        float g0 = vc[c0i + 1], g1 = vc[c1i + 1], g2 = vc[c2i + 1];
        float b_0 = vc[c0i + 2], b_1 = vc[c1i + 2], b_2 = vc[c2i + 2];
        float nx0 = vn[c0i], nx1 = vn[c1i], nx2 = vn[c2i];
        float ny0 = vn[c0i + 1], ny1 = vn[c1i + 1], ny2 = vn[c2i + 1];
        float nz0 = vn[c0i + 2], nz1 = vn[c1i + 2], nz2 = vn[c2i + 2];
        float wx0 = vp[c0i], wx1 = vp[c1i], wx2 = vp[c2i];
        float wy0 = vp[c0i + 1], wy1 = vp[c1i + 1], wy2 = vp[c2i + 1];
        float wz0 = vp[c0i + 2], wz1 = vp[c1i + 2], wz2 = vp[c2i + 2];

        float metal = pm[3 * t], shine = pm[3 * t + 1];
        int ipat = (int)(pm[3 * t + 2] + 0.5f);
        int lut = shine < 20.0f ? 0 : (shine < 44.0f ? 1 : 2);
        int metallic = metal > 0.02f;
        int ibl = metal > 0.55f;
        int enh = metallic || ipat;
        float alpha = (float)va[t] / 255.0f;
        int blend = vb[t];

        for (int py = ya; py <= yb; ++py) {
            float sy = (float)py + 0.5f;
            float B0 = c0 * sy + b0, B1 = c1 * sy + b1, B2 = c2 * sy + b2;
            int lo = xa, hi = xb;
            int empty = 0;

            if (a0 > 1e-10f) {
                int q = (int)ceilf(-B0 / a0 - 0.5f);
                if (q > lo) lo = q;
            } else if (a0 < -1e-10f) {
                int q = (int)floorf(-B0 / a0 - 0.5f);
                if (q < hi) hi = q;
            } else if (B0 < 0) empty = 1;

            if (a1 > 1e-10f) {
                int q = (int)ceilf(-B1 / a1 - 0.5f);
                if (q > lo) lo = q;
            } else if (a1 < -1e-10f) {
                int q = (int)floorf(-B1 / a1 - 0.5f);
                if (q < hi) hi = q;
            } else if (B1 < 0) empty = 1;

            if (a2 > 1e-10f) {
                int q = (int)ceilf(-B2 / a2 - 0.5f);
                if (q > lo) lo = q;
            } else if (a2 < -1e-10f) {
                int q = (int)floorf(-B2 / a2 - 0.5f);
                if (q < hi) hi = q;
            } else if (B2 < 0) empty = 1;

            if (empty || lo > hi) continue;
            if (lo < xa) lo = xa;
            if (hi > xb) hi = xb;
            if (lo > hi) continue;

            float sx = (float)lo + 0.5f;
            float p0 = a0 * sx + B0;
            float p1 = a1 * sx + B1;
            float p2 = 1.0f - p0 - p1;
            float iz = p0 * z0 + p1 * z1 + p2 * z2;
            float rr = p0 * r0 + p1 * r1 + p2 * r2;
            float gg = p0 * g0 + p1 * g1 + p2 * g2;
            float bb = p0 * b_0 + p1 * b_1 + p2 * b_2;
            float NX = 0, NY = 0, NZ = 0, WX = 0, WY = 0, WZ = 0;
            if (enh) {
                NX = p0 * nx0 + p1 * nx1 + p2 * nx2;
                NY = p0 * ny0 + p1 * ny1 + p2 * ny2;
                NZ = p0 * nz0 + p1 * nz1 + p2 * nz2;
                WX = p0 * wx0 + p1 * wx1 + p2 * wx2;
                WY = p0 * wy0 + p1 * wy1 + p2 * wy2;
                WZ = p0 * wz0 + p1 * wz1 + p2 * wz2;
            }
            float dz = a0 * z0 + a1 * z1 + a2 * z2;
            float dr = a0 * r0 + a1 * r1 + a2 * r2;
            float dg = a0 * g0 + a1 * g1 + a2 * g2;
            float db = a0 * b_0 + a1 * b_1 + a2 * b_2;
            float dNX = 0, dNY = 0, dNZ = 0, dWX = 0, dWY = 0, dWZ = 0;
            if (enh) {
                dNX = a0 * nx0 + a1 * nx1 + a2 * nx2;
                dNY = a0 * ny0 + a1 * ny1 + a2 * ny2;
                dNZ = a0 * nz0 + a1 * nz1 + a2 * nz2;
                dWX = a0 * wx0 + a1 * wx1 + a2 * wx2;
                dWY = a0 * wy0 + a1 * wy1 + a2 * wy2;
                dWZ = a0 * wz0 + a1 * wz1 + a2 * wz2;
            }
            int row = py * W;

            for (int px = lo; px <= hi; ++px) {
                int idx = row + px;
                if (iz > zbuf[idx]) {
                    if (!blend) zbuf[idx] = iz;
                    int c = idx * 3;
                    float tex = 1.0f;
                    float add = 0.0f;
                    float envr = 0.0f, envg = 0.0f, envb = 0.0f;
                    float invz = 1.0f / iz;
                    if (ipat) {
                        float wx = WX * invz, wy = WY * invz, wz = WZ * invz;
                        if (ipat == 1) {                 /* logam disikat */
                            tex = 0.945f + 0.055f * TBL[(int)(wy * 760.0f + wx * 23.0f) & 1023];
                        } else if (ipat == 2) {          /* papan PCB */
                            float v = TBL[(int)(wx * 330.0f) & 1023] *
                                      TBL[(int)(wz * 330.0f) & 1023];
                            tex = 0.925f + 0.075f * v;
                        } else if (ipat == 3) {          /* plastik gelap / gril */
                            tex = 0.900f + 0.100f * TBL[(int)((wx + wz) * 520.0f) & 1023];
                        } else if (ipat == 4) {          /* plastik sedang */
                            tex = 0.945f + 0.055f * TBL[(int)(wx * 410.0f + wz * 410.0f) & 1023];
                        } else {                         /* karet */
                            tex = 0.960f + 0.040f * TBL[(int)(wy * 900.0f) & 1023];
                        }
                    }
                    if (metallic) {
                        float nx = NX * invz, ny = NY * invz, nz = NZ * invz;
                        /* normalisasi Newton orde-1 (tanpa sqrt per piksel) */
                        float l2 = nx * nx + ny * ny + nz * nz;
                        float il = 1.5f - 0.5f * l2;
                        nx *= il; ny *= il; nz *= il;
                        float s1 = nx * h1x + ny * h1y + nz * h1z;
                        float s2 = nx * h2x + ny * h2y + nz * h2z;
                        s1 = s1 > 1.0f ? 1.0f : (s1 > 0.0f ? s1 : 0.0f);
                        s2 = s2 > 1.0f ? 1.0f : (s2 > 0.0f ? s2 : 0.0f);
                        float sp1 = SLUT[lut][(int)(s1 * 255.0f)];
                        float sp2 = SLUT[lut][(int)(s2 * 255.0f)];
                        float ndv = -nz;
                        ndv = ndv < 0.0f ? 0.0f : (ndv > 1.0f ? 1.0f : ndv);
                        float g = 1.0f - ndv;
                        float g2 = g * g, g4 = g2 * g2, g5 = g4 * g;
                        float fres = metal * 0.20f * g2;   /* Schlick, orde 5 */
                        add = metal * (0.88f * sp1 + 0.36f * sp2) + fres;
                        add *= 0.78f + 0.30f * tex;        /* goresan logam */
                        if (ibl) {
                            /* IBL matcap: pantulan studio dari normal view-space */
                            int ex = (int)((nx * 0.5f + 0.5f) * 63.0f);
                            int ey = (int)((0.5f - ny * 0.5f) * 63.0f);
                            ex = ex < 0 ? 0 : (ex > 63 ? 63 : ex);
                            ey = ey < 0 ? 0 : (ey > 63 ? 63 : ey);
                            const float *e = env + (ey * 64 + ex) * 3;
                            float ek = metal * (0.24f + 0.78f * g5 + 0.24f * g);
                            envr = e[0] * rr * ek;
                            envg = e[1] * gg * ek;
                            envb = e[2] * bb * ek;
                        }
                    }
                    float R = rr * tex + add * sr * 190.0f + envr;
                    float G = gg * tex + add * sg * 190.0f + envg;
                    float B = bb * tex + add * sb * 190.0f + envb;
                    R = R < 0.0f ? 0.0f : (R > 255.0f ? 255.0f : R);
                    G = G < 0.0f ? 0.0f : (G > 255.0f ? 255.0f : G);
                    B = B < 0.0f ? 0.0f : (B > 255.0f ? 255.0f : B);
                    if (blend) {
                        float k = 1.0f - alpha;
                        rgb[c]     = (unsigned char)(rgb[c]     * k + R * alpha);
                        rgb[c + 1] = (unsigned char)(rgb[c + 1] * k + G * alpha);
                        rgb[c + 2] = (unsigned char)(rgb[c + 2] * k + B * alpha);
                    } else {
                        rgb[c] = (unsigned char)R;
                        rgb[c + 1] = (unsigned char)G;
                        rgb[c + 2] = (unsigned char)B;
                    }
                }
                iz += dz; rr += dr; gg += dg; bb += db;
                NX += dNX; NY += dNY; NZ += dNZ;
                WX += dWX; WY += dWY; WZ += dWZ;
            }
        }
    }
}

/* Ambient occlusion murah dari z-buffer (fallback bila SSAO Numba nonaktif). */
void post(int W, int H, const float *zbuf, unsigned char *rgb)
{
    const int r1 = 4, r2 = 11;
    for (int y = r2; y < H - r2; y += 2) {
        int row = y * W;
        for (int x = r2; x < W - r2; x += 2) {
            int idx = row + x;
            float iz = zbuf[idx];
            if (iz <= 0.0f) continue;
            float lim = iz * 1.07f;
            float occ = 0.0f;
            occ += zbuf[idx - r1] > lim;
            occ += zbuf[idx + r1] > lim;
            occ += zbuf[idx - r1 * W] > lim;
            occ += zbuf[idx + r1 * W] > lim;
            occ += zbuf[idx - r2 - r2 * W] > lim;
            occ += zbuf[idx + r2 - r2 * W] > lim;
            occ += zbuf[idx - r2 + r2 * W] > lim;
            occ += zbuf[idx + r2 + r2 * W] > lim;
            if (occ <= 0.0f) continue;
            float ao = 1.0f - 0.34f * (occ / 8.0f);
            for (int dy = 0; dy < 2; ++dy) {
                int c = (idx + dy * W) * 3;
                for (int dx = 0; dx < 2; ++dx) {
                    int k = c + dx * 3;
                    rgb[k]     = (unsigned char)(rgb[k]     * ao);
                    rgb[k + 1] = (unsigned char)(rgb[k + 1] * ao);
                    rgb[k + 2] = (unsigned char)(rgb[k + 2] * ao);
                }
            }
        }
    }
}
