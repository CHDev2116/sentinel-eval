"""Reliability diagram SVG from calibration metrics."""

from __future__ import annotations

from pathlib import Path

from sentinel_eval.domain.suite_metrics import CalibrationMetrics, ReliabilityBin


def reliability_diagram_svg(
    bins: list[ReliabilityBin],
    *,
    width: int = 480,
    height: int = 320,
    title: str = "Calibration reliability diagram",
) -> str:
    """Generate SVG string (predicted vs actual unsafe rate per bin)."""
    margin = 48
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    x0, y0 = margin, margin

    def x_pos(mean_pred: float) -> float:
        return x0 + mean_pred * plot_w

    def y_pos(mean_actual: float) -> float:
        return y0 + plot_h - mean_actual * plot_h

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a"/>',
        f'<text x="{margin}" y="28" fill="#f8fafc" font-size="14" font-family="system-ui,sans-serif">'
        f"{title}</text>",
        f'<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0 + plot_h}" stroke="#64748b"/>',
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + plot_h}" stroke="#64748b"/>',
        f'<line x1="{x0}" y1="{y0 + plot_h}" x2="{x0 + plot_w}" y2="{y0}" '
        f'stroke="#334155" stroke-dasharray="4"/>',
        f'<text x="{x0 + plot_w / 2}" y="{height - 12}" fill="#94a3b8" font-size="11" '
        f'text-anchor="middle">Mean predicted P(unsafe)</text>',
        f'<text x="14" y="{y0 + plot_h / 2}" fill="#94a3b8" font-size="11" '
        f'transform="rotate(-90 14 {y0 + plot_h / 2})" text-anchor="middle">'
        f"Mean actual unsafe</text>",
    ]

    for b in bins:
        cx = x_pos(b.mean_predicted)
        cy = y_pos(b.mean_actual)
        r = max(4, min(14, 4 + b.count))
        elements.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#38bdf8" fill-opacity="0.75" '
            f'stroke="#0ea5e9"/>'
        )
        elements.append(
            f'<text x="{cx:.1f}" y="{cy - r - 4:.1f}" fill="#cbd5e1" font-size="9" '
            f'text-anchor="middle">n={b.count}</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)


def write_reliability_chart(
    calibration: CalibrationMetrics | None,
    path: str | Path,
    *,
    title: str = "Calibration reliability diagram",
) -> Path | None:
    """Write SVG reliability diagram; returns path or None if no bins."""
    if calibration is None or not calibration.reliability_diagram:
        return None
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    svg = reliability_diagram_svg(calibration.reliability_diagram, title=title)
    out.write_text(svg, encoding="utf-8")
    return out
