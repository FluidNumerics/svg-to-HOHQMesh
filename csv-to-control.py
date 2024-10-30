import csv
import matplotlib.pyplot as plt

# debugging
write_inner_boundaries = True
inner_boundaries_exist = False

# user defined parameters
csv_file = "coordinates.csv"  # input
control_file = "pumpkin.control"  # output
core_name = control_file.split(".")[0]
mesh_file_name = core_name + ".mesh"
plot_file_name = core_name + ".tec"
stats_file_name = core_name + ".txt"
mesh_file_format = "ISM"
polynomial_order = 5
plot_file_format = "sem"
# Background grid
background_grid_size = [15.0, 15.0, 0.0]
# Smoothing
smoothing = "ON"
smoothing_type = "LinearAndCrossbarSpring"
numer_of_iterations = 25

# boundary_data = {}
boundary_data = []
with open(csv_file, "r") as f:
    reader = csv.reader(f)
    next(reader, None)  # Skip header
    boundary_data = list(reader)

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


def write_line(p0, p1, line_name=""):
    x0, y0 = p0
    x1, y1 = p1
    f.write(r"        \begin{END_POINTS_LINE}" + "\n")
    if line_name != "":
        f.write(f"            name   = {line_name}" + "\n")
    f.write(f"            xStart = {str([x0,y0,0.0])}" + "\n")
    f.write(f"            xEnd   = {str([x1,y1,0.0])}" + "\n")
    f.write(r"        \end{END_POINTS_LINE}" + "\n")


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
    for index, row in enumerate(boundary_data):
        current_xy = row[1:3]
        current_path_index = path_index[row[4]]

        new_segment = False
        new_path = False
        if row[0] == "0.000000000000000":
            new_segment = True
            current_segment_index += 1
        if current_path_index != last_path_index:
            new_path = True
            last_path_xy = row[1:3]

        # if new_segment and not new_path:
        #     if row[1:3] != last_row[1:3]:
        #         row[1:3] = last_row[1:3]
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
            # plt.scatter(float(row[1]), float(row[2]))
        # INNER BOUNDARIES ----------------------------------------------------
        elif row[5] == "InnerBoundary" and write_inner_boundaries:
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
            # plt.scatter(float(row[1]), float(row[2]))
        else:
            pass
            # raise Warning(
            #     "boundary_label needs to be 'OuterBoundary' or 'InnerBoundary'"
            # )
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

# plt.show()
