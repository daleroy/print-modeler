"""Read the YAML front matter of a job's spec.md. Shared by the job tools."""
from pathlib import Path


def read_spec(job_dir):
    p = Path(job_dir) / "spec.md"
    if not p.exists():
        return {}
    text = p.read_text()
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    try:
        import yaml
        data = yaml.safe_load(block) or {}
    except Exception:
        data = {}
        for line in block.splitlines():
            line = line.split("#", 1)[0].rstrip()
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip() or None
    return data


def resolve_output_dir(job_dir):
    """spec.md output_dir if set, else <job>/out."""
    out = read_spec(job_dir).get("output_dir")
    if out:
        return Path(str(out)).expanduser()
    return Path(job_dir) / "out"
