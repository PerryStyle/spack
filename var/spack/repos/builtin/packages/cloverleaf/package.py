# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------

from spack.package import *

import os

class Cloverleaf(CMakePackage, CudaPackage, ROCmPackage):
    """FIXME: Put a proper description of your package here."""

    homepage = "https://www.example.com"
    url = "cloverleaf"
    git = "https://github.com/UoB-HPC/CloverLeaf.git"

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    # maintainers("github_user1", "github_user2")

    version("main", branch="main")

    variant("kokkos", default=False, description="Enable Kokkos support")
    variant("omp", default=False, description="Enable OpenMP support")
    variant("hip", default=False, description="Enabel HIP support")
    variant("omp-target", default=False, description="Enable OpenMP target offload support")
    variant("raja", default=False, description="Enable RAJA support")
    variant("sycl-acc", default=False, description="Enable sycl-acc support")
    variant("sycl-usm", default=False, description="Enable sycl-usm support")
    variant("managed-alloc", default=False, description="Enable unified memory")
    variant("sync-all-kernels", default=False, description="Enabling synchronizing of kernels")

    variant("sycl-compiler",
            default="None",
            values=("ONEAPI-ICPX", "ONEAPI-Clang", "DPCPP",
                    "HIPSYCL", "COMPUTECPP", "None"),
            description="Compile using the specified SYCL compiler implementation"
            )

    variant("extra-flags",
            values=str,
            default="none"
            )

    with when("+hip"):
        depends_on("hip +cuda -rocm", when="+cuda")
        depends_on("hip +rocm", when="+rocm")
    
    depends_on("kokkos", when="+kokkos")

    depends_on("raja", when="+raja")
    depends_on("umpire", when="+raja")

    conflicts("sycl-compiler=None", when="+sycl-acc")
    conflicts("sycl-compiler=None", when="+sycl-usm")


    def cmake_args(self):
        spec = self.spec
        model = ""
        args = []

        if "+sycl-acc" in spec or "+sycl-usm" in spec:
            if "+sycl-acc" in spec:
                model = "sycl-acc"

            if "+sycl-usm" in spec:
                model = "sycl-usm"

            if "sycl-compiler=DPCPP":
                cxx_bin = os.path.dirname(self.compiler.cxx)
                cxx_prefix = join_path(cxx_bin, '..')
                args.append(self.define("SYCL_COMPILER_DIR", cxx_prefix))

            if "cuda_arch" in spec.variants:
                cuda_arch = spec.variants["cuda_arch"].value[0]
                args.append(self.define("CXX_EXTRA_FLAGS", "-fsycl-targets=nvidia_gpu_sm_{0}".format(cuda_arch)))

            if "amdgpu_target" in spec.variants:
                hip_arch = spec.variants["amdgpu_target"].value
                args.append(self.define("CXX_EXTRA_FLAGS", "-fsycl-targets=amd_gpu_{0}".format(hip_arch)))

            args.append(self.define_from_variant("SYCL_COMPILER", "sycl-compiler"))
        elif "+hip" in spec:
            model = "hip"
            args.append(self.define("CMAKE_CXX_COMPILER", spec["hip"].prefix.bin.hipcc))

            if "amdgpu_target" in spec.variants:
                hip_arch = spec.variants["amdgpu_target"].value
                args.append(self.define("CXX_EXTRA_FLAGS", self.hip_flags(hip_arch)))

            if "cuda_arch" in spec.variants:
                cuda_arch = spec.variants["cuda_arch"].value
                args.append(self.define("CXX_EXTRA_FLAGS", " ".join(self.cuda_flags(cuda_arch))))
        elif "+cuda" in spec:
            model = "cuda"
            args.append(self.define("CMAKE_CUDA_COMPILER", spec["cuda"].prefix.bin.nvcc))
            args.append(self.define("CUDA_ARCH", "sm_{0}".format(spec.variants["cuda_arch"].value[0])))
        elif "+kokkos" in spec:
            kokkos_spec = spec["kokkos"]
            model = "kokkos"
            args.append(self.define("KOKKOS_IN_PACKAGE", kokkos_spec.prefix))

            if spec["kokkos"].satisfies("+rocm"):
                args.append(self.define("CMAKE_CXX_COMPILER", kokkos_spec["hip"].prefix.bin.hipcc))
        elif "+omp" in spec:
            model = "omp"
        elif "+omp-target" in spec:
            model = "omp-target"

        if "+raja" in spec:
            model = "raja"

        if spec.variants["extra-flags"].value != "none":
            args.append(self.define("CXX_EXTRA_FLAGS", spec["extra-flags"].value))

        args.append(self.define("MODEL", model))

        return args

