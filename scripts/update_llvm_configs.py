import argparse
import time
import hashlib
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument("--tag", type=str, required=True)

args = parser.parse_args()

all_os = ["linux", "windows", "macos"]
all_cpu = ["aarch64", "riscv64", "x86_64"]
all_artifacts = ["clang", "clang-tools", "clangd", "bolt", "libcxx", "lld"]

today = time.strftime("%Y-%m-%d")

readme = ""

for os_ in all_os:
  for cpu in all_cpu:
    for art in all_artifacts:
      try:
        print(f"Testing {args.tag}-{os_}-{cpu}-{art}.tar.zst")
        path = f"artifacts/{os_}-{cpu}-toolchain/{args.tag}-{os_}-{cpu}-{art}.tar.zst"
        f = open(path, 'rb')
        hash = hashlib.file_digest(f, 'sha256').hexdigest()
        f.close()

        print(f"Hash is {hash}")

        config_path = f"llvm/{os_}/{cpu}/{art}.json"
        config_file = open(config_path, 'r')
        data = json.load(config_file)
        config_file.close()
        print("Loaded config")
        url = f"https://github.com/cpp-toolchains/toolchains/releases/download/{args.tag}-{today}/{args.tag}-{os_}-{cpu}-{art}.tar.zst"
        if args.tag not in data:
          data[args.tag] = {}
        data[args.tag]["url"] = url
        data[args.tag]["sha256"] = hash
        config_file = open(config_file, 'w')
        config_file.write(json.dumps(data, indent=4))
        config_file.close()

        print("Ok")

        readme += f"{hash} {args.tag}-{os_}-{cpu}-{art}.tar.zst\n"
      except Exception as e:
        print(f"Failed - {e}")

f = open("RELEASE_NOTES.txt", 'w')
f.write(readme)
f.close()