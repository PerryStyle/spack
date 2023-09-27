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
    variant("dpcpp", default=False, description="Build with DPC++ support")
    variant("openacc", default=False, description="Build with OpenACC support")
    variant("hip", default=False, description="Build with HIP support")
    variant("align", default=False, description="Adjust timers to include data movement to device")
    variant("dir", values=str, default="none", description="Enable Directory support")
    variant(
        "pkg", default=False,
        description="Use spack package support instead of directory where possible"
    )

    conflicts(
        "dir=none",
        when="+kokkos~pkg",
        msg="Kokkos variant requires either in-tree path to kokkos or use of package"
    )
    for arch in CudaPackage.cuda_arch_values:
        depends_on(
            "kokkos+cuda+cuda_lambda cuda_arch=%s" % arch, when="+kokkos+pkg+cuda cuda_arch=%s" % arch
        )
    for arch in ROCmPackage.amdgpu_targets:
        depends_on(
            "kokkos+rocm amdgpu_target=%s" % arch, when="+kokkos+pkg+rocm amdgpu_target=%s" % arch
        )


    build_system("makefile", "cmake", default="makefile")

    conflicts("build_system=makefile", when="+kokkos")
    conflicts("build_system=makefile", when="+raja")
    
    # conflicts("+cuda +hip", msg="CUDA and HIP are mutually exclusive")

    depends_on("kokkos", when="+kokkos")
    backends = {
        "kokkos": [
            ("cuda", "cuda", "enable CUDA backend"),
            ("omp", "none", "enable OMP backend"),
            ("amd", "hip", "enable ROCm backend"),
        ],
    }
    backend_vals = ["none"]
    for lang in backends:
        for item in backends[lang]:
            backend, dpdncy, descr = item
            backend_vals.append(backend.lower())

    variant("backend", values=backend_vals, default="none", description="Enable backend support")

    for lang in backends:
        for item in backends[lang]:
            backend, dpdncy, descr = item
            if dpdncy.lower() != "none":
                depends_on("%s" % dpdncy.lower(), when="+%s backend=%s" % (lang, backend.lower()))

    
    depends_on("raja", when="+raja")
    depends_on("umpire", when="+raja")
    depends_on("chai", when="+raja")
    depends_on("rocthrust", when="+hip")

    @property
    def build_targets(self):
        try:
            spec = self.spec
            compiler = ""
            cflags = "-O3"
            align = "no"

            if "+openmp_offload" in spec:
                compiler = self.compiler.cxx
                cflags += " " + self.compiler.openmp_flag
                cflags += " -fopenmp-targets=amdgcn-amd-amdhsa -Xopenmp-target=amdgcn-amd-amdhsa"
                cflags += " -march=" + spec.variants["amdgpu_target"].value[0]
            elif "+hip" in spec:
                compiler = spec["hip"].prefix.bin.hipcc
                hip_arch = spec.variants["amdgpu_target"].value
                cflags += " " + self.hip_flags(hip_arch)
                cflags += " -I " + spec["hip"].prefix + "/include"
                cflags += " -I " + spec["rocthrust"].prefix + "/include"
            elif "+cuda" in spec:
                compiler = spec["cuda"].prefix.bin.nvcc
                cuda_arch = spec.variants["cuda_arch"].value
                cflags += " --x cu " + " ".join(self.cuda_flags(cuda_arch))
            else:
                compiler = "c++"

            if "+openmp_cpu" in spec:
                cflags += " " + self.compiler.openmp_flag

            if "+dpcpp" in spec:
                cflags += " -fsycl"

            if "+align" in spec:
                cflags += " -DALIGNED_WORK"

            return {
                "CC={0}".format(compiler),
                "CFLAGS={0}".format(cflags),
                "all",
            }
        except AttributeError as e:
            raise Exception(f"Error in property method build_targets: {e}")

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

        if "+align" in spec:
            args.append(self.define("ALIGN", "ON"))

        if "+kokkos" in spec:
            model = "Kokkos"
            kokkos_spec = spec["kokkos"]
            if "+pkg" in self.spec and "dir=none" in self.spec:
                if "backend=amd" in self.spec:
                    args.append("-DCMAKE_CXX_COMPILER=" + kokkos_spec["hip"].prefix.bin.hipcc)
                else:
                    args.append("-DCMAKE_CXX_COMPILER=" + self.compiler.cxx)
            else:
                if "+hip" in kokkos_spec:
                    args.append(self.define("CMAKE_CXX_COMPILER", kokkos_spec["hip"].prefix.bin.hipcc))

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
