
from math import sqrt, degrees, acos, asin, atan, atan2, radians
import numpy as np

from .qgs_tools import project_point

from ..gsf.geometry import Vect, GPlane, Point, GAxis

MIN_2D_SEPARATION_THRESHOLD = 1e-10
MINIMUM_SEPARATION_THRESHOLD = 1e-10
MINIMUM_VECTOR_MAGNITUDE = 1e-10


class Segment(object):
    
    def __init__(self, start_pt, end_pt):

        self._start_pt = start_pt  # .clone()
        self._end_pt = end_pt  # .clone()

    @property
    def start_pt(self):

        return self._start_pt

    @property
    def end_pt(self):

        return self._end_pt

    def clone(self):

        return Segment(self.start_pt, self.end_pt)

    def increasing_x(self):

        if self.end_pt.x < self.start_pt.x:
            return Segment(self.end_pt, self.start_pt)
        else:
            return self.clone()

    @property
    def x_range(self):

        if self.start_pt.x < self.end_pt.x:
            return self.start_pt.x, self.end_pt.x
        else:
            return self.end_pt.x, self.start_pt.x

    @property
    def y_range(self):

        if self.start_pt.y < self.end_pt.y:
            return self.start_pt.y, self.end_pt.y
        else:
            return self.end_pt.y, self.start_pt.y

    @property
    def z_range(self):

        if self.start_pt.z < self.end_pt.z:
            return self.start_pt.z, self.end_pt.z
        else:
            return self.end_pt.z, self.start_pt.z

    @property
    def delta_x(self):

        return self.end_pt.x - self.start_pt.x

    @property
    def delta_y(self):

        return self.end_pt.y - self.start_pt.y

    @property
    def delta_z(self):

        return self.end_pt.z - self.start_pt.z

    @property
    def length_2d(self):

        return self.start_pt.dist_2d(self.end_pt)

    @property
    def length_3d(self):

        return self.start_pt.dist_3d(self.end_pt)

    def vector(self):

        return Vect(self.delta_x,
                    self.delta_y,
                    self.delta_z)

    def segment_2d_m(self):

        return (self.end_pt.y - self.start_pt.y) / (self.end_pt.x - self.start_pt.x)

    def segment_2d_p(self):

        return self.start_pt.y - self.segment_2d_m() * self.start_pt.x

    def intersection_2d_pt(self, another):

        assert self.length_2d > 0.0
        assert another.length_2d > 0.0

        if self.start_pt.x == self.end_pt.x:  # self segment parallel to y axis
            x0 = self.start_pt.x
            try:
                m1, p1 = another.segment_2d_m(), another.segment_2d_p()
            except:
                return None
            y0 = m1 * x0 + p1
        elif another.start_pt.x == another.end_pt.x:  # another segment parallel to y axis
            x0 = another.start_pt.x
            try:
                m1, p1 = self.segment_2d_m(), self.segment_2d_p()
            except:
                return None
            y0 = m1 * x0 + p1
        else:  # no segment parallel to y axis
            m0, p0 = self.segment_2d_m(), self.segment_2d_p()
            m1, p1 = another.segment_2d_m(), another.segment_2d_p()
            x0 = (p1 - p0) / (m0 - m1)
            y0 = m0 * x0 + p0

        return Point(x0, y0)

    def contains_2d_pt(self, pt2d):

        segment_length2d = self.length_2d
        segmentstart_pt2d_distance = self.start_pt.dist_2d(pt2d)
        segmentend_pt2d_distance = self.end_pt.dist_2d(pt2d)

        if segmentstart_pt2d_distance > segment_length2d or \
           segmentend_pt2d_distance > segment_length2d:
            return False
        else:
            return True

    def fast_2d_contains_pt(self, pt2d):
        """
        to work properly, requires that the pt lies on the line defined by the segment
        """

        range_x = self.x_range
        range_y = self.y_range

        if range_x[0] <= pt2d.x <= range_x[1] or \
           range_y[0] <= pt2d.y <= range_y[1]:
            return True
        else:
            return False

    def scale(self, scale_factor):

        delta_x = self.delta_x * scale_factor
        delta_y = self.delta_y * scale_factor
        delta_z = self.delta_z * scale_factor

        end_pt = Point(self.start_pt.x + delta_x,
                       self.start_pt.y + delta_y,
                       self.start_pt.z + delta_z)

        return Segment(self.start_pt,
                       end_pt)

    def densify_2d(self, densify_distance):

        assert densify_distance > 0.0

        length2d = self.length_2d

        assert length2d > 0.0

        generator_vector = self.vector().versor.scale(densify_distance)

        interpolated_line = Line([self.start_pt])
        n = 0
        while True:
            n += 1
            new_pt = self.start_pt.vect_offset(generator_vector.scale(n))
            if self.start_pt.dist_2d(new_pt) >= length2d:
                break
            interpolated_line.add_pt(new_pt)
        interpolated_line.add_pt(self.end_pt)

        return interpolated_line


