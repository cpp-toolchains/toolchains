import argparse
import platform
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--build_dir", type=str, required=True)
parser.add_argument("--llvm_dir", type=str, default="llvm/llvm")

args = parser.parse_args()

llvm_tools = [
    "dsymutil",
    "llvm-ar",
    "llvm-cxxfilt",
    "llvm-cov",
    "llvm-dwarfdump",
    "llvm-nm",
    "llvm-objdump",
    "llvm-objcopy",
    "llvm-profdata",
    "llvm-ranlib",
    "llvm-readobj",
    "llvm-strip",
    "llvm-size",
    "llvm-symbolizer"
]

runtime_targets = []
targets_to_build = []

if platform.system() == "Linux":
    runtime_targets = [
        "x86_64-unknown-linux-gnu",
        "aarch64-unknown-linux-gnu",
        "riscv64-unknown-linux-gnu",
        "armv7-unknown-linux-gnueabihf",
    ]
    targets_to_build = [
        "X86",
        "AArch64",
        "ARM",
        "NVPTX",
        "AMDGPU",
        "RISCV",
        "WebAssembly",
        "BPF",
    ]
elif platform.system() == "Darwin":
    if platform.processor() == "arm":
        runtime_targets = ["aarch64-apple-darwin"]
    else:
        runtime_targets = ["x86_64-apple-darwind"]
    targets_to_build = ["X86", "AArch64", "WebAssembly"]

cmake_args = [
    "cmake",
    "-GNinja",
    "-B",
    args.build_dir,
    "-S",
    args.llvm_dir,
    "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_INSTALL_PREFIX=/usr/local",
    "-DLLVM_TARGETS_TO_BUILD={}".format(';'.join(targets_to_build)),
    "-DLLVM_RUNTIME_TARGETS={}".format(';'.join(runtime_targets)),
    "-DLLVM_ENABLE_PER_TARGET_RUNTIME_DIR=ON",
    "-DLLVM_ENABLE_TERMINFO=OFF",
    "-DLLVM_ENABLE_ZLIB=OFF",
    "-DLLVM_ENABLE_ZSTD=OFF",
    "-DCLANG_DEFAULT_CXX_STDLIB=libc++",
    "-DCLANG_DEFAULT_RTLIB=compiler-rt",
    "-DCLANG_DEFAULT_UNWINDLIB=libunwind",
    "-DCLANG_DEFAULT_LINKER=lld",
    "-DLLVM_ENABLE_RUNTIMES=libunwind;compiler-rt;libcxx;libcxxabi;openmp",
    "-DLLVM_ENABLE_PROJECTS=bolt;clang;clang-tools-extra;lld;pstl",
    "-DLLVM_STATIC_LINK_CXX_STDLIB=ON",
    "-DLLVM_INSTALL_TOOLCHAIN_ONLY=ON",
    "-DLLVM_TOOLCHAIN_TOOLS={}".format(';'.join(llvm_tools)),
    "-DLLVM_DISTRIBUTIONS=ClangTools;BoltTool;LldTool;StdLib;Toolchain",
    "-DLLVM_ClangTools_DISTRIBUTION_COMPONENTS=clang-tidy;clang-doc;clang-format;clangd",
    "-DLLVM_BoltTool_DISTRIBUTION_COMPONENTS=bolt",
    "-DLLVM_LldTool_DISTRIBUTION_COMPONENTS=lld",
    "-DLLVM_StdLib_DISTRIBUTION_COMPONENTS=runtimes",
    "-DLLVM_Toolchain_DISTRIBUTION_COMPONENTS=clang;clang-format;clang-tidy;clang-doc;clangd;clang-resource-headers;bolt;runtimes;lld;{}".format(';'.join(llvm_tools)),
]

if platform.system() == "Darwin":
    cmake_args.extend([
        "-DRUNTIMES_BUILD_ALLOW_DARWIN=ON",
        "-DLLVM_BUILD_EXTERNAL_COMPILER_RT=ON",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=13",
        "-DCMAKE_C_COMPILER=/opt/homebrew/opt/llvm/bin/clang",
        "-DCMAKE_C_COMPILER=/opt/homebrew/opt/llvm/bin/clang++",
    ])

for rt in runtime_targets:
    cmake_args.extend([
        f"-DRUNTIMES_{rt}_OPENMP_LIBDIR_SUFFIX={rt}",
        f"-DRUNTIMES_{rt}_OPENMP_STANDALONE_BUILD=ON",
        f"-DRUNTIMES_{rt}_OPENMP_LLVM_TOOLS_DIR={args.build_dir}/bin",
        f"-DRUNTIMES_{rt}_LIBCXX_HERMETIC_STATIC_LIBRARY=ON",
        f"-DRUNTIMES_{rt}_LIBCXXABI_USE_LLVM_UNWINDER=ON",
        f"-DRUNTIMES_{rt}_LIBCXX_STATICALLY_LINK_ABI_IN_STATIC_LIBRARY=ON",
        f"-DRUNTIMES_{rt}_LIBCXXABI_STATICALLY_LINK_UNWINDER_IN_STATIC_LIBRARY=ON",
        f"-DRUNTIMES_{rt}_LIBCXX_USE_COMPILER_RT=ON",
    ])
    if platform.system() == "Darwin":
      cmake_args.extend([
        "-DCOMPILER_RT_SUPPORTED_ARCH=arm64e;x86_64",
        "-DCOMPILER_RT_ENABLE_IOS=ON",
        "-DCOMPILER_RT_ENABLE_WATCHOS=ON",
        "-DCOMPILER_RT_ENABLE_TVOS=ON",
      ])

    if rt != "x86_64-unknown-linux-gnu":
        cmake_args.extend([
            f"-DRUNTIMES_{rt}_OPENMP_ENABLE_LIBOMPTARGET=OFF",
            f"-DRUNTIMES_{rt}_LIBOMP_OMPD_GDB_SUPPORT=OFF",
            f"-DRUNTIMES_{rt}_COMPILER_RT_SUPPORTED_ARCH=arm64e;x86_64",
        ])

if platform.system() == "Linux":
    cmake_args.extend([
        "-DCMAKE_C_COMPILER=clang",
        "-DCMAKE_CXX_COMPILER=clang++",
        "-DLLVM_USE_LINKER=mold",
    ])

print(' '.join(cmake_args))
subprocess.run(cmake_args, check=True)