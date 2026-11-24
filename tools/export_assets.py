"""Exporta as artes SVG de Turnos Zero para PNGs compatíveis com Tkinter."""
from pathlib import Path
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "ambientes"
NAMES = (
    "agencia_menu",
    "cidade_noturna",
    "loja_24_horas",
    "edificio_residencial",
    "cinema_ultima_sessao",
    "laboratorio_experimental",
)

def main():
    for name in NAMES:
        source = ASSET_DIR / f"{name}.svg"
        target = ASSET_DIR / f"{name}.png"
        if not source.is_file():
            raise SystemExit(f"Arte SVG ausente: {source}")
        cairosvg.svg2png(
            url=str(source),
            write_to=str(target),
            output_width=834,
            output_height=315,
        )
        print(f"Exportado: {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
