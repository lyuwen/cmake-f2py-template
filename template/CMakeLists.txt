### setup project ###
cmake_minimum_required(VERSION 3.9)

project({{ project }}
  VERSION 1.0
  DESCRIPTION "{{ project.title() }} F2PY Module"
  LANGUAGES C Fortran
)

# Safety net
if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
  message(
    FATAL_ERROR
      "In-source builds not allowed. Please make a new directory (called a build directory) and run CMake from there.\n"
  )
endif()

# Ensure scikit-build modules
if (NOT SKBUILD)
  # # Grab Python, 3.8 or newer
  # find_package(Python 3.8 REQUIRED
  #   COMPONENTS Interpreter Development.Module NumPy)

  find_package(PythonInterp 3.8 REQUIRED)
  # Kanged --> https://github.com/Kitware/torch_liberator/blob/master/CMakeLists.txt
  # If skbuild is not the driver; include its utilities in CMAKE_MODULE_PATH
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}"
    -c "import os, skbuild; print(os.path.dirname(skbuild.__file__))"
    OUTPUT_VARIABLE SKBLD_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  list(APPEND CMAKE_MODULE_PATH "${SKBLD_DIR}/resources/cmake")
  message(STATUS "Looking in ${SKBLD_DIR}/resources/cmake for CMake modules")
endif()

# scikit-build style includes
find_package(PythonExtensions REQUIRED) # for ${PYTHON_EXTENSION_MODULE_SUFFIX}

{% if require_openmp %}
# OpenMP Package
find_package(OpenMP)
if (OPENMP_FOUND)
  set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
  set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
  set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif()
{% endif %}

{% if require_blas %}
# Lapack Package
find_package(BLAS REQUIRED)
set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${BLAS_LINKER_FLAGS}")
{% endif %}

{% if require_lapack %}
# Lapack Package
find_package(LAPACK REQUIRED)
set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${LAPACK_LINKER_FLAGS}")
{% endif %}

{% if require_openmp %}
# PThreads Package
find_package(Threads)
if (THREADS_PREFER_PTHREAD_FLAG)
  set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${THREADS_PREFER_PTHREAD_FLAG}")
  set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${THREADS_PREFER_PTHREAD_FLAG}")
  set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${THREADS_PREFER_PTHREAD_FLAG}")
endif()
{% endif %}

# Grab the variables from a local Python installation
# NumPy headers
execute_process(
  COMMAND "${PYTHON_EXECUTABLE}"
  -c "import numpy; print(numpy.get_include())"
  OUTPUT_VARIABLE NumPy_INCLUDE_DIRS
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
# F2PY headers
execute_process(
  COMMAND "${PYTHON_EXECUTABLE}"
  -c "import numpy.f2py; print(numpy.f2py.get_include())"
  OUTPUT_VARIABLE F2PY_INCLUDE_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Prepping the module
set(f2py_module_name "{{ module_name }}")
set( fortran_src_file {{ source_files }})
set(f2py_module_c "${f2py_module_name}module.c")
{% if is_f90 %}
set(f2py_module_wrapper "${f2py_module_name}-f2pywrappers2.f90")
{% else %}
set(f2py_module_wrapper "${f2py_module_name}-f2pywrappers.f")
{% endif %}

# Target for enforcing dependencies
add_custom_target({{ prefix }}
  DEPENDS "${fortran_src_file}"
)
add_custom_command(
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${f2py_module_c}" "${CMAKE_CURRENT_BINARY_DIR}/${f2py_module_wrapper}"
  COMMAND ${PYTHON_EXECUTABLE}  -m "numpy.f2py"
                   ${fortran_src_file}
                   -m "${f2py_module_name}"
                   --lower # Important
  DEPENDS "${fortran_src_file}" # Fortran source
)

add_library(${f2py_module_name} MODULE
            "${CMAKE_CURRENT_BINARY_DIR}/${f2py_module_c}" # Generated
            "${CMAKE_CURRENT_BINARY_DIR}/${f2py_module_wrapper}" # Generated
            "${F2PY_INCLUDE_DIR}/fortranobject.c"
            "${fortran_src_file}"
            )

target_include_directories(${f2py_module_name} PUBLIC
                           ${F2PY_INCLUDE_DIR}
                           ${NumPy_INCLUDE_DIRS}
                           ${PYTHON_INCLUDE_DIRS})
set_target_properties(${f2py_module_name} PROPERTIES SUFFIX "${PYTHON_EXTENSION_MODULE_SUFFIX}")
set_target_properties(${f2py_module_name} PROPERTIES PREFIX "")

# Linker fixes
if (UNIX)
  if (APPLE)
    set_target_properties(${f2py_module_name} PROPERTIES
    LINK_FLAGS  '-Wl,-dylib,-undefined,dynamic_lookup')
  else()
    set_target_properties(${f2py_module_name} PROPERTIES
  LINK_FLAGS  '-Wl,--allow-shlib-undefined')
  endif()
endif()


if (NOT SKBUILD)
  target_link_libraries(${f2py_module_name} PRIVATE Python::NumPy)
endif()

{% if require_blas %}
target_link_libraries(${f2py_module_name} PRIVATE "${BLAS_LIBRARIES}")
{% endif %}

{% if require_lapack %}
target_link_libraries(${f2py_module_name} PRIVATE "${LAPACK_LIBRARIES}")
{% endif %}

{% if require_openmp %}
if (OPENMP_FOUND)
  target_link_libraries(${f2py_module_name} PRIVATE OpenMP::OpenMP_Fortran)
endif()

if (THREADS_PREFER_PTHREAD_FLAG)
  target_link_libraries(${f2py_module_name} PRIVATE Threads::Threads)
endif()
{% endif %}

add_dependencies(${f2py_module_name} {{ prefix }}genpyf)

file(RELATIVE_PATH rel ${CMAKE_BINARY_DIR} ${CMAKE_CURRENT_BINARY_DIR})
if (rel STREQUAL "")
  set(rel ".")
endif()
set(PROGRAM_PERMISSIONS_DEFAULT
    OWNER_WRITE OWNER_READ OWNER_EXECUTE
    GROUP_READ GROUP_EXECUTE
    WORLD_READ WORLD_EXECUTE)
install(
  TARGETS ${f2py_module_name}
  DESTINATION ${rel}
  PERMISSIONS ${PROGRAM_PERMISSIONS_DEFAULT}
  )
