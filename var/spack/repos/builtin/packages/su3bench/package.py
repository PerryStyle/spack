# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install su
#
# You can edit this file again by typing:
#
#     spack edit su
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *


class Su3bench(MakefilePackage, CudaPackage):
    """Lattice QCD SU(3) Matrix-Matrix Multiply Microbenchmark"""

    homepage = "https://gitlab.com/NERSC/nersc-proxies/su3_bench"
    git = "https://gitlab.com/NERSC/nersc-proxies/su3_bench.git"

    version("master", branch="master")

    variant("openmp_cpu", default=False, description="Build with OpenMP CPU support")

    @property
    def build_targets(self):
        spec = self.spec
        compiler = ""
        cflags = "-O3"

        if "+cuda" in spec:
            compiler = spec["cuda"].prefix.bin.nvcc
        else:
            compiler = "c++"

        if "+openmp_cpu" in spec:
            cflags += " " + self.compiler.openmp_flag


        return {
            "CC={0}".format(compiler),
            "CFLAGS={0}".format(cflags),
        }


    def build(self, spec, prefix):
        make("-f", "Makefile.openmp_cpu")

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        # TODO Add Variant Name
        install("bench_f32_openmp.exe", prefix.bin)
