import os
import sys

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--self-test":
        from wardogs_mortar.selftest import run
        run(sys.argv[2], sys.argv[3])
    else:
        from wardogs_mortar.app import main
        main()
