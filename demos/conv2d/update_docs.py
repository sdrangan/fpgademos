import argparse
import re
import shutil
from pathlib import Path

import pandas as pd


MARKER_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def csv_to_markdown(csv_path: Path) -> str:
    df = pd.read_csv(csv_path)
    if df.empty and len(df.columns) == 0:
        raise ValueError(f"CSV file is empty: {csv_path}")
    
    # Rename the first column to 'Module' if it's currently a placeholder/blank
    if df.columns[0].startswith("Unnamed") or df.columns[0] == "":
        df.columns.values[0] = "Module"
    return df.to_markdown(index=False) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Render Conv2D documentation assets.")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the rendered results.md into docs/projects/example_projects/conv2d.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    results_template = script_dir / "results.md.template"
    results = script_dir / "results.md"
    data_dir = script_dir / "data"
    csynth_resources = data_dir / "csynth_resources.csv"
    csynth_resources_md = data_dir / "csynth_resources.md"
    docs_results = (
        script_dir.parent.parent
        / "docs"
        / "projects"
        / "example_projects"
        / "conv2d"
        / "results.md"
    )

    template_text = results_template.read_text(encoding="utf-8")
    csynth_resources_md.write_text(csv_to_markdown(csynth_resources), encoding="utf-8")

    def replace_marker(match: re.Match[str]) -> str:
        rel_path = match.group(1).strip()
        include_path = data_dir / rel_path
        if not include_path.is_file():
            raise FileNotFoundError(
                f"Template marker '{{{{ {rel_path} }}}}' references missing file: {include_path}"
            )
        return include_path.read_text(encoding="utf-8")

    rendered = MARKER_RE.sub(replace_marker, template_text)
    results.write_text(rendered, encoding="utf-8")

    if args.copy:
        shutil.copyfile(results, docs_results)
        print(f"Copied {results} -> {docs_results}")

    print(f"Wrote {csynth_resources_md}")
    print(f"Wrote {results}")


if __name__ == "__main__":
    main()

