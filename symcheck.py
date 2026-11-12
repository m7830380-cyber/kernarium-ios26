import sys, os, re, subprocess
sdk, lst = sys.argv[1], sys.argv[2]
syms = set()
for root, _, fs in os.walk(sdk):
    for f in fs:
        if not f.endswith('.tbd'): continue
        t = open(os.path.join(root, f), errors='ignore').read()
        for key, body in re.findall(r"(symbols|weak-symbols|thread-local-symbols|objc-classes|objc-eh-types|objc-ivars):\s*\[([^\]]*)\]", t):
            for s in re.split(r"[,\s]+", body):
                s = s.strip().strip("'\"")
                if not s: continue
                if key == 'objc-classes':
                    syms.add('_OBJC_CLASS_$_' + s); syms.add('_OBJC_METACLASS_$_' + s)
                elif key == 'objc-eh-types': syms.add('_OBJC_EHTYPE_$_' + s)
                elif key == 'objc-ivars': syms.add('_OBJC_IVAR_$_' + s)
                else: syms.add(s)
print("tbd symbols:", len(syms))
for f in open(lst).read().split('\n'):
    if not f: continue
    out = subprocess.run(['nm', '-m', '-u', f], capture_output=True, text=True).stdout
    miss = []
    for l in out.splitlines():
        m = re.match(r"\s*\(undefined\)\s*(weak )?external (\S+) \(from (\S+)\)", l)
        if not m: continue
        weak, s, lib = m.groups()
        if lib in ('executable', 'flat-namespace') or '/' in lib: pass
        if s not in syms and not weak:
            # only system libs matter
            miss.append(f"{s} ({lib})")
    libs = subprocess.run(['otool', '-L', f], capture_output=True, text=True).stdout
    print("##", f, "MISSING strong:", len(miss))
    for x in miss[:200]: print("   ", x)
