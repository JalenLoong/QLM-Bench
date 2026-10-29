"""Portable runtime compatibility for the selected CPU rollout implementation."""
import ast
from functools import lru_cache
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def semantic_file(path):
    path=Path(path);st=path.stat()
    return _semantic_file(str(path.resolve()),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


@lru_cache(maxsize=512)
def _semantic_file(name,*stamp):
    path=Path(name)
    if path.suffix == '.json':
        return digest(json.loads(path.read_text()))
    tree = ast.parse(path.read_text())
    def value(node):
        if isinstance(node, ast.AST):
            fields = {}
            for key, item in ast.iter_fields(node):
                # Python 3.12 adds empty type_params to otherwise identical 3.10 ASTs.
                if key == 'type_params' and not item:
                    continue
                if key == 'body' and isinstance(item, list) and item and isinstance(item[0], ast.Expr) and isinstance(item[0].value, ast.Constant) and isinstance(item[0].value.value, str):
                    item = item[1:]
                fields[key] = value(item)
            return [type(node).__name__, fields]
        if isinstance(node, list):
            return [value(x) for x in node]
        if isinstance(node, bytes):
            return ['bytes', node.hex()]
        if isinstance(node, complex):
            return ['complex', repr(node)]
        if node is Ellipsis:
            return ['Ellipsis']
        return node
    return digest(value(tree))


def fingerprint(root, specification):
    return {'schema': specification['schema'], 'version': specification['version'],
            'sha256': digest({name: semantic_file(Path(root) / name) for name in specification['files']})}


def runtime_contract():
    root = Path(__file__).parents[2]
    spec = json.loads(Path(__file__).with_suffix('.json').read_text())
    return fingerprint(root, spec)
