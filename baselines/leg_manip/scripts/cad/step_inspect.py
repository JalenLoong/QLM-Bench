"""Inspect the camera-bracket STEP assembly (SolidWorks AP214, mm).

Prints the product tree, per-part bounding boxes (edge vertices only) and the
assembly placements. Optional outputs:

    python scripts/cad/step_inspect.py <assembly.step>                  # summary
    python scripts/cad/step_inspect.py <assembly.step> verts.npz        # + vertices
    python scripts/cad/step_inspect.py <assembly.step> - faces origin.npy
        # planar faces of the bracket near the camera, normals in the Go2 base frame

Only numpy is needed. See src/leg_manip/assets/go2/CAMERA_MOUNT.md.
"""

import json
import re
import sys

import numpy as np

path = sys.argv[1]
REF = re.compile(r"#(\d+)")
NUM3 = re.compile(r"\(\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*,\s*([-0-9.Ee+]+)\s*\)")


def dec(s):
    return re.sub(
        r"\\X2\\([0-9A-Fa-f]+)\\X0\\",
        lambda m: bytes.fromhex(m.group(1)).decode("utf-16-be"),
        s,
    )


typ, refs, raw, pts = {}, {}, {}, {}
buf = ""
with open(path, encoding="utf-8", errors="replace") as f:
    for line in f:
        buf += line.strip()
        if not buf.endswith(";"):
            continue
        m = re.match(r"#(\d+)\s*=\s*\(?\s*([A-Z_0-9]+)(.*);$", buf)
        buf = ""
        if not m:
            continue
        i, t, rest = int(m.group(1)), m.group(2), m.group(3)
        typ[i] = t
        if t == "CARTESIAN_POINT" or t == "DIRECTION":
            n = NUM3.search(rest)
            if n:
                pts[i] = tuple(float(x) for x in n.groups())
            continue
        refs[i] = [int(x) for x in REF.findall(rest)]
        if t in (
            "PRODUCT",
            "PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE",
            "PRODUCT_DEFINITION",
            "PRODUCT_DEFINITION_SHAPE",
            "SHAPE_DEFINITION_REPRESENTATION",
            "SHAPE_REPRESENTATION",
            "SHAPE_REPRESENTATION_RELATIONSHIP",
            "NEXT_ASSEMBLY_USAGE_OCCURRENCE",
            "CONTEXT_DEPENDENT_SHAPE_REPRESENTATION",
            "REPRESENTATION_RELATIONSHIP",
            "ITEM_DEFINED_TRANSFORMATION",
            "AXIS2_PLACEMENT_3D",
            "ADVANCED_BREP_SHAPE_REPRESENTATION",
            "MANIFOLD_SURFACE_SHAPE_REPRESENTATION",
            "MANIFOLD_SOLID_BREP",
            "SHELL_BASED_SURFACE_MODEL",
        ):
            raw[i] = dec(rest)
print("entities", len(typ), "points", len(pts), file=sys.stderr)


def of_type(t):
    return [i for i, x in typ.items() if x == t]


# product -> product definition
prod_name = {i: raw[i].split("'")[1] for i in of_type("PRODUCT")}
pdf_of = {}
for i in of_type("PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE"):
    for r in refs[i]:
        if r in prod_name:
            pdf_of[i] = r
pd_prod = {}
for i in of_type("PRODUCT_DEFINITION"):
    for r in refs[i]:
        if r in pdf_of:
            pd_prod[i] = pdf_of[r]
pds_pd = {
    i: next(r for r in refs[i] if r in pd_prod)
    for i in of_type("PRODUCT_DEFINITION_SHAPE")
    if any(r in pd_prod for r in refs[i])
}
# product -> shape representation
prod_rep = {}
for i in of_type("SHAPE_DEFINITION_REPRESENTATION"):
    pds = refs[i][0]
    rep = refs[i][1]
    if pds in pds_pd:
        prod_rep[pd_prod[pds_pd[pds]]] = rep
# representation relationships: shape rep -> geometric reps
geo_of = {}
for i in of_type("SHAPE_REPRESENTATION_RELATIONSHIP"):
    a, b = refs[i][0], refs[i][1]
    for x, y in ((a, b), (b, a)):
        if typ.get(x) == "SHAPE_REPRESENTATION" and typ.get(y) in (
            "ADVANCED_BREP_SHAPE_REPRESENTATION",
            "MANIFOLD_SURFACE_SHAPE_REPRESENTATION",
        ):
            geo_of.setdefault(x, []).append(y)


def reach_points(roots):
    seen, stack, out = set(), list(roots), []
    while stack:
        e = stack.pop()
        if e in seen:
            continue
        seen.add(e)
        if typ.get(e) == "CARTESIAN_POINT":
            continue
        if typ.get(e) in ("VERTEX_POINT", "POLY_LOOP", "POLYLINE"):
            out.extend(pts[r] for r in refs[e] if typ.get(r) == "CARTESIAN_POINT")
        if typ.get(e) in (
            "SHAPE_REPRESENTATION",
            "GEOMETRIC_REPRESENTATION_CONTEXT",
            "PRODUCT_DEFINITION_SHAPE",
        ):
            continue
        stack.extend(
            r
            for r in refs.get(e, [])
            if typ.get(r) not in ("GEOMETRIC_REPRESENTATION_CONTEXT",)
        )
    return np.array(out) if out else np.zeros((0, 3))


