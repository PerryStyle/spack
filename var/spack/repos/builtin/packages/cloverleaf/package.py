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

    depends_on("kokkos", when="+kokkos")

    depends_on("raja", when="+raja")
    depends_on("umpire", when="+raja")


    def cmake_args(self):
        spec = self.spec
        args = []

        if "+cuda" in spec:
            args.append(self.define("CMAKE_CUDA_COMPILER", spec["cuda"].prefix.bin.nvcc))
            args.append(self.define("CUDA_ARCH", "sm_{0}".format(spec.variants["cuda_arch"].value)))

        return args

