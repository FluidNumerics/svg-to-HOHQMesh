#!/usr/bin/env python
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// #
#
# Maintainers : support@fluidnumerics.com
# Official Repository : https://github.com/FluidNumerics/self/
#
# Copyright © 2024 Fluid Numerics LLC
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUsLESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARIsLG IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// #

import svgpathtools
import csv
import numpy as np
import xml.etree.ElementTree as ET
from numpy import linspace
from math import sqrt
import matplotlib.pyplot as plt
import sys
import os

# check arguments
if len(sys.argv) < 2:
    raise ValueError("No .svg file specified.")

else:
    svg_file = sys.argv[1]
    basename = os.path.basename(svg_file)
    core_name = os.path.splitext(basename)[0]
    control_file = f"{core_name}.control"

# debugging
write_inner_boundaries = True
plot = False

# file names
csv_file = "coordinates.csv"  # csv
mesh_file_name = core_name + ".mesh"
plot_file_name = core_name + ".tec"
stats_file_name = core_name + ".txt"

# HOHQMesh control file variables
mesh_file_format = "ISM"
polynomial_order = 5
plot_file_format = "sem"
background_grid_size = [5.0, 5.0, 0.0]
# Smoothing
smoothing = "ON"
smoothing_type = "LinearAndCrossbarSpring"
numer_of_iterations = 1000

# svg-to-csv ------------------------------------------------------------------
tree = ET.parse(svg_file)
root = tree.getroot()
# get page height
page_height = float(root.attrib["viewBox"].split()[3])

# n_nodes = 6 is usually sufficient, but particularly
# complex segments might require more nodes
n_nodes = 6

# Used to make sure paths close correctly
tolerance = 1e-4

with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["t", "x", "y", "z", "path_label", "boundary_label"])
    for g in root.findall(".//{http://www.w3.org/2000/svg}g"):
        g_label = g.get("{http://www.inkscape.org/namespaces/inkscape}label")
        for path_element in g.findall(".//{http://www.w3.org/2000/svg}path"):
            path_label = path_element.get(
                "{http://www.inkscape.org/namespaces/inkscape}label"
            )
            d = path_element.get("d")
            path = svgpathtools.parse_path(d)
            name = path_element.get("id")

            # Sometimes SVGpathtools will append a Line
            # if it thinks the path doesn't connect
            for segment in path:
                if type(segment) == svgpathtools.path.Line and len(path) - 1:
                    distance = sqrt(
                        (segment.start.real - segment.end.real) ** 2
                        + (segment.start.imag - segment.end.imag) ** 2
                    )
                    if distance < tolerance:
                        print(
                            "WARNING: Skipping erroneous line between path start and end \n"
                        )
                        print(name)
                        print(segment.start)
                        print(segment.end)

                        path = path[:-1]

            for i, segment in enumerate(path):

                for t in linspace(0, 1, n_nodes, endpoint=True):
                    point = segment.point(t)
                    x, y = point.real, point.imag

                    # segment start and end
                    if t == 1.0:
                        last_segment_x1, last_segment_y1 = x, y
                    elif t == 0.0 and i != 0:
                        error = sqrt(
                            (x - last_segment_x1) ** 2 + (y - last_segment_y1) ** 2
                        )
                        if error > 1e-4:
                            print(
                                "WARNING: Large error between segment start and end points:\n"
                            )
                            print(f"end point:\n    {x}\n    {y}\n")
                            print(
                                f"start point:\n    {last_segment_x1}\n    {last_segment_y1}\n"
                            )
                        x, y = last_segment_x1, last_segment_y1

                    # path start and end
                    if t == 0.0 and i == 0:
                        path_x0, path_y0 = x, y
                    elif t == 1.0 and i == len(path) - 1:
                        error = sqrt((x - path_x0) ** 2 + (y - path_y0) ** 2)
                        if error >= tolerance:
                            print(
                                "WARNING: Large error between path start and end points:\n"
                            )
                            print(f"path:\n    {name}")
                            print(f"end point:\n    {x}\n    {y}\n")
                            print(f"start point:\n    {path_x0}\n    {path_y0}\n")
                        x, y = path_x0, path_y0

                    y = page_height - y
                    writer.writerow(
                        [
                            f"{float(t):.15f}",
                            f"{float(x):.15f}",
                            f"{float(y):.15f}",
                            "0.0",
                            path_label,
                            g_label,
                        ]
                    )


