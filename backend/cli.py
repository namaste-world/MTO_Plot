import argparse, pathlib
from . import load_data, semantic, sharedref, lineage, density

def main():
    p = argparse.ArgumentParser(description="Build graph JSON files")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(x):
        x.add_argument("--json_dir", default="data")
        x.add_argument("--out_dir",  default="public")

    for name in ("semantic","citation","sharedref","lineage","density","institution","all"):
        common(sub.add_parser(name))

    # semantic params
    for name in ("semantic","all"):
        sg=sub.choices[name]
        sg.add_argument("--top_k", type=int, default=5)
        sg.add_argument("--sim_threshold", type=float, default=.60)

    args = p.parse_args()
    papers = load_data.load(pathlib.Path(args.json_dir))
    out    = pathlib.Path(args.out_dir); out.mkdir(exist_ok=True)

    if args.cmd in ("semantic","all"):
        semantic.build(papers, out, args.top_k, args.sim_threshold)
    if args.cmd in ("sharedref","all"):
        sharedref.build(papers, out)
    if args.cmd in ("lineage","all"):
        lineage.build(papers, out)
    if args.cmd in ("density","all"):
        density.build(papers, out)

if __name__ == "__main__":
    main()
