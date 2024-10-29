import svgpathtools
import csv
import xml.etree.ElementTree as ET
from numpy import linspace
from math import sqrt


svg_file = "pumpkin-smooth.svg"  # input
csv_file = "coordinates.csv"  # output

tree = ET.parse(svg_file)
root = tree.getroot()

n_nodes = 20
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
            # transforms = path_element.get("transform")
            path = svgpathtools.parse_path(d)
            # for transform in transforms:
            #     path = svgpathtools.transform_path(
            #         path,
            #         transform,
            #     )

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
                        if error > 1e-4:
                            print(
                                "WARNING: Large error between path start and end points:\n"
                            )
                            print(f"end point:\n    {x}\n    {y}\n")
                            print(f"start point:\n    {path_x0}\n    {path_y0}\n")
                        x, y = path_x0, path_y0
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
