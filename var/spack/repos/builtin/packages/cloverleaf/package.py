# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------

from spack.package import *


class Cloverleaf(CMakePackage, CudaPackage, ROCmPackage):
    """FIXME: Put a proper description of your package here."""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://www.example.com"
    url = "cloverleaf"
    git = "https://github.com/UoB-HPC/CloverLeaf.git"

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    # maintainers("github_user1", "github_user2")

    version("main", branch="main")

    variant("kokkos", default=False, description="Enable Kokkos support")
    variant("omp", default=False, description="Enable OpenMP support")
    variant("omp-target", default=False, description="Enable OpenMP target offload support")
    variant("raja", default=False, description="Enable RAJA support")
    variant("sycl-acc", default=False, description="Enable sycl-acc support")
    variant("sycl-usm", default=False, description="Enable sycl-usm support")
    variant("managed-alloc", default=False, description="Enable unified memory")
    variant("sync-all-kernels", default=False, description="Enabling synchronizing of kernels")

    variant("sycl-compiler",
            default="none",
            values=("ONEAPI-ICPX", "ONEAPI-Clang", "DPCPP",
                    "HIPSYCL", "COMPUTECPP"),
            description="Compile using the specified SYCL compiler implementation"
            )

    depends_on("kokkos", when="+kokkos")

    depends_on("raja", when="+raja")
    depends_on("umpire", when="+raja")

    conflicts("sycl-compiler=none", when="+sycl-acc")
    conflicts("sycl-compiler=none", when="+sycl-usm")


    def cmake_args(self):
        spec = self.spec
        model = ""
        args = []

        if "+cuda" in spec:
            model = "cuda"
            args.append(self.define("CMAKE_CUDA_COMPILER", spec["cuda"].prefix.bin.nvcc))
            args.append(self.define("CUDA_ARCH", "sm_{0}".format(spec.variants["cuda_arch"].value)))

        if "+kokkos" in spec:
            model = "kokkos"
            args.append(self.define("KOKKOS_IN_PACKAGE", spec["kokkos"].prefix))

        if "+omp" in spec:
            model = "omp"

        if "+omp-target" in spec:
            model = "omp-target"

        if "+raja" in spec:
            model = "raja"

        if "+sycl-acc" or "+sycl-usm":
            if "+sycl-acc" in spec:
                model = "sycl-acc"

            if "+sycl-usm" in spec:
                model = "sycl-usm"

            args.append(self.define_from_variant("SYCL_COMPILER", "sycl-compiler"))

        args.append(self.define("MODEL", model))

        return args

