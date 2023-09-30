# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *
import os
import glob

class Su3bench(MakefilePackage, CMakePackage, CudaPackage, ROCmPackage):
    """Lattice QCD SU(3) Matrix-Matrix Multiply Microbenchmark"""

    homepage = "https://gitlab.com/NERSC/nersc-proxies/su3_bench"
    git = "https://gitlab.com/NERSC/nersc-proxies/su3_bench.git"

    version("master", branch="master")

    variant("openmp_cpu", default=False, description="Build with OpenMP CPU support")
    variant("openmp_offload", default=False, description="Build with OpenMP Offload support")
    variant("kokkos", default=False, description="Build with Kokkos support")
    variant("raja", default=False, description="Build with RAJA support")
    variant("dpcpp", default=False, description="Build with Intel DPC++ support")
    variant("sycl", default=False, description="Build with SYCL support")
    variant("openacc", default=False, description="Build with OpenACC support")
    variant("align", default=False, description="Adjust timers to include data movement to device")
    variant("milc_complex", default=False, description="Use MILC complex numbers")

    build_system("makefile", "cmake", default="makefile")

    conflicts("build_system=makefile", when="+kokkos")
    conflicts("build_system=makefile", when="+raja")

    depends_on("kokkos", when="+kokkos")
    
    with when("+raja"):
        depends_on("raja")
        depends_on("blt")
        depends_on("umpire")
        depends_on("chai")

    @property
    def build_targets(self):
        spec = self.spec
        compiler = ""
        cflags = "-O3"
        libs = ""
        align = "no"
        args = []

        if "+rocm" in spec:
            compiler = spec["hip"].prefix.bin.hipcc
            hip_arch = spec.variants["amdgpu_target"].value
            cflags += " " + self.hip_flags(hip_arch)
        elif "+cuda" in spec:
            compiler = spec["cuda"].prefix.bin.nvcc
            cuda_arch = spec.variants["cuda_arch"].value
            cflags += " --x cu " + " ".join(self.cuda_flags(cuda_arch))
        else:
            compiler = "c++"

        if "+openmp_cpu" in spec or "+openmp_offload" in spec:
            cflags += " " + self.compiler.openmp_flag

        if "+dpcpp" in spec:
            cflags += " -fsycl"

        if "+sycl" in spec:
            cflags += " -fsycl"

        if "+align" in spec:
            align = "yes"

        if "+milc_complex" in spec:
            cflags += " -DMILC_COMPLEX"

        return {
            "CC={0}".format(compiler),
            "CFLAGS={0}".format(cflags),
            "ALIGNED={0}".format(align),
            "LIBS={0}".format(libs),
            "all",
        }


    def build(self, spec, prefix):
        makefile_file = ""

        if "+openmp_cpu" in spec:
            makefile_file = "Makefile.openmp_cpu"

        if "+openmp_offload" in spec:
            makefile_file = "Makefile.openmp"

        if "+rocm" in spec:
            makefile_file = "Makefile.hip"

        if "+cuda" in spec: 
            makefile_file = "Makefile.cuda"

        if "+dpcpp" in spec:
            makefile_file = "Makefile.dpcpp"

        if "+sycl" in spec:
            makefile_file = "Makefile.sycl"

        if "+openacc" in spec:
            makefile_file = "Makefile.openacc"

        make("-f", makefile_file, *self.build_targets)

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        executables = glob.glob("*.exe")
        for exe in executables:
            new_name = exe[:9]
            os.rename(exe, new_name)
            install(new_name, prefix.bin)

class CMakeBuilder(spack.build_systems.cmake.CMakeBuilder):
    install_targets = ["install"]

    def cmake_args(self):
        spec = self.spec
        args = []
        model = ""

        if "+align" in spec:
            args.append(self.define("ALIGN", "ON"))

        if "+kokkos" in spec:
            model = "Kokkos"
            kokkos_spec = spec["kokkos"]

            if "+rocm" in kokkos_spec:
                args.append(self.define("CMAKE_CXX_COMPILER", kokkos_spec["hip"].prefix.bin.hipcc))

        if "+raja" in spec:
            model = "RAJA"
            args.append(self.define("BLT_DIR", spec["blt"].prefix))

            raja_spec = spec["raja"]
            if "+cuda" in raja_spec:
                args.append(self.define("TARGET", "CUDA"))

            if "+rocm" in raja_spec:
                args.append(self.define("TARGET", "HIP"))

        args.append(self.define("MODEL", model))

        return args
