
cmake_minimum_required(VERSION 3.10)

project(BoardProject)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Collect all source files
file(GLOB SOURCES "code/*.cpp")

add_executable(Game ${SOURCES})