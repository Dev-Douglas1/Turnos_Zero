"""Exporta cenários completos e objetos independentes para PNGs do Tkinter."""
from pathlib import Path
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
SCENE_DIR = ROOT / "assets" / "ambientes"
OBJECT_DIR = ROOT / "assets" / "objetos"
SCENE_NAMES = (
    "agencia_menu",
    "cidade_noturna",
    "loja_24_horas",
    "edificio_residencial",
    "cinema_ultima_sessao",
    "laboratorio_experimental",
)


def export_svg(source: Path, target: Path, size: tuple[int, int]) -> None:
    if not source.is_file():
        raise SystemExit(f"Arte SVG ausente: {source}")
    cairosvg.svg2png(
        url=str(source),
        write_to=str(target),
        output_width=size[0],
        output_height=size[1],
    )
    print(f"Exportado: {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")


def main() -> None:
    for name in SCENE_NAMES:
        export_svg(
            SCENE_DIR / f"{name}.svg",
            SCENE_DIR / f"{name}.png",
            (834, 469),
        )

    object_sources = sorted(OBJECT_DIR.glob("*.svg"))
    if not object_sources:
        raise SystemExit(f"Nenhum objeto SVG encontrado em {OBJECT_DIR}")
    for source in object_sources:
        export_svg(source, source.with_suffix(".png"), (512, 512))


if __name__ == "__main__":
    main()