# csv-to-control --------------------------------------------------------------

boundary_data = []
with open(csv_file, "r") as f:
    reader = csv.reader(f)
    next(reader, None)  # Skip header
    boundary_data = list(reader)


inner_boundaries_exist = False
path_index = {}
index_counter = 0
knot_count = []
segment_counter = 0
for i, row in enumerate(boundary_data):
    path_string = row[4]
    if path_string not in path_index:
        path_index[path_string] = index_counter
        index_counter += 1
        knot_count.append([])
        segment_counter = 0
    if row[0] == "0.000000000000000":
        knot_count[index_counter - 1].append(0)
        segment_counter += 1
    knot_count[index_counter - 1][segment_counter - 1] += 1

with open(control_file, "w") as f:
    f.write(r"\begin{CONTROL_INPUT}" + "\n")
    f.write(r"    \begin{RUN_PARAMETERS}" + "\n")
    f.write(f"        mesh file name   = {mesh_file_name}" + "\n")
    f.write(f"        plot file name   = {plot_file_name}" + "\n")
    f.write(f"        stats file name  = {stats_file_name}" + "\n")
    f.write(f"        mesh file format   = {mesh_file_format}" + "\n")
    f.write(f"        polynomial order = {polynomial_order}" + "\n")
    f.write(f"        plot file format = {plot_file_format}" + "\n")
    f.write(r"    \end{RUN_PARAMETERS}" + "\n")
    f.write(r"    \begin{BACKGROUND_GRID}" + "\n")
    f.write(f"        background grid size = {str(background_grid_size)}" + "\n")
    f.write(r"    \end{BACKGROUND_GRID}" + "\n")
    f.write(r"    \begin{SPRING_SMOOTHER}" + "\n")
    f.write(f"        smoothing            = {smoothing}" + "\n")
    f.write(f"        smoothing type       = {smoothing_type}" + "\n")
    f.write(f"        number of iterations = {numer_of_iterations}" + "\n")
    f.write(r"    \end{SPRING_SMOOTHER}" + "\n")
    f.write(r"\end{CONTROL_INPUT}" + "\n")
    f.write(r"\begin{MODEL}" + "\n")

    last_path_index = -1
    current_segment_index = -1
    shoelace_area = 0
    position_vectors = np.zeros((1, 2))

    for index, row in enumerate(boundary_data):
        current_path_index = path_index[row[4]]

        new_segment = False
        new_path = False
        if row[0] == "0.000000000000000":
            new_segment = True
            current_segment_index += 1
        if current_path_index != last_path_index:
            new_path = True

        position_vector = np.array(
            [
                float(row[1]),
                float(row[2]),
            ]
        ).reshape((1, 2))

        # Check if all paths are clockwise ------------------------------------
        if not new_path:
            position_vectors = np.concatenate(
                (position_vectors, position_vector), axis=0
            )
        if index == 0:
            init_path_row = row

        if (new_path and index != 0) or (row == boundary_data[-1]):
            position_vectors[0] = np.array(
                [
                    float(last_row[1]),
                    float(last_row[2]),
                ]
            ).reshape((1, 2))
            for i in range(position_vectors.shape[0] - 1):
                local_vectors = position_vectors[i : i + 2]
                shoelace_area += np.linalg.det(local_vectors)
            local_vectors = position_vectors[-1].reshape((1, 2))
            local_vectors = np.concatenate(
                (local_vectors, position_vectors[0].reshape((1, 2))), axis=0
            )
            shoelace_area += np.linalg.det(local_vectors)
            if shoelace_area < 0:
                raise ValueError(
                    f"path '{init_path_row[4]}' is reversed. HOHQMesh will fail to run."
                )
            shoelace_area = 0
            position_vectors = np.zeros((1, 2))
            init_path_row = row

        coordinates = " ".join(row[0:4])

        # OUTER BOUNDARY ------------------------------------------------------
        if row[5] == "OuterBoundary":
            spline_name = f"OuterSpline{current_segment_index + 1}"
            n_knots = knot_count[current_path_index][current_segment_index]
            if index == 0:
                f.write(r"\begin{OUTER_BOUNDARY}" + "\n")
                # f.write(r"    \begin{CHAIN}" + "\n")
                # f.write(r"        name = OuterChain" + "\n")
                f.write(r"        \begin{SPLINE_CURVE}" + "\n")
                f.write(f"            name   = {spline_name}" + "\n")
                f.write(f"            nKnots = {n_knots}" + "\n")
                f.write(r"            \begin{SPLINE_DATA}" + "\n")
            elif new_segment:
                f.write(r"            \end{SPLINE_DATA}" + "\n")
                f.write(r"        \end{SPLINE_CURVE}" + "\n")
                f.write(r"        \begin{SPLINE_CURVE}" + "\n")
                f.write(f"            name   = {spline_name}" + "\n")
                f.write(f"            nKnots = {n_knots}" + "\n")
                f.write(r"            \begin{SPLINE_DATA}" + "\n")
            f.write("                " + coordinates + "\n")
            plt.scatter(float(row[1]), float(row[2]))

        # INNER BOUNDARIES ----------------------------------------------------
        elif row[5] == "InnerBoundaries" and write_inner_boundaries:
            inner_boundaries_exist = True
            if last_path_index == 0:
                current_segment_index = 0
                n_knots = knot_count[current_path_index][current_segment_index]

                f.write(r"            \end{SPLINE_DATA}" + "\n")
                f.write(r"        \end{SPLINE_CURVE}" + "\n")
                # f.write(r"    \end{CHAIN}" + "\n")
                f.write(r"\end{OUTER_BOUNDARY}" + "\n")
                f.write(r"\begin{INNER_BOUNDARIES}" + "\n")
                f.write(r"    \begin{CHAIN}" + "\n")
                f.write(f"        name = InnerChain1" + "\n")
                f.write(r"        \begin{SPLINE_CURVE}" + "\n")
                f.write(f"            name   = InnerSpline1_1" + "\n")
                f.write(f"            nKnots = {n_knots}" + "\n")
                f.write(r"            \begin{SPLINE_DATA}" + "\n")

            elif new_segment and not new_path:
                n_knots = knot_count[current_path_index][current_segment_index]
                spline_name = (
                    f"InnerSpline{current_path_index}_{current_segment_index+1}"
                )

                f.write(r"            \end{SPLINE_DATA}" + "\n")
                f.write(r"        \end{SPLINE_CURVE}" + "\n")
                f.write(r"        \begin{SPLINE_CURVE}" + "\n")
                f.write(f"            name   = {spline_name}" + "\n")
                f.write(f"            nKnots = {n_knots}" + "\n")
                f.write(r"            \begin{SPLINE_DATA}" + "\n")

            elif new_path:
                current_segment_index = 0
                n_knots = knot_count[current_path_index][current_segment_index]
                spline_name = (
                    f"InnerSpline{current_path_index}_{current_segment_index+1}"
                )
                f.write(r"            \end{SPLINE_DATA}" + "\n")
                f.write(r"        \end{SPLINE_CURVE}" + "\n")
                f.write(r"    \end{CHAIN}" + "\n")
                f.write(r"    \begin{CHAIN}" + "\n")
                f.write(f"        name = InnerChain{current_path_index}" + "\n")
                f.write(r"        \begin{SPLINE_CURVE}" + "\n")
                f.write(f"            name   = {spline_name}" + "\n")
                f.write(f"            nKnots = {n_knots}" + "\n")
                f.write(r"            \begin{SPLINE_DATA}" + "\n")
            f.write("                " + coordinates + "\n")
            plt.scatter(float(row[1]), float(row[2]))
        else:
            # layers not named "OuterBoundary" or "InnerBoundaries" are skipped
            pass

        last_path_index = current_path_index
        last_segment_index = current_segment_index
        last_row = row

    if write_inner_boundaries and inner_boundaries_exist:
        f.write(r"            \end{SPLINE_DATA}" + "\n")
        f.write(r"        \end{SPLINE_CURVE}" + "\n")
        f.write(r"    \end{CHAIN}" + "\n")
        f.write(r"\end{INNER_BOUNDARIES}" + "\n")
        f.write(r"\end{MODEL}" + "\n")
        f.write(r"\end{FILE}")
    else:
        f.write(r"            \end{SPLINE_DATA}" + "\n")
        f.write(r"        \end{SPLINE_CURVE}" + "\n")
        f.write(r"\end{OUTER_BOUNDARY}" + "\n")
        f.write(r"\end{MODEL}" + "\n")
        f.write(r"\end{FILE}")

if plot:
    plt.show()
