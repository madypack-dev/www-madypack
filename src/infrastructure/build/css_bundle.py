"""Builder del bundle CSS de la aplicación.

Se ejecuta como módulo:

    python -m src.infrastructure.build.css_bundle
"""

from pathlib import Path

from src.infrastructure.logging.logger import configurar_logging, get_logger

configurar_logging()
logger = get_logger()


def compilar_bundle_css() -> None:
    """Une todos los archivos CSS de la aplicación en un único static/css/bundle.css.

    El objetivo es reducir las peticiones HTTP concurrentes al cargar la página.
    """
    infra_dir = Path(__file__).resolve().parent.parent
    root_dir = infra_dir.parents[1]
    static_dir = root_dir / "static"
    css_dir = static_dir / "css"

    css_files = [
        css_dir / "base" / "fonts.css",
        css_dir / "base" / "variables.css",
        css_dir / "base" / "reset.css",
        css_dir / "layout.css",
        css_dir / "components" / "buttons.css",
        css_dir / "components" / "social.css",
        css_dir / "components" / "header.css",
        css_dir / "components" / "footer.css",
        css_dir / "components" / "home.css",
        css_dir / "components" / "cart.css",
        css_dir / "components" / "tienda.css",
        css_dir / "components" / "cookie-banner.css",
        css_dir / "components" / "confirmation.css",
    ]

    bundle_content = []
    for file_path in css_files:
        if file_path.exists():
            rel_path = file_path.relative_to(static_dir)
            bundle_content.append(f"/* --- Start of {rel_path} --- */")
            bundle_content.append(file_path.read_text(encoding="utf-8"))
            bundle_content.append(f"/* --- End of {rel_path} --- */\n")
        else:
            logger.warning(f"Archivo CSS no encontrado para empaquetar: {file_path}")

    bundle_file = css_dir / "bundle.css"
    bundle_file.write_text("\n".join(bundle_content), encoding="utf-8")
    logger.info(f"CSS root bundle compilado con éxito en {bundle_file}")


if __name__ == "__main__":
    compilar_bundle_css()