class Line(object):
    """
    CartesianLine3DT is a list of Point objects
    """

    def __init__(self, pts=None):

        if pts is None:
            pts = []
        self._pts = pts  # [pt_3dt.clone() for pt_3dt in pts_3dt]

    @property
    def pts(self):

        return self._pts

    @property
    def num_pts(self):

        return len(self.pts)

    def clone(self):

        return Line(self.pts)

    def add_pt(self, pt):

        self.pts.append(pt)

    def add_pts(self, pt_list):

        self._pts += pt_list

    @property
    def x_list(self):

        return [pt.x for pt in self.pts]

    @property
    def y_list(self):

        return [pt.y for pt in self.pts]

    @property
    def z_list(self):

        return [pt.z for pt in self.pts]

    def xy_lists(self):

        return self.x_list, self.y_list

    @property
    def x_min(self):

        return min([x for x in self.x_list if not np.isnan(x)])

    @property
    def x_max(self):

        return max([x for x in self.x_list if not np.isnan(x)])

    @property
    def y_min(self):

        return min([y for y in self.y_list if not np.isnan(y)])

    @property
    def y_max(self):

        return max([y for y in self.y_list if not np.isnan(y)])

    @property
    def z_min(self):

        return min([z for z in self.z_list if not np.isnan(z)])

    @property
    def z_max(self):

        return max([z for z in self.z_list if not np.isnan(z)])


    def z_array(self):

        return np.array(self.z_list)

    def z_array_not_nan(self):

        return np.array(filter(lambda pt: not np.isnan(pt.p_z), self.pts))

    @property
    def z_mean(self):

        return np.nanmean(self.z_array())

    @property
    def z_var(self):

        return np.nanvar(self.z_array())

    @property
    def z_std(self):

        return np.nanstd(self.z_array())

    def remove_coincident_successive_points(self):

        assert self.num_pts > 0

        new_line = Line(self.pts[0])
        for ndx in range(1, self.num_pts):
            if not self.pts[ndx].coincident(new_line.pts[-1]):
                new_line.add_pt(self.pts[ndx])
        return new_line

    def join(self, another):
        """
        Joins together two lines and returns the join as a new line without point changes,
        with possible overlapping points
        and orientation mismatches between the two original lines
        """

        return Line(self.pts + another.pts)

    @property
    def length_3d(self):

        length = 0.0
        for ndx in range(self.num_pts - 1):
            length += self.pts[ndx].dist_3d(self.pts[ndx + 1])
        return length

    @property
    def length_2d(self):

        length = 0.0
        for ndx in range(self.num_pts - 1):
            length += self.pts[ndx].dist_2d(self.pts[ndx + 1])
        return length

    def incremental_length_3d(self):

        incremental_length_list = []
        length = 0.0
        incremental_length_list.append(length)
        for ndx in range(self.num_pts - 1):
            length += self.pts[ndx].dist_3d(self.pts[ndx + 1])
            incremental_length_list.append(length)

        return incremental_length_list

    def incremental_length_2d(self):

        incremental_length_list = []
        length = 0.0
        incremental_length_list.append(length)
        for ndx in range(self.num_pts - 1):
            length += self.pts[ndx].dist_2d(self.pts[ndx + 1])
            incremental_length_list.append(length)

        return incremental_length_list

    def reverse_direction(self):

        new_line = self.clone()
        new_line.pts.reverse()  # in-place operation on new_line

        return new_line

    def slopes(self):

        slopes_list = []
        for ndx in range(self.num_pts - 1):
            vector = Segment(self.pts[ndx], self.pts[ndx + 1]).vector()
            slopes_list.append(vector.slope)
        slopes_list.append(np.nan)  # slope value for last point is unknown

        return slopes_list

    def absolute_slopes(self):

        return map(abs, self.slopes())

    def crs_project(self, srcCrs, destCrs):

        points = []
        for point in self.pts:
            destCrs_point = project_point(point, srcCrs, destCrs)
            points.append(destCrs_point)

        return Line(points)


