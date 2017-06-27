
from __future__ import division

import xml.dom.minidom

from .qgs_tools import *

from .features import Line

from .geodetic import TrackPointGPX

from .errors import GPXIOException


class Profile_Elements(object):

    def __init__(self):

        self.profile_source_type = None
        self.source_profile_line2dt = None
        self.sample_distance = None  # max spacing along profile; float
        self.topoline_colors = None
        self.plot_params = None

        self.resamp_src_line = None
        self.topo_profiles = None
        self.plane_attitudes = []
        self.curves = []
        self.curves_ids = []
        self.intersection_pts = []
        self.intersection_lines = []

    def set_topo_profiles(self, topo_profiles):

        self.topo_profiles = topo_profiles

    def add_intersections_pts(self, intersection_list):

        self.intersection_pts += intersection_list

    def add_intersections_lines(self, formation_list, intersection_line3d_list, intersection_polygon_s_list2):

        self.intersection_lines = zip(formation_list, intersection_line3d_list, intersection_polygon_s_list2)

    def get_current_dem_names(self):

        return self.topo_profiles.names

    def max_s(self):
        return self.topo_profiles.max_s()

    def min_z_topo(self):
        return self.topo_profiles.min_z()

    def max_z_topo(self):
        return self.topo_profiles.max_z()

    def min_z_plane_attitudes(self):

        # TODO:  manage case for possible nan p_z values
        return min([plane_attitude.pt_3d.p_z for plane_attitude_set in self.plane_attitudes for plane_attitude in
                    plane_attitude_set if 0.0 <= plane_attitude.sign_hor_dist <= self.max_s()])

    def max_z_plane_attitudes(self):

        # TODO:  manage case for possible nan p_z values
        return max([plane_attitude.pt_3d.p_z for plane_attitude_set in self.plane_attitudes for plane_attitude in
                    plane_attitude_set if 0.0 <= plane_attitude.sign_hor_dist <= self.max_s()])

    def min_z_curves(self):

        return min([pt_2d.p_y for multiline_2d_list in self.curves for multiline_2d in multiline_2d_list for line_2d in
                    multiline_2d.lines for pt_2d in line_2d.pts if 0.0 <= pt_2d.p_x <= self.max_s()])

    def max_z_curves(self):

        return max([pt_2d.p_y for multiline_2d_list in self.curves for multiline_2d in multiline_2d_list for line_2d in
                    multiline_2d.lines for pt_2d in line_2d.pts if 0.0 <= pt_2d.p_x <= self.max_s()])

    def min_z(self):

        min_z = self.min_z_topo()

        if len(self.plane_attitudes) > 0:
            min_z = min([min_z, self.min_z_plane_attitudes()])

        if len(self.curves) > 0:
            min_z = min([min_z, self.min_z_curves()])

        return min_z

    def max_z(self):

        max_z = self.max_z_topo()

        if len(self.plane_attitudes) > 0:
            max_z = max([max_z, self.max_z_plane_attitudes()])

        if len(self.curves) > 0:
            max_z = max([max_z, self.max_z_curves()])

        return max_z

    def add_plane_attitudes(self, plane_attitudes):

        self.plane_attitudes.append(plane_attitudes)

    def add_curves(self, multiline_2d_list, ids_list):

        self.curves.append(multiline_2d_list)
        self.curves_ids.append(ids_list)

class DEMParams(object):

    def __init__(self, layer, params):
        self.layer = layer
        self.params = params


class TopoLine3D(object):

    def __init__(self, name, line3d):
        self.name = name
        self.profile_3d = line3d  # class CartesianLine3DT, a list of CartesianPoint3DT

    def min_z(self):
        return self.profile_3d.z_min()

    def max_z(self):
        return self.profile_3d.z_max()

    def mean_z(self):
        return self.profile_3d.z_mean()

    def var_z(self):
        return self.profile_3d.z_var()

    def std_z(self):
        return self.profile_3d.z_std()

    def x_list(self):
        return [pt_3d.p_x for pt_3d in self.profile_3d.pts]

    def y_list(self):
        return [pt_3d.p_y for pt_3d in self.profile_3d.pts]

    def z_list(self):
        return [pt_3d.p_z for pt_3d in self.profile_3d.pts]

    def directional_slopes(self):
        return self.profile_3d.slopes()

    def length_2d(self):
        return self.profile_3d.length_2d()

    def get_increm_dist_3d(self):
        return self.profile_3d.incremental_length_3d()

    def get_increm_dist_2d(self):
        return self.profile_3d.incremental_length_2d()


