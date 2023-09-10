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
    variant("hip", default=False, description="Build with HIP support")
    variant("dpcpp", default=False, description="Build with DPC++ support")
    variant("openacc", default=False, description="Build with OpenACC support")
    variant("align", default=False, description="Adjust timers to include data movement to device")

    build_system("makefile", "cmake", default="makefile")

    conflicts("build_system=makefile", when="+kokkos")
    conflicts("build_system=makefile", when="+raja")
    
    # conflicts("+cuda +hip", msg="CUDA and HIP are mutually exclusive")

    depends_on("hip", when="+hip")

    depends_on("kokkos", when="+kokkos")
    
    depends_on("raja", when="+raja")
    depends_on("umpire", when="+raja")
    depends_on("chai", when="+raja")

    @property
    def build_targets(self):
        spec = self.spec
        compiler = ""
        cflags = "-O3"

        if "+hip" in spec and "+rocm" in spec:
            compiler = spec["hip"].prefix.bin.hipcc
            hip_arch = spec.variants["amdgpu_target"].value
            cflags += " " + " ".join(self.hip_flags(hip_arch))
        elif "+hip" in spec and "+cuda" in spec:
            compiler = spec["hip"].prefix.bin.hipcc
            cuda_arch = spec.variants["cuda_arch"].value
            cflags += " ".join(self.cuda_flags(cuda_arch))
        elif "+cuda" in spec:
            compiler = spec["cuda"].prefix.bin.nvcc
            cuda_arch = spec.variants["cuda_arch"].value
            cflags += " --x cu " + " ".join(self.cuda_flags(cuda_arch))
        else:
            compiler = "c++"

        if "+openmp_cpu" in spec or "+openmp" in spec:
            cflags += " " + self.compiler.openmp_flag

        if "+dpcpp" in spec:
            cflags += "-ffast-math -fsycl"

        if "+align" in spec:
            targets.append("ALIGN=yes")

        return {
            "CC={0}".format(compiler),
            "CFLAGS={0}".format(cflags),
            "all",
        }


    def build(self, spec, prefix):
        makefile_file = ""

        if "+openmp_cpu" in spec:
            makefile_file = "Makefile.openmp_cpu"

        if "+openmp_offload" in spec:
            makefile_file = "Makefile.openmp"

        if "+hip" in spec:
            makefile_file = "Makefile.hip"

        if "+cuda" in spec: 
            makefile_file = "Makefile.cuda"

        if "+dpcpp" in spec:
            makefile_file = "Makefile.dpcpp"

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

        if "+kokkos" in spec:
            model = "Kokkos"

        if "+raja" in spec:
            model = "RAJA"

            raja_spec = spec["raja"]
            if raja_spec.satisfies("+openmp"):
                args.append(self.define("ENABLE_OPENMP", "ON"))
            if raja_spec.satisfies("+cuda"):
                args.append(self.define("ENABLE_CUDA", "ON"))
            if raja_spec.satisfies("+hip"):
                args.append(self.define("ENABLE_HIP", "ON"))

        args.append(self.define("MODEL", model))

        return args
