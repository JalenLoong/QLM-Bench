"""Compatibility import: all producers share the frozen Canonical converter."""
from qlm_bench.compatibility.dataset_v2.conversion import convert, main

__all__=["convert"]

if __name__=="__main__":main()