class TopoProfiles(object):

    def __init__(self):

        self.xs = None
        self.ys = None
        self.lons = None
        self.lats = None
        self.times = None
        self.names = []
        self.s = None
        self.s3d = []
        self.elevs = []
        self.dir_slopes = []
        self.dem_params = []
        self.gpx_params = None
        self.colors = []
        self.statistics_defined = False
        self.profile_defined = False

    def max_s(self):
        return self.s[-1]

    def min_z(self):
        return min(map(np.nanmin, self.elevs))

    def max_z(self):
        return max(map(np.nanmax, self.elevs))

    @property
    def absolute_slopes(self):
        return map(np.fabs, self.dir_slopes)

class PlaneAttitude(object):

    def __init__(self, rec_id, source_point_3d, source_geol_plane, point_3d, slope_rad, dwnwrd_sense, sign_hor_dist):
        self.id = rec_id
        self.src_pt_3d = source_point_3d
        self.src_geol_plane = source_geol_plane
        self.pt_3d = point_3d
        self.slope_rad = slope_rad
        self.dwnwrd_sense = dwnwrd_sense
        self.sign_hor_dist = sign_hor_dist


def profile_from_dem(resampled_trace2d, bOnTheFlyProjection, project_crs, dem, dem_params):

    if bOnTheFlyProjection and dem.crs() != project_crs:
        trace2d_in_dem_crs = resampled_trace2d.crs_project(project_crs, dem.crs())
    else:
        trace2d_in_dem_crs = resampled_trace2d

    ln3dtProfile = Line()
    for trace_pt2d_dem_crs, trace_pt2d_project_crs in zip(trace2d_in_dem_crs.pts, resampled_trace2d.pts):
        fInterpolatedZVal = interpolate_z(dem, dem_params, trace_pt2d_dem_crs)
        pt3dtPoint = Point(trace_pt2d_project_crs.x,
                           trace_pt2d_project_crs.y,
                           fInterpolatedZVal)
        ln3dtProfile.add_pt(pt3dtPoint)

    return ln3dtProfile


def topoprofiles_from_dems(canvas, source_profile_line, sample_distance, selected_dems, selected_dem_parameters,
                           invert_profile):
    # get project CRS information
    on_the_fly_projection, project_crs = get_on_the_fly_projection(canvas)

    if invert_profile:
        line = source_profile_line.reverse_direction()
    else:
        line = source_profile_line

    resampled_line = line.densify_2d_line(sample_distance)  # line resampled by sample distance

    # calculate 3D profiles from DEMs

    dem_topolines3d = []
    for dem, dem_params in zip(selected_dems, selected_dem_parameters):
        dem_topoline3d = profile_from_dem(resampled_line,
                                          on_the_fly_projection,
                                          project_crs,
                                          dem,
                                          dem_params)
        dem_topolines3d.append(dem_topoline3d)

    # setup topoprofiles properties

    topo_profiles = TopoProfiles()

    topo_profiles.xs = np.asarray(resampled_line.x_list)
    topo_profiles.ys = np.asarray(resampled_line.y_list)
    topo_profiles.names = map(lambda dem: dem.name(), selected_dems)
    topo_profiles.s = np.asarray(resampled_line.incremental_length_2d())
    topo_profiles.s3d = map(lambda cl3dt: np.asarray(cl3dt.incremental_length_3d()), dem_topolines3d)
    topo_profiles.elevs = map(lambda cl3dt: cl3dt.z_array(), dem_topolines3d)
    topo_profiles.dir_slopes = map(lambda cl3dt: np.asarray(cl3dt.slopes()), dem_topolines3d)
    topo_profiles.dem_params = [DEMParams(dem, params) for (dem, params) in
                                zip(selected_dems, selected_dem_parameters)]

    return topo_profiles


