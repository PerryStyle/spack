# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class Xsbench(MakefilePackage, CMakePackage, CudaPackage):
    """XSBench is a mini-app representing a key computational
    kernel of the Monte Carlo neutronics application OpenMC.
    A full explanation of the theory and purpose of XSBench
    is provided in docs/XSBench_Theory.pdf."""

    homepage = "https://github.com/ANL-CESAR/XSBench/"
    url = "https://github.com/ANL-CESAR/XSBench/archive/v13.tar.gz"
    git = "https://github.com/ANL-CESAR/XSBench.git"

    tags = ["proxy-app", "ecp-proxy-app"]

    version("master", branch="master")
    version("20", sha256="3430328267432b4c29605f248809caec3e8b0e3442d4dcd672fa09b8bb9aa1b6")
    version("19", sha256="57cc44ae3b0a50d33fab6dd48da13368720d2aa1b91cde47d51da78bf656b97e", deprecated=True)
    version("18", sha256="a9a544eeacd1be8d687080d2df4eeb701c04eda31d3806e7c3ea1ff36c26f4b0", deprecated=True)
    version("14", sha256="595afbcba8c1079067d5d17eedcb4ab0c1d115f83fd6f8c3de01d74b23015e2d", deprecated=True)
    version("13", sha256="b503ea468d3720a0369304924477b758b3d128c8074776233fa5d567b7ffcaa2", deprecated=True)

    build_system(
        conditional("cmake", when="+kokkos"), conditional("makefile", when="~kokkos"), default="makefile"
    )

    variant("mpi", default=False, description="Build with MPI support")
    variant("openmp-threading", default=False, description="Build with OpenMP Threading support")
    variant("openmp-offload", default=False, description="Build with OpenMP Offload support")
    variant("hip", default=False, description="Build with HIP support")
    variant("kokkos", default=False, description="Build with Kokkos support")
    variant("sycl", default=False, description="Build with SYCL support")
    variant("openacc", default=False, description="Build with OpenACC support")
    variant("align", default=False, description="Adjust timers to match across XSBench programming model variants")

    depends_on("mpi", when="+mpi")
    depends_on("hip", when="+hip")
    depends_on("kokkos+openmp", when="+kokkos")

    conflicts("cuda_arch=none", when="+cuda", msg="CUDA architecture is required")
    conflicts("cuda_arch=none", when="+openacc", msg="CUDA arch required with OpenACC")
    conflicts("cuda_arch=none", when="+openmp-offload", msg="CUDA arch required with OpenMP Offload")
    requires("%nvhpc", when="+openacc", msg="OpenACC only supported with NVHPC compiler")
    requires("%clang", when="+openmp-offload", msg="OpenMP Offload only supported with Clang compiler")

    @property
    def build_directory(self):
        spec = self.spec

        if "+openmp-threading" in spec:
            return "openmp-threading"

        if "+openmp-offload" in spec:
            return "openmp-offload"

        if "+hip" in spec:
            return "hip"

        if "+cuda" in spec:
            return "cuda"

        if "+kokkos" in spec:
            return "kokkos"

        if "+sycl" in spec:
            return "sycl"

        if "+openacc" in spec:
            return "openacc"

        if "+hip" in spec:
            return "hip"

        if "+cuda" in spec:
            return "cuda"

    @property
    def build_targets(self):
        spec = self.spec

        targets = []
        cflags = "-O3"
        ldflags = "-lm"

        if "+mpi" in spec:
            targets.append("CC=mpicc")
            targets.append("MPI=yes")
        else:
            if "+cuda" in spec and "+openacc" not in spec and "+openmp-offload" not in spec:
                targets.append("CC={0}".format(spec["cuda"].prefix.bin.nvcc))
                cuda_arch = spec.variants["cuda_arch"].value
                cflags += " " + " ".join(self.cuda_flags(cuda_arch))
            elif "+hip" in spec:
                targets.append("CC={0}".format(spec["hip"].prefix.bin.hipcc))
            elif "+sycl" in spec:
                targets.append("CC={0}".format(spack_cxx))
                cflags += " -fsycl" + " " + self.compiler.cxx17_flag
            elif "+openmp-offload" in spec:
                targets.append("CC={0}".format(spack_cc))
                cflags += " -fopenmp-targets=nvptx-nvidia-cuda -Xopenmp-target -march=sm_" + spec.variants["cuda_arch"].value[0]
            elif "+openacc" in spec:
                targets.append("CC={0}".format(spack_cc))
                cflags += " -acc -Minfo=accel -gpu=cc" + spec.variants["cuda_arch"].value[0]
            else:
                targets.append("CC={0}".format(spack_cc))

            targets.append("MPI=no")

        # Need to add for acc here because we use omp timers in the acc code
        if "+openmp-threading" in spec or "+openmp-offload" in spec or "+openacc" in spec:
            cflags += " " + self.compiler.openmp_flag

        if "+align" in spec:
            targets.append("ALIGNED=yes")
            cflags += " -DALIGNED_WORK"
        elif "~align" in spec:
            targets.append("ALIGNED=no")

        targets.append("CFLAGS={0}".format(cflags))
        targets.append("LDFLAGS={0}".format(ldflags))

        return targets

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        with working_dir(self.build_directory):
            install("XSBench", prefix.bin)

class CMakeBuilder(spack.build_systems.cmake.CMakeBuilder):
    @property
    def root_cmakelists_dir(self):
        spec = self.spec

        if "+kokkos" in spec:
            return "kokkos"

    def cmake_args(self):
        spec = self.spec
        args = [
            self.define("Kokkos_ROOT", spec["kokkos"].prefix)
        ]
        return args
