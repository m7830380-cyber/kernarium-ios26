import sys, struct
path, names = sys.argv[1], set(sys.argv[2:])
d = bytearray(open(path, 'rb').read())
assert struct.unpack_from('<I', d, 0)[0] == 0xfeedfacf, 'thin arm64 only'
ncmds = struct.unpack_from('<I', d, 16)[0]
off = 32; done = 0
for _ in range(ncmds):
    cmd, sz = struct.unpack_from('<II', d, off)
    if cmd == 0x80000034:  # LC_DYLD_CHAINED_FIXUPS
        doff, dsz = struct.unpack_from('<II', d, off + 8)
        h = doff
        ver, starts, imp, sym, cnt, fmt, symfmt = struct.unpack_from('<7I', d, h)
        assert symfmt == 0
        for i in range(cnt):
            if fmt in (1, 2):
                p = h + imp + i * (4 if fmt == 1 else 8)
                v = struct.unpack_from('<I', d, p)[0]
                no = v >> 9; bit = 1 << 8
            else:
                p = h + imp + i * 16
                v = struct.unpack_from('<Q', d, p)[0]
                no = v >> 32; bit = 1 << 16
            s = h + sym + no; e = d.index(0, s); n = d[s:e].decode()
            if n in names:
                v |= bit
                struct.pack_into('<I' if fmt in (1, 2) else '<Q', d, p, v)
                print('weak:', n); done += 1
    off += sz
open(path, 'wb').write(d)
print('patched', done, 'of', len(names))