def topoprofiles_from_gpxfile(source_gpx_path, gpx_colors, invert_profile):
    doc = xml.dom.minidom.parse(source_gpx_path)

    # define track name
    try:
        trkname = doc.getElementsByTagName('trk')[0].getElementsByTagName('name')[0].firstChild.data
    except:
        trkname = ''

    # get raw track point values (lat, lon, elev, time)
    track_raw_data = []
    for trk_node in doc.getElementsByTagName('trk'):
        for trksegment in trk_node.getElementsByTagName('trkseg'):
            for tkr_pt in trksegment.getElementsByTagName('trkpt'):
                track_raw_data.append((tkr_pt.getAttribute("lat"),
                                       tkr_pt.getAttribute("lon"),
                                       tkr_pt.getElementsByTagName("ele")[0].childNodes[0].data,
                                       tkr_pt.getElementsByTagName("time")[0].childNodes[0].data))

    # reverse profile orientation if requested
    if invert_profile:
        track_data = track_raw_data[::-1]
    else:
        track_data = track_raw_data

    # create list of TrackPointGPX elements
    track_points = []
    for val in track_data:
        gpx_trackpoint = TrackPointGPX(*val)
        track_points.append(gpx_trackpoint)

    # check for the presence of track points
    if len(track_points) == 0:
        raise GPXIOException("No track point found in this file")

    # calculate delta elevations between consecutive points
    delta_elev_values = [np.nan]
    for ndx in range(1, len(track_points)):
        delta_elev_values.append(track_points[ndx].elev - track_points[ndx - 1].elev)

    # convert original values into ECEF values (x, y, z in ECEF global coordinate system)
    trk_ECEFpoints = map(lambda trck: trck.as_pt3dt(), track_points)

    # calculate 3D distances between consecutive points
    dist_3D_values = [np.nan]
    for ndx in range(1, len(trk_ECEFpoints)):
        dist_3D_values.append(trk_ECEFpoints[ndx].dist_3d(trk_ECEFpoints[ndx - 1]))

    # calculate slope along track
    dir_slopes = []
    for delta_elev, dist_3D in zip(delta_elev_values, dist_3D_values):
        try:
            slope = degrees(asin(delta_elev / dist_3D))
        except:
            slope = 0.0
        dir_slopes.append(slope)

    # calculate horizontal distance along track
    horiz_dist_values = []
    for slope, dist_3D in zip(dir_slopes, dist_3D_values):
        try:
            horiz_dist_values.append(dist_3D * cos(radians(slope)))
        except:
            horiz_dist_values.append(np.nan)

    # defines the cumulative 2D distance values
    cum_distances_2D = [0.0]
    for ndx in range(1, len(horiz_dist_values)):
        cum_distances_2D.append(cum_distances_2D[-1] + horiz_dist_values[ndx])

    # defines the cumulative 3D distance values
    cum_distances_3D = [0.0]
    for ndx in range(1, len(dist_3D_values)):
        cum_distances_3D.append(cum_distances_3D[-1] + dist_3D_values[ndx])

    lat_values = [track.lat for track in track_points]
    lon_values = [track.lon for track in track_points]
    time_values = [track.time for track in track_points]
    elevations = [track.elev for track in track_points]

    topo_profiles = TopoProfiles()

    topo_profiles.lons = np.asarray(lon_values)
    topo_profiles.lats = np.asarray(lat_values)
    topo_profiles.times = time_values
    topo_profiles.names = [trkname]  # [] required for compatibility with DEM case
    topo_profiles.s = np.asarray(cum_distances_2D)
    topo_profiles.s3d = [np.asarray(cum_distances_3D)]  # [] required for compatibility with DEM case
    topo_profiles.elevs = [np.asarray(elevations)]  # [] required for compatibility with DEM case
    topo_profiles.dir_slopes = [np.asarray(dir_slopes)]  # [] required for compatibility with DEM case
    topo_profiles.colors = gpx_colors

    return topo_profiles
