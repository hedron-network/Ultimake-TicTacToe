#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // enables std::vector conversion
#include "game.h"
namespace py = pybind11;

PYBIND11_MODULE(engine, m) {
    py::class_<Game>(m, "Game")
        .def(py::init<>())
        .def("get_state", &Game::get_state)     // vector<float>
        .def("undo", &Game::undo)
        .def("get_legal_moves", &Game::get_legal_moves)
        .def("apply_move", &Game::apply_move)
        .def("get_winner", &Game::get_winner)
        .def("is_done", &Game::is_done)
}