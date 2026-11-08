/* Rasterizer z-buffer per-piksel: scanline dengan rentang-x analitik.
   Perspektif benar (1/z linear), Gouraud, alpha blend. Loop piksel di C. */
#include <math.h>

static inline float fmin3(float a, float b, float c) {
    float m = a < b ? a : b;
    return m < c ? m : c;
}
static inline float fmax3(float a, float b, float c) {
    float m = a > b ? a : b;
    return m > c ? m : c;
}

void raster(int W, int H, int n,
            const float *vx, const float *vy, const float *viz,
            const float *vc, const unsigned char *va,
            const unsigned char *vb, float *zbuf, unsigned char *rgb)
{
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

        /* l_i(sx,sy) = a_i*sx + c_i*sy + b_i */
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
        float r0 = vc[3 * i0], r1 = vc[3 * i1], r2 = vc[3 * i2];
        float g0 = vc[3 * i0 + 1], g1 = vc[3 * i1 + 1], g2 = vc[3 * i2 + 1];
        float b_0 = vc[3 * i0 + 2], b_1 = vc[3 * i1 + 2], b_2 = vc[3 * i2 + 2];
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
            float dz = a0 * z0 + a1 * z1 + a2 * z2;
            float dr = a0 * r0 + a1 * r1 + a2 * r2;
            float dg = a0 * g0 + a1 * g1 + a2 * g2;
            float db = a0 * b_0 + a1 * b_1 + a2 * b_2;
            int row = py * W;

            for (int px = lo; px <= hi; ++px) {
                int idx = row + px;
                if (iz > zbuf[idx]) {
                    if (!blend) zbuf[idx] = iz;
                    int c = idx * 3;
                    if (blend) {
                        float k = 1.0f - alpha;
                        rgb[c]     = (unsigned char)(rgb[c]     * k + rr * alpha);
                        rgb[c + 1] = (unsigned char)(rgb[c + 1] * k + gg * alpha);
                        rgb[c + 2] = (unsigned char)(rgb[c + 2] * k + bb * alpha);
                    } else {
                        rgb[c]     = (unsigned char)(rr < 0 ? 0 : (rr > 255 ? 255 : rr));
                        rgb[c + 1] = (unsigned char)(gg < 0 ? 0 : (gg > 255 ? 255 : gg));
                        rgb[c + 2] = (unsigned char)(bb < 0 ? 0 : (bb > 255 ? 255 : bb));
                    }
                }
                iz += dz; rr += dr; gg += dg; bb += db;
            }
        }
    }
}

/* Ambient occlusion murah dari z-buffer: 8 sampel kedalaman sekitar piksel.
   Daerah cekung / kontak antar objek jadi lebih gelap -> kesan volume. */
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
