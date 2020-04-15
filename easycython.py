from __future__ import print_function, division
import sys
import os
import logging
from os.path import splitext
import begin
from glob import glob


@begin.start
def main(*filenames):
    files = [f for g in filenames for f in glob(g)]
    extensions = []
    for f in files:
        basename, ext = splitext(f)
        extensions.append((basename, f))
    if len(extensions) == 0:
        sys.exit(1)
    missing = [f for n, f in extensions if not os.path.exists(f)]
    if missing:
        sys.exit(2)

    sys.argv = [sys.argv[0], 'build_ext', '--inplace']

    from setuptools import setup, Extension
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
    import Cython.Compiler.Options
    Cython.Compiler.Options.annotate = True
    ext_modules = []
    for n, f in extensions:
        module_name = os.path.basename(n)
        obj = Extension(module_name, [f],
                extra_compile_args=["-O2", "-march=native"])
        ext_modules.append(obj)
    include_dirs = []

    setup(
        cmdclass = {'build_ext': build_ext},
        include_dirs=include_dirs,
        ext_modules = cythonize(ext_modules),
        )
