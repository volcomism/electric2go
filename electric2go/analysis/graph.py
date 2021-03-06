# coding=utf-8

from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
import numpy as np

from ..systems import get_city_by_result_dict


# speed ranges are designated as: 0-5; 5-15; 15-30; 30+
SPEEDS = [(5, 'r'), (15, 'y'), (30, 'g'), (float('inf'), 'b')]


# strictly not correct as lat/lng isn't a grid, but close enough at city scales
def map_latitude(city_data, latitudes):
    south = city_data['MAP_LIMITS']['SOUTH']
    north = city_data['MAP_LIMITS']['NORTH']
    return ((latitudes - south) / (north - south)) * city_data['MAP_SIZES']['MAP_Y']


def map_longitude(city_data, longitudes):
    west = city_data['MAP_LIMITS']['WEST']
    east = city_data['MAP_LIMITS']['EAST']
    return ((longitudes - west) / (east - west)) * city_data['MAP_SIZES']['MAP_X']


def is_latlng_in_bounds(city_data, latlng):
    lat = latlng[0]
    lng = latlng[1]

    is_lat = city_data['BOUNDS']['SOUTH'] <= lat <= city_data['BOUNDS']['NORTH']
    is_lng = city_data['BOUNDS']['WEST'] <= lng <= city_data['BOUNDS']['EAST']

    return is_lat and is_lng


def get_pixel_size(city_data):
    # find the length in metres represented by one pixel on graph in both lat and lng direction

    lat_range = city_data['MAP_LIMITS']['NORTH'] - city_data['MAP_LIMITS']['SOUTH']
    lat_in_m = lat_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LATITUDE']
    pixel_in_lat_m = lat_in_m / city_data['MAP_SIZES']['MAP_Y']

    lng_range = city_data['MAP_LIMITS']['EAST'] - city_data['MAP_LIMITS']['WEST']
    lng_in_m = lng_range * city_data['DEGREE_LENGTHS']['LENGTH_OF_LONGITUDE']
    pixel_in_lng_m = lng_in_m / city_data['MAP_SIZES']['MAP_X']

    return pixel_in_lat_m, pixel_in_lng_m


def get_mean_pixel_size(city_data):
    # find the length in metres represented by one pixel on graph

    # take mean of latitude- and longitude-based numbers,
    # which is not quite correct but more than close enough for most uses

    pixel_in_m = get_pixel_size(city_data)

    return (pixel_in_m[0] + pixel_in_m[1]) / 2


def make_graph_axes(city_data, background=None):
    """
    Sets up figure area and axes for a city to be graphed.
    :param background: path to an image file to load,
    or a matplotlib.imshow()-compatible value, or None
    :return: tuple(matplotlib_fig, matplotlib_ax)
    """

    # set up figure area

    dpi = 80
    # i actually have no idea why this is necessary, but the 
    # figure sizes are wrong otherwise. ???
    dpi_adj_x = 0.775
    dpi_adj_y = 0.8

    # TODO: see if it is possible to reuse figure or axes rather than
    # creating new ones every time
    f = plt.figure(dpi=dpi)
    f.set_size_inches(city_data['MAP_SIZES']['MAP_X']/dpi_adj_x/dpi,
                      city_data['MAP_SIZES']['MAP_Y']/dpi_adj_y/dpi)

    ax = f.add_subplot(111)
    ax.axis([0, city_data['MAP_SIZES']['MAP_X'], 0, city_data['MAP_SIZES']['MAP_Y']])

    # remove visible axes and figure frame
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_frame_on(False)

    if background is not None:
        ax.imshow(background, origin='lower', aspect='auto')

    return f, ax


def plot_points(ax, points, colour, symbol):
    ys, xs = zip(*points)

    ax.plot(xs, ys, colour + symbol)

    return ax


def plot_geopoints(ax, city_data, geopoints_dict, symbol):
    for colour in geopoints_dict:
        if len(geopoints_dict[colour]):
            lats, lngs = zip(*geopoints_dict[colour])

            latitudes = map_latitude(city_data, np.array(lats))
            longitudes = map_longitude(city_data, np.array(lngs))

            ax = plot_points(ax, zip(latitudes, longitudes), colour, symbol)

    return ax


def plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour='#aaaaaa'):
    for i in range(len(lines_start_y)):
        l = plt.Line2D([lines_start_x[i], lines_end_x[i]],
                       [lines_start_y[i], lines_end_y[i]],
                       color=colour)
        ax.add_line(l)

    return ax


def plot_geolines(ax, city_data, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour='#aaaaaa'):
    # translate into map coordinates
    lines_start_y = map_latitude(city_data, np.array(lines_start_lat))
    lines_start_x = map_longitude(city_data, np.array(lines_start_lng))
    lines_end_y = map_latitude(city_data, np.array(lines_end_lat))
    lines_end_x = map_longitude(city_data, np.array(lines_end_lng))

    return plot_lines(ax, lines_start_y, lines_start_x, lines_end_y, lines_end_x, colour)


def plot_trips(ax, city_data, trips, colour='#aaaaaa'):
    lines_start_lat = [t['from'][0] for t in trips]
    lines_start_lng = [t['from'][1] for t in trips]
    lines_end_lat = [t['to'][0] for t in trips]
    lines_end_lng = [t['to'][1] for t in trips]

    return plot_geolines(ax, city_data, lines_start_lat, lines_start_lng, lines_end_lat, lines_end_lng, colour)


def filter_positions_to_bounds(city_data, positions):
    """
    Filters the list of positions to only include those that in graphing bounds for the given city
    """

    return [p for p in positions if is_latlng_in_bounds(city_data, p['coords'])]


def create_points_default_colour(positions):
    """
    Assigns a default colour to all positions in the list
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    return {
        SPEEDS[-1][1]: [position['coords'] for position in positions]
    }


def create_points_electric_colour(positions, electric_colour='r', standard_colour='b'):
    """
    Electric engines get electric_colour, other engines get standard_colour
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    # Position electric_colour on top of standard_colour. There is likely to be
    # many more standard cars than electric cars - putting the electric on top
    # makes them more visible.
    return OrderedDict([
        (standard_colour, [position['coords'] for position in positions if not position['electric']]),
        (electric_colour, [position['coords'] for position in positions if position['electric']])
    ])