def axis(i):
    r = refs[i]
    o = np.array(pts[r[0]])
    z = np.array(pts[r[1]])
    x = np.array(pts[r[2]])
    z = z / np.linalg.norm(z)
    x = x - z * (x @ z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4)
    T[:3, :3] = np.stack([x, y, z], 1)
    T[:3, 3] = o
    return T


result = {}
for p, name in prod_name.items():
    rep = prod_rep.get(p)
    geos = geo_of.get(rep, [])
    P = reach_points([g for g in geos])
    solids = [
        raw[s].split("'")[1]
        for g in geos
        for s in refs[g]
        if typ.get(s) in ("MANIFOLD_SOLID_BREP", "SHELL_BASED_SURFACE_MODEL")
    ]
    result[p] = {
        "name": name,
        "rep": rep,
        "geo_types": [typ[g] for g in geos],
        "n_points": len(P),
        "bbox_min_mm": P.min(0).round(1).tolist() if len(P) else None,
        "bbox_max_mm": P.max(0).round(1).tolist() if len(P) else None,
        "solids": solids,
    }
# assembly placements
for i in of_type("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
    parent_pd, child_pd = refs[i][0], refs[i][1]
    print(
        "NAUO",
        raw[i].split("'")[1],
        ":",
        prod_name[pd_prod[parent_pd]],
        "->",
        prod_name[pd_prod[child_pd]],
    )
for i in of_type("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION"):
    rr, pds = refs[i][0], refs[i][1]
    nauo = (
        refs[pds][0]
        if typ.get(refs[pds][0]) == "NEXT_ASSEMBLY_USAGE_OCCURRENCE"
        else None
    )
    # rr: complex REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION (rep1, rep2, idt).
    idt = next(r for r in refs[rr] if typ.get(r) == "ITEM_DEFINED_TRANSFORMATION")
    a1, a2 = refs[idt][0], refs[idt][1]
    reps = [r for r in refs[rr] if typ.get(r) == "SHAPE_REPRESENTATION"]
    parent = next((p for p, r in prod_rep.items() if r == reps[0]), None)
    child = next((p for p, r in prod_rep.items() if r == reps[1]), None)
    T1, T2 = axis(a1), axis(a2)
    # rep_1 = parent (assembly), rep_2 = child: child frame -> parent frame.
    Tchild_in_parent = T1 @ np.linalg.inv(T2)
    result.setdefault("T", {})[prod_name.get(child)] = Tchild_in_parent
    result.setdefault("placements", []).append(
        {
            "child": prod_name.get(child),
            "parent": prod_name.get(parent),
            "R": Tchild_in_parent[:3, :3].round(4).tolist(),
            "t_mm": Tchild_in_parent[:3, 3].round(2).tolist(),
        }
    )
Ts = result.pop("T")
for p, r in list(result.items()):
    if p == "placements":
        continue
    T = Ts.get(r["name"])
    if T is not None and r["n_points"]:
        P = reach_points(geo_of.get(r["rep"], []))
        Q = P @ T[:3, :3].T + T[:3, 3]
        r["bbox_in_root_min_mm"] = Q.min(0).round(1).tolist()
        r["bbox_in_root_max_mm"] = Q.max(0).round(1).tolist()
print(json.dumps(result, ensure_ascii=False, indent=None))

# --- orientation probe: dump root-frame vertices of the go2 and the bracket ---
if len(sys.argv) > 2 and sys.argv[2] != "-":
    out = {}
    for p, r in result.items():
        if p == "placements" or not r["n_points"]:
            continue
        T = Ts.get(r["name"])
        P = reach_points(geo_of.get(r["rep"], []))
        out[r["name"]] = (P @ T[:3, :3].T + T[:3, 3]) if T is not None else P
    np.savez(sys.argv[2], **{k: v for k, v in out.items()})

# --- planar faces of the single bracket, with normals and vertex extents ---
if len(sys.argv) > 3 and sys.argv[3] == "faces":
    org = np.load(sys.argv[4])
    Rb = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)
    bp = next(
        p for p, r in result.items() if p != "placements" and r["name"] == "单支架"
    )
    T = Ts["单支架"]
    faces = []
    seen = set()
    stack = list(geo_of.get(result[bp]["rep"], []))
    while stack:
        e = stack.pop()
        if e in seen:
            continue
        seen.add(e)
        if typ.get(e) == "ADVANCED_FACE":
            faces.append(e)
            continue
        stack.extend(refs.get(e, []))
    rows = []
    for f in faces:
        surf = [r for r in refs[f] if typ.get(r) == "PLANE"]
        if not surf:
            continue
        ax = refs[surf[0]][0]
        n_cad = np.array(pts[refs[ax][1]])
        P = reach_points([f]) / 1000.0
        if len(P) < 3:
            continue
        P = P @ T[:3, :3].T + T[:3, 3] / 1000.0
        Q = (P - org) @ Rb
        n = Rb.T @ (T[:3, :3] @ n_cad)
        ext = Q.max(0) - Q.min(0)
        area_proxy = np.sort(ext)[1] * np.sort(ext)[2]
        rows.append((area_proxy, Q.mean(0), n, ext))
    rows.sort(key=lambda r: -r[0])
    for _, c, n, ext in rows:
        if c[0] > 0.25:
            print(
                f"face centre {np.round(c, 3)} normal {np.round(n, 3)} "
                f"extent {np.round(ext, 3)}"
            )
