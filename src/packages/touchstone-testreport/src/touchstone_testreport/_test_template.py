from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


class TouchstoneTestTemplate:
    # Constants
    TEMPLATE_DIR_DEFAULT: Path = Path(__file__).parent / 'templates'
    OUTPUT_DIR_DEFAULT: Path = Path(__file__).parent / 'generated'

    def __init__(self, in_template_dir: Path = None, in_out_dir: Path = None):
        self._template_dir: Path = in_template_dir or self.TEMPLATE_DIR_DEFAULT
        self._out_dir: Path = in_out_dir or self.OUTPUT_DIR_DEFAULT
        self._env: Environment = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            # Removes trailing newlines after a template tag
            trim_blocks=True,
            # Strips tabs/spaces from the start of a line to a tag
            lstrip_blocks=True
        )

        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def template_dir(self) -> Path:
        return self._template_dir.resolve().absolute()

    @property
    def output_dir(self) -> Path:
        return self._out_dir.resolve().absolute()

    def to_html(self, in_template_name: str, in_out_filename: str, *args, **kwargs):
        file_path: Path = Path(self.output_dir) / in_out_filename
        template: Template = self._env.get_template(in_template_name)

        with file_path.open(mode='w', encoding='utf-8') as file:
            file.write(template.render(*args, **kwargs))