def create_points_speed_colour(positions):
    """
    Extracts a list of all positions ordered by colour according to vehicle speed
    from a list of objects with metadata.
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    collected = defaultdict(list)

    for position in positions:
        # find the right speed basket
        try:
            speed_bin = next(speed[1] for speed in SPEEDS
                             if position['metadata']['speed'] < speed[0])
        except (KeyError, StopIteration):
            # KeyError when the position doesn't have 'speed' defined
            # StopIteration when no speed matches the condition
            # default to the last colour
            speed_bin = SPEEDS[-1][1]

        # append the position
        collected[speed_bin].append(position['coords'])

    return collected


def create_points_trip_start_end(trips, from_colour='b', to_colour='r'):
    """
    Extracts a list of all start and end positions for provided trips.
    :returns a dict of lists formatted suitably for passing to plot_geopoints()
    """

    # Using OrderedDict to always return the end of the trip last
    # to ensure "to" points appear on top in the graph.
    # In plot_geopoints, points are plotted in the order of the
    # colour-key dictionary, and depending on the colours being used,
    # either "from" or "to" points could end up on top.
    # (E.g. on my implementation, "g" points would be drawn after "b",
    # which would be drawn after "r" -
    # this would vary depending on hash function in use.)
    # With OrderedDict, I specify the order.
    return OrderedDict([
        (from_colour, [trip['from'] for trip in trips]),
        (to_colour, [trip['to'] for trip in trips])
    ])


def graph_wrapper(city_data, plot_function, image_name, background=None):
    """
    Handles creating the figure, saving it as image, and closing the figure.
    :param plot_function: function accepting f, ax params to actually draw on the figure
    :param image_name: image will be saved with this name
    :param background: background for the figure (accessibility snapshot, etc)
    :return: none
    """

    # set up axes
    f, ax = make_graph_axes(city_data, background)

    # pass axes back to function to actually do the plotting
    plot_function(f, ax)

    # render graph to file
    # TODO: could see if saving to a file type other than a png is faster
    # (it seems to have been when I was trying it a long time ago,
    # ps being ~4 times faster, svg and pdf being ~2 times faster),
    # but make sure to include time to render the file to a format
    # that avconv can use as input.
    f.savefig(image_name, bbox_inches='tight', pad_inches=0, dpi=80, transparent=True)

    # close the plot to free the memory. memory is never freed otherwise until
    # script is killed or exits.
    plt.close(f)


def make_graph(result_dict, positions, trips, image_filename, printed_time,
               show_speeds, highlight_distance, symbol):
    """ Creates and saves matplotlib figure for provided positions and trips. """

    city_data = get_city_by_result_dict(result_dict)

    # filter to only vehicles that are in city's graphing bounds
    filtered_positions = filter_positions_to_bounds(city_data, positions)

    if highlight_distance:
        positions_without_metadata = [p['coords'] for p in filtered_positions]
        graph_background = make_accessibility_background(city_data, positions_without_metadata, highlight_distance)
    else:
        graph_background = None

    # mark with either speed, or default colour
    if show_speeds:
        positions_by_colour = create_points_speed_colour(filtered_positions)
    else:
        positions_by_colour = create_points_default_colour(filtered_positions)

    # define what to add to the graph
    def plotter(f, ax):
        # plot points for vehicles
        ax = plot_geopoints(ax, city_data, positions_by_colour, symbol)

        # add in lines for moving vehicles
        if len(trips) > 0:
            ax = plot_trips(ax, city_data, trips)

        # add labels
        coords = city_data['LABELS']['lines']
        fontsizes = city_data['LABELS']['fontsizes']

        ax.text(coords[0][0], coords[0][1],
                city_data['display'], fontsize=fontsizes[0])
        # prints something like "December 10, 2014"
        ax.text(coords[1][0], coords[1][1],
                '{d:%B} {d.day}, {d.year}'.format(d=printed_time),
                fontsize=fontsizes[1])
        # prints something like "Wednesday, 04:02"
        ax.text(coords[2][0], coords[2][1],
                '{d:%A}, {d:%H}:{d:%M}'.format(d=printed_time),
                fontsize=fontsizes[2])
        ax.text(coords[3][0], coords[3][1],
                'available cars: %d' % len(filtered_positions),
                fontsize=fontsizes[3])

    # create and save plot
    graph_wrapper(city_data, plotter, image_filename, graph_background)


def make_positions_graph(result_dict, image_name, symbol, colour_electric=False):
    city_data = get_city_by_result_dict(result_dict)

    # positions are "unfinished parkings" (cars still parked at the end of the dataset)
    # plus all of the "finished parkings" (cars that were parked at one point but moved)
    positions = [p for p in result_dict['unfinished_parkings'].values()]
    positions.extend(parking for vin in result_dict['finished_parkings']
                     for parking in result_dict['finished_parkings'][vin])

    filtered = filter_positions_to_bounds(city_data, positions)

    if colour_electric:
        coloured = create_points_electric_colour(filtered)
    else:
        coloured = create_points_default_colour(filtered)

    def plotter(f, ax):
        plot_geopoints(ax, city_data, coloured, symbol)

    graph_wrapper(city_data, plotter, image_name, background=None)


def _get_trips(result_dict):
    return [trip
            for vin in result_dict['finished_trips']
            for trip in result_dict['finished_trips'][vin]]


def make_trips_graph(result_dict, image_name):
    city_data = get_city_by_result_dict(result_dict)

    trips = _get_trips(result_dict)

    def plotter(f, ax):
        if len(trips) > 0:
            plot_trips(ax, city_data, trips)

    graph_wrapper(city_data, plotter, image_name, background=None)


def make_trip_origin_destination_graph(result_dict, image_name, symbol):
    city_data = get_city_by_result_dict(result_dict)

    trips = _get_trips(result_dict)

    # TODO: use hexbin instead of just drawing points, to avoid problem/unexpected results
    # caused when a trip ends in a given point then the vehicle is picked up again
    # and a second trip starts in the same point (described in a comment in
    # create_points_trip_start_end()).
    # Maybe try to assign value of +1 to trips starting at a point,
    # -1 to trips ending, then do hexbin on sum or mean of the values
    # to find spots where vehicles mostly arrive, mostly depart, or are balanced

    def plotter(f, ax):
        trip_points = create_points_trip_start_end(trips)
        plot_geopoints(ax, city_data, trip_points, symbol)

    graph_wrapper(city_data, plotter, image_name, background=None)


def make_accessibility_background(city_data, positions, distance):
    latitudes, longitudes = zip(*positions)
    latitudes = np.round(map_latitude(city_data, np.array(latitudes)))
    longitudes = np.round(map_longitude(city_data, np.array(longitudes)))

    # The below is based off http://stackoverflow.com/questions/8647024/how-to-apply-a-disc-shaped-mask-to-a-numpy-array
    # Basically, we build a True/False mask (master_mask) the same size 
    # as the map. Each 'pixel' within the mask indicates whether the point 
    # is within provided distance from a car.
    # To build this, iterate over all cars and apply a circular mask of Trues
    # (circle_mask) around the point indicating each car. We'll need to shift 
    # things around near the borders of the map, but this is relatively
    # straightforward.

    accessible_colour = (255, 255, 255, 0)  # white, fully transparent
    inaccessible_colour = (239, 239, 239, 100)  # #efefef, mostly transparent

    # not using accessible_multiplier currently because it's too slow
    # accessible_multiplier = (1, 1, 1, 0.6)
    # if using accessible_multiplier, 160 alpha for inaccessible looks better

    # generate basic background, for now uniformly indicating no cars available
    markers = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X'], 4),
        dtype=np.uint8)
    markers[:] = inaccessible_colour  # can't use fill since it isn't a scalar

    # find distance radius, in pixels
    pixel_in_m = get_mean_pixel_size(city_data)
    radius = np.round(distance / pixel_in_m)

    # generate master availability mask
    master_mask = np.empty(
        (city_data['MAP_SIZES']['MAP_Y'], city_data['MAP_SIZES']['MAP_X']),
        dtype=np.bool)
    master_mask.fill(False)
    m_m_shape = master_mask.shape

    # generate basic circle mask
    y, x = np.ogrid[-radius: radius+1, -radius: radius+1]
    circle_mask = x**2+y**2 <= radius**2
    c_m_shape = circle_mask.shape

    for i in range(len(latitudes)):
        # to just crudely mark a square area around lat/lng:
        # markers[ (lat - radius) : (lat+radius), (lng-radius) : (lng+radius)] = accessible_colour

        # mask is drawn from top-left corner. to center mask around the point:
        x = latitudes[i] - radius
        y = longitudes[i] - radius

        # find various relevant locations within the matrix...

        # cannot give a negative number as first param in slice
        master_x_start = max(x, 0)
        master_y_start = max(y, 0)
        # but going over boundaries is ok, will trim automatically
        master_x_end = x + c_m_shape[0]
        master_y_end = y + c_m_shape[1]

        circle_x_start = 0
        circle_y_start = 0
        circle_x_end = c_m_shape[0]
        circle_y_end = c_m_shape[1]

        if x < 0:   # trim off left side
            circle_x_start = x * -1
        if y < 0:   # trim off top
            circle_y_start = y * -1
        if master_x_end > m_m_shape[0]:  # trim off right side
            circle_x_end = (m_m_shape[0] - master_x_end)
        if master_y_end > m_m_shape[1]:  # trim off bottom
            circle_y_end = (m_m_shape[1] - master_y_end)

        # make sure to OR the masks so that earlier circles' Trues 
        # aren't overwritten by later circles' Falses
        master_mask[
            master_x_start: master_x_end,
            master_y_start: master_y_end
            ] |= circle_mask[
                circle_x_start: circle_x_end,
                circle_y_start: circle_y_end]

        # not using accessible_multiplier currently because it's too slow
        # markers[master_mask] *= accessible_multiplier

    # note: can also do something like this: markers[mask] *= (1, 1, 1, 0.5)
    # and it updates everything - should be useful for relative values.
    # except it has to happen within the iteration as shown above, and is also
    # pretty slow. like, adds 1.2 seconds per image slow. see if I can 
    # optimize it somehow, but multiplying a million-item array, even masked,
    # by a vector 200 times might just be inherently a bit slow :(

    markers[master_mask] = accessible_colour

    return markers