class MultiLine(object):
    # CartesianMultiLine3DT is a list of CartesianLine3DT objects

    def __init__(self, lines_list=None):

        if lines_list is None:
            lines_list = []
        self._lines = lines_list

    @property
    def lines(self):

        return self._lines

    def add(self, line):

        return MultiLine(self.lines + [line])

    def clone(self):

        return MultiLine(self.lines)

    @property
    def num_parts(self):

        return len(self.lines)

    @property
    def num_points(self):

        num_points = 0
        for line in self.lines:
            num_points += line.num_pts

        return num_points

    @property
    def x_min(self):

        return min([line.x_min for line in self.lines])

    @property
    def x_max(self):

        return max([line.x_max for line in self.lines])

    @property
    def y_min(self):

        return min([line.y_min for line in self.lines])

    @property
    def y_max(self):

        return max([line.y_max for line in self.lines])

    def is_continuous(self):

        for line_ndx in range(len(self._lines) - 1):
            if not self.lines[line_ndx].pts[-1].coincident(self.lines[line_ndx + 1].pts[0]) or \
                    not self.lines[line_ndx].pts[-1].coincident(self.lines[line_ndx + 1].pts[-1]):
                return False

        return True

    def is_unidirectional(self):

        for line_ndx in range(len(self.lines) - 1):
            if not self.lines[line_ndx].pts[-1].coincident(self.lines[line_ndx + 1].pts[0]):
                return False

        return True

    def to_line(self):

        return Line([point for line in self.lines for point in line.pts])


    def crs_project(self, srcCrs, destCrs):

        lines = []
        for line in self.lines:
            lines.append(line.crs_project(srcCrs, destCrs))

        return MultiLine(lines)

    def densify(self, sample_distance):

        lDensifiedMultilinea = []
        for line in self.lines:
            lDensifiedMultilinea.append(line.densify_2d(sample_distance))

        return MultiLine(lDensifiedMultilinea)

    def remove_coincident_points(self):

        cleaned_lines = []
        for lines in self.lines:
            cleaned_lines.append(lines.remove_coincident_successive_points())

        return MultiLine(cleaned_lines)


class ParamLine3D(object):
    """
    parametric line
    srcPt: source Point
    l, m, n: .....
    """

    def __init__(self, srcPt, l, m, n):

        assert -1.0 <= l <= 1.0
        assert -1.0 <= m <= 1.0
        assert -1.0 <= n <= 1.0

        self._srcPt = srcPt
        self._l = l
        self._m = m
        self._n = n

    def intersect_cartes_plane(self, cartes_plane):
        """
        Return intersection point between parametric line and Cartesian plane
        """

        # line parameters
        x1, y1, z1 = self._srcPt.x, self._srcPt.y, self._srcPt.p_z
        l, m, n = self._l, self._m, self._n

        # Cartesian plane parameters
        a, b, c, d = cartes_plane.a, cartes_plane.b, cartes_plane.c, cartes_plane.d

        try:
            k = (a * x1 + b * y1 + c * z1 + d) / (a * l + b * m + c * n)
        except ZeroDivisionError:
            return None

        return Point(x1 - l * k,
                     y1 - m * k,
                     z1 - n * k)


def eq_xy_pair(xy_pair_1, xy_pair_2):

    if xy_pair_1[0] == xy_pair_2[0] and xy_pair_1[1] == xy_pair_2[1]:
        return True

    return False


def remove_equal_consecutive_xypairs(xy_list):

    out_xy_list = [xy_list[0]]

    for n in range(1, len(xy_list)):
        if not eq_xy_pair(xy_list[n], out_xy_list[-1]):
            out_xy_list.append(xy_list[n])

    return out_xy_list


def xytuple_list_to_Line(xy_list):

    return Line([Point(x, y) for (x, y) in xy_list])


def xytuple_l2_to_MultiLine(xytuple_list2):

    # input is a list of list of (x,y) values

    assert len(xytuple_list2) > 0
    lines_list = []
    for xy_list in xytuple_list2:
        assert len(xy_list) > 0
        lines_list.append(xytuple_list_to_Line(xy_list))

    return MultiLine(lines_list)



def merge_lines(lines, progress_ids):
    """
    lines: a list of list of (x,y,z) tuples for multilines
    """

    sorted_line_list = [line for (_, line) in sorted(zip(progress_ids, lines))]

    line_list = []
    for line in sorted_line_list:

        line_type, line_geometry = line

        if line_type == 'multiline':
            path_line = xytuple_l2_to_MultiLine(line_geometry).to_line()
        elif line_type == 'line':
            path_line = xytuple_list_to_Line(line_geometry)
        else:
            continue

        line_list.append(path_line)  # now a list of Lines

    # now the list of Lines is transformed into a single Point
    return MultiLine(line_list).to_line().remove_coincident_successive_points()
