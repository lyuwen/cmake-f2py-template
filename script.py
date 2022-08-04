import os
from jinja2 import Template


cwd = os.getcwd()


def process_source_files(files, relpath=False):
  if isinstance(files, str):
    files = files.replace(",", " ").replace(";", " ").split()
  if relpath:
    return " ".join(["\"" + "${CMAKE_CURRENT_SOURCE_DIR}/" + os.path.relpath(file, cwd) + "\"" for file in files])
  else:
    return " ".join(["\"" + "${CMAKE_CURRENT_SOURCE_DIR}/" + file + "\"" for file in files])


def process_prefix(prefix):
  if prefix:
    if prefix.endswith("_"):
      return prefix
    else:
      return prefix + "_"
  return ""


def main():
  project        = input("Enter project name: ").strip()
  module_name    = input("Enter module name: ").strip()
  source_files   = input("Enter paths of source files (separated by ','): ").strip()
  prefix         = input("Enter prefix for target name in cmake (optional): ").strip()
  is_f90         = input("Is the fortran source written in F90 (Yn): ").strip() or "y"
  require_blas   = input("Requires BLAS (yN): ").strip()
  require_lapack = input("Requires LAPACK (yN): ").strip()
  require_openmp = input("Requires OpenMP (yN): ").strip()
  is_f90         = is_f90.lower()         in ["y", "yes"]
  require_blas   = require_blas.lower()   in ["y", "yes"]
  require_lapack = require_lapack.lower() in ["y", "yes"]
  require_openmp = require_openmp.lower() in ["y", "yes"]

  template = Template(
      open("template/CMakeLists.txt", "r").read(),
      trim_blocks=True,
      lstrip_blocks=True,
      )

  data = {
      "project"        : project,
      "module_name"    : module_name,
      "source_files"   : process_source_files(source_files),
      "prefix"         : process_prefix(prefix),
      "is_f90"         : is_f90,
      "require_blas"   : require_blas,
      "require_lapack" : require_lapack,
      "require_openmp" : require_openmp,
      }

  file = "CMakeLists.txt"
  if os.path.exists(file):
    remove = input("CMakeLists.txt already exists, overwrite? (yN): ").strip()
    if remove.lower() in ["n", "no"]:
      return
  with open(file, "w") as f:
    f.write(template.render(data))


def test():
  project = "tetrahdron"
  module_name = "_tetrahdron"
  source_files = "../../fortran/tetrahedron/fort_tetrahedron.f90;../../fortran/tetrahedron/fort_tetra_energy.f90"
  prefix = "tet"
  require_blas   = False
  require_lapack = True
  require_openmp = True

  template = Template(
      open("template/CMakeLists.txt", "r").read(),
      trim_blocks=True,
      lstrip_blocks=True,
      )

  data = {
      "project": project,
      "module_name": module_name,
      "source_files": process_source_files(source_files),
      "prefix": process_prefix(prefix),
      "require_blas"   : require_blas,
      "require_lapack" : require_lapack,
      "require_openmp" : require_openmp,
      }

  print(template.render(data))


if __name__ == '__main__':
  main()

