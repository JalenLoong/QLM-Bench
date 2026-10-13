"""Legacy import name; all tasks use the shared frozen-format converter."""
from .conversion import convert, main

__all__=["convert"]

if __name__=="__main__":main()
