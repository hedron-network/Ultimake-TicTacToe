cmake_minimum_required(VERSION 3.15)
project(Game)
set(CMAKE_CXX_STANDARD 17)
set(PYBIND11_FINDPYTHON ON)

find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Collect all source files (includes bindings.cpp + Game.cpp etc.)
file(GLOB SOURCES "code/*.cpp")

# Pass ALL sources, not just bindings.cpp
pybind11_add_module(engine ${SOURCES})