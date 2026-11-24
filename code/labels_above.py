"""Put each node's label directly above its node.

Every label starts centred just above the edge of its own node. Labels that would overlap other labels,
large nodes or the legend are nudged apart, but never further than `max_shift` points from their start;
a thin leader line is drawn only when a label had to move noticeably. Offsets are in points relative to the
node, so the label stays with its node however the axes are later resized.
"""
import numpy as np
import matplotlib.patheffects as pe

HALO = [pe.withStroke(linewidth=2.2, foreground='white')]


def place_labels_above(fig, ax, items, obstacles_nodes=(), obstacle_boxes=(), max_shift=16, iters=500,
                       line_color='#888', line_width=0.4, gap=1.5, min_obstacle_r=6):
    """items: dicts with x, y (data), text, r (node radius in points), kw (Text kwargs), below (bool), fixed (bool).
    obstacles_nodes: (x, y, r_points) for all nodes; only those with r >= min_obstacle_r repel labels.
    obstacle_boxes: matplotlib artists (e.g. legends) that labels must keep clear of."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    k = 72.0 / fig.dpi                                   # pixels -> points
    T = ax.transData
    boxes = []
    for it in items:
        t = ax.text(0, 0, it['text'], **it['kw'])
        bb = t.get_window_extent(rend)
        t.remove()
        w, h = bb.width * k, bb.height * k
        ax0, ay0 = (T.transform((it['x'], it['y'])) * k)
        dy0 = -(it['r'] + gap + h / 2) if it.get('below') else (it['r'] + gap + h / 2)
        boxes.append(dict(ax=ax0, ay=ay0, w=w, h=h, dx=0.0, dy=dy0, dy0=dy0, fixed=it.get('fixed', False),
                          wt=1.0 / max(it['kw'].get('fontsize', 9), 1)))
    obs = [(*(T.transform((x, y)) * k), r) for x, y, r in obstacles_nodes if r >= min_obstacle_r]
    obb = []
    for art in obstacle_boxes:
        bb = art.get_window_extent(rend)
        obb.append(((bb.x0 + bb.x1) / 2 * k, (bb.y0 + bb.y1) / 2 * k, bb.width * k / 2, bb.height * k / 2))
    n = len(boxes)
    for _ in range(iters):
        moved = False
        cx = np.array([b['ax'] + b['dx'] for b in boxes]); cy = np.array([b['ay'] + b['dy'] for b in boxes])
        for i in range(n):
            bi = boxes[i]
            for j in range(i + 1, n):
                bj = boxes[j]
                ox = (bi['w'] + bj['w']) / 2 + 1.5 - abs(cx[i] - cx[j])
                oy = (bi['h'] + bj['h']) / 2 + 0.5 - abs(cy[i] - cy[j])
                if ox > 0 and oy > 0:
                    wi = 0 if bi['fixed'] else bi['wt']; wj = 0 if bj['fixed'] else bj['wt']
                    if wi + wj == 0: continue
                    si, sj = wi / (wi + wj), wj / (wi + wj)
                    if oy < ox:                          # separate vertically when that is the shorter move
                        s = 1 if cy[i] >= cy[j] else -1
                        bi['dy'] += s * oy * si * 0.6; bj['dy'] -= s * oy * sj * 0.6
                    else:
                        s = 1 if cx[i] >= cx[j] else -1
                        bi['dx'] += s * ox * si * 0.6; bj['dx'] -= s * ox * sj * 0.6
                    moved = True
        for b in boxes:
            if b['fixed']: continue
            bx, by = b['ax'] + b['dx'], b['ay'] + b['dy']
            for (ox_, oy_, r) in obs:
                if abs(ox_ - b['ax']) < 0.5 and abs(oy_ - b['ay']) < 0.5: continue   # own node
                px = b['w'] / 2 + r - abs(bx - ox_); py = b['h'] / 2 + r - abs(by - oy_)
                if px > 0 and py > 0:
                    if py < px: b['dy'] += (1 if by >= oy_ else -1) * py * 0.5
                    else: b['dx'] += (1 if bx >= ox_ else -1) * px * 0.5
                    moved = True
            for (ox_, oy_, hw, hh) in obb:
                px = b['w'] / 2 + hw - abs(bx - ox_); py = b['h'] / 2 + hh - abs(by - oy_)
                if px > 0 and py > 0:
                    if py < px: b['dy'] += (1 if by >= oy_ else -1) * py * 0.5
                    else: b['dx'] += (1 if bx >= ox_ else -1) * px * 0.5
                    moved = True
            # pull back towards the start, keep within max_shift, never onto its own node
            b['dx'] *= 0.97; b['dy'] = b['dy0'] + (b['dy'] - b['dy0']) * 0.97
            ddx, ddy = b['dx'], b['dy'] - b['dy0']
            d = (ddx ** 2 + ddy ** 2) ** 0.5
            if d > max_shift: b['dx'] *= max_shift / d; b['dy'] = b['dy0'] + ddy * max_shift / d
            if b['dy0'] > 0: b['dy'] = max(b['dy'], b['dy0'] - 0.5)
            else: b['dy'] = min(b['dy'], b['dy0'] + 0.5)
        if not moved: break
    out = []
    for it, b in zip(items, boxes):
        shift = ((b['dx']) ** 2 + (b['dy'] - b['dy0']) ** 2) ** 0.5
        kw = dict(it['kw']); kw.update(ha='center', va='center')
        arrow = dict(arrowstyle='-', color=line_color, lw=line_width, shrinkA=0, shrinkB=it['r'] + 1) if shift > 5 else None
        a = ax.annotate(it['text'], xy=(it['x'], it['y']), xytext=(b['dx'], b['dy']), textcoords='offset points',
                        arrowprops=arrow, annotation_clip=False, **kw)
        a.set_path_effects(HALO)
        out.append(a)
    return out
