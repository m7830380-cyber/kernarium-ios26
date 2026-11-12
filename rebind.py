import sys, struct
# usage: rebind.py file OLD=NEW ...   (NEW must be <= OLD length, same dylib)
path = sys.argv[1]; m = dict(a.split('=') for a in sys.argv[2:])
d = bytearray(open(path, 'rb').read())
ncmds = struct.unpack_from('<I', d, 16)[0]; off = 32; n_ok = 0
for _ in range(ncmds):
    cmd, sz = struct.unpack_from('<II', d, off)
    if cmd == 0x80000034:
        h = struct.unpack_from('<I', d, off + 8)[0]
        ver, starts, imp, sym, cnt, fmt, symfmt = struct.unpack_from('<7I', d, h)
        for i in range(cnt):
            if fmt in (1, 2):
                p = h + imp + i * (4 if fmt == 1 else 8); v = struct.unpack_from('<I', d, p)[0]; no = v >> 9
            else:
                p = h + imp + i * 16; v = struct.unpack_from('<Q', d, p)[0]; no = v >> 32
            s = h + sym + no; e = d.index(0, s); name = d[s:e].decode()
            if name in m:
                new = m[name].encode(); assert len(new) <= e - s
                d[s:e] = new + b'\0' * (e - s - len(new)); n_ok += 1
                print('rebind', name, '->', m[name])
    off += sz
open(path, 'wb').write(d); print('rebound', n_ok)
